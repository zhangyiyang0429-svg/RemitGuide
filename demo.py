"""RemitGuide · 南向汇款教学模拟。启动：streamlit run demo.py"""
import hashlib
import json
import os
import re
import sqlite3
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from remit_language import tr

D = Decimal
BANKS = ("海湾银行", "明港银行", "远洋银行")
HOURS = ("23:00",) + tuple(f"{h:02}:00" for h in range(8))
# 教学用官方参考值；模拟银行在同一时点加上各自的报价差额。
REFERENCE = tuple(map(D, ("92.10", "92.72", "92.56", "92.42", "92.17",
                          "92.67", "92.78", "92.29", "92.90")))
NORMAL = "正常"
# 演示备注：全部资料均为虚构。按所选收款路径核对登记号码、户名和银行；
# 付款人地址与模拟客户档案比对。回执取自匹配账户的模拟银行脚本。
RECIPIENTS = (
    dict(name="ZHANGSAN", style="pinyin", document="中国大陆居民身份证", sample_id="110101199001010015",
         bank="中大银行", account="1000000001", phone="90000001"),
    dict(name="CHENDAIWEN", style="pinyin", document="香港居民身份证", sample_id="A123456(3)",
         bank="香港银行", account="2000000002", phone="90000002"),
    dict(name="Kevin James", style="english", document="护照", sample_id="P00000001",
         bank="香港银行", account="2000000003", phone="90000003"),
)
RECEIVING_FEES = {"中大银行": D("0"), "香港银行": D("5")}
PROFILES = dict(zip(("张三", "陈大文", "Kevin James"), RECIPIENTS))
PAYER_ADDRESSES = {
    "张三": "Flat B2, 8F, Cedar Court, No.18 Maple Lane, Mong Kok, Kowloon, Hong Kong",
    "陈大文": "Flat A1, 6F, Chinese Hill, No.77 Dai Hok Lane, Sha Tin, New Territories, Hong Kong",
    "Kevin James": "Flat C3, 12F, Willow House, No.32 Laurel Road, Wan Chai, Hong Kong Island, Hong Kong",
}
# 付款账户与收款人独立；比价和更换收款人不会改变资金来源。
ACCOUNTS = {
    "张三": (D("18000"), D("12000"), D("24000")),
    "陈大文": (D("32000"), D("15000"), D("20000")),
    "Kevin James": (D("45000"), D("25000"), D("35000")),
}
# 教学地址模板：先检查英文和标点，再核对固定地区段。
WORDS = r"[A-Za-z]+(?: [A-Za-z]+)*"
ADDRESS_PATTERN = re.compile(
    rf"Flat [A-Za-z0-9]+, [0-9]+F, {WORDS}, No\.[0-9]+ {WORDS}, {WORDS}, {WORDS}, {WORDS}"
)


def address_error(value):
    if not ADDRESS_PATTERN.fullmatch(value):
        return "请检查地址格式：使用英文、半角逗号和一个空格，门牌写作 No.77。"
    district = value.rsplit(", ", 3)[1:]
    if not any(district == addr.rsplit(", ", 3)[1:] for addr in PAYER_ADDRESSES.values()):
        return "无效地址：请核对地区、区域与 Hong Kong 的组合。"
    return None

DB = Path(os.getenv("REMITGUIDE_DB", str(Path.home() / ".remitguide" / "demo.sqlite3")))


def money(value):
    return D(str(value)).quantize(D(".01"), rounding=ROUND_HALF_UP)


def quote(bank, hour, budget, currency, receiving_bank=""): 
    bank = {"海湾银行 A": BANKS[0], "明港银行 B": BANKS[1], "远洋银行 C": BANKS[2]}.get(bank, bank)
    i = BANKS.index(bank)
    amount = money(budget)
    fee = (D("10"), money(max(D("2"), amount * D(".0015"))), D("18"))[i]
    receiving_fee = RECEIVING_FEES[receiving_bank] if receiving_bank else D("0")
    fee += receiving_fee
    cost = REFERENCE[hour] + (D(".20"), D(".08"), D(".40"))[i]
    rate = D("100") / cost if currency == "HKD" else D("1")
    principal = max(D("0"), amount - fee)
    net = money(principal * 100 / cost) if currency == "HKD" else money(principal)
    key = f"{bank}|{hour}|{amount}|{currency}|{rate}|{fee}"
    return dict(receiving_bank=receiving_bank, receiving_fee=str(money(receiving_fee)), bank=bank, hour=hour, total=str(amount), fee=str(money(fee)),
                cost_per_100=str(cost) if currency == "HKD" else None, rate=str(rate), net=str(net), currency=currency,
                ref=hashlib.sha256(key.encode()).hexdigest()[:10].upper())


def rate_label(q):
    if q["currency"] == "CNY":
        return "1 CNY / CNY"
    cost = D(q["cost_per_100"]) if q.get("cost_per_100") else D("100") / D(q["rate"])
    return f"{cost:.2f} CNY / 100 HKD"


def quote_changed(viewed, current):
    return viewed["ref"] != current["ref"]


def check(data, q, issue):
    if not data["name"].strip():
        return "待修正", "请填写收款人姓名。"
    mobile = data["method"] == "香港手机号"
    pattern = r"[0-9]{8}" if mobile else r"[0-9]{8,16}"
    if not re.fullmatch(pattern, data["number"]):
        return "待修正", "本模拟路线要求半角数字，手机号为 8 位，账号为 8 至 16 位。"
    if D(q["total"]) <= D(q["fee"]):
        return "待修正", "付款总额须大于手续费。"
    if issue == "超过累计额度":
        return "受限", "已超出演示账户的可用汇款额度。"
    if issue == "手机号未登记" and mobile:
        return "待修正", "此号码未取得可用收款登记。请核对或改用银行账户。"
    if issue == "收款币种不支持" and q["currency"] == "HKD":
        return "受限", "该收款账户仅支持人民币。请更换币种。"
    results = {
        "证件过期": ("待补资料", "请通过付款银行更新本人身份证件。"),
        "地址待核验": ("银行复核中", "请通过付款银行核对本人留档资料。"),
        "收款资料无法核实": ("待修正", "收款资料未能核实，请与收款人确认。"),
        "账户受限": ("受限", "该账户暂无法办理，请联系付款银行。"),
        "授权失效": ("待授权", "请通过付款银行重新授权。"),
        "用途资料待补充": ("待补资料", "请向付款银行补充用途资料。"),
        "银行风险复核": ("银行复核中", "银行正在复核，请等待通知。"),
        "登记查询超时": ("待核实", "暂时无法取得核验结果，请稍后重新查询。"),
    }
    return results.get(issue, ("已通过", "自动预检已通过。"))


def verify_recipient(data, q):
    decision = check(data, q, NORMAL)
    if decision[0] != "已通过":
        return decision, None
    mobile = data["method"] == "香港手机号"
    key = "phone" if mobile else "account"
    recipient = next((r for r in RECIPIENTS if r[key] == data["number"]), None)
    if mobile and recipient is None:
        return check(data, q, "手机号未登记"), None
    if not mobile and recipient and recipient["name"] == "CHENDAIWEN" and data["bank"] == "中大银行":
        return ("待修正", "未能查到收款账户"), None
    if recipient is None:
        return check(data, q, "收款资料无法核实"), None
    if recipient != PROFILES[data["holder"]]:
        return ("待修正", "收款账户与付款人登记身份不一致，请使用本人的收款资料。"), None
    name = data["name"]
    if recipient["style"] == "pinyin":
        if not re.fullmatch("[A-Z]+", name):
            return ("待修正", "请使用英文拼音：需要全部大写并无空格。"), None
        matches = name == recipient["name"]
    else:
        matches = " ".join(name.split()).casefold() == recipient["name"].casefold()
    if not matches:
        hint = "需要全部大写并无空格。" if recipient["style"] == "pinyin" else "请核对英文姓名拼写。"
        return ("待修正", "收款人英文姓名与登记资料不匹配。" + hint), None
    if data["document"] != recipient["document"]:
        return ("待修正", "证件类型与该收款人的演示档案不匹配。"), None
    patterns = {"中国大陆居民身份证": r"[0-9]{17}[0-9X]", "香港居民身份证": r"[A-Z]{1,2}[0-9]{6}\([0-9A]\)", "护照": r"[A-Z][A-Z0-9]{8}"}
    number = data["sample_id"].strip().upper()
    if not re.fullmatch(patterns[data["document"]], number):
        return ("待修正", "请检查证件号码格式，参照使用手册中的虚构示例。"), None
    if number != recipient["sample_id"]:
        return ("待修正", "证件号码与收款人的演示档案不匹配。"), None
    error = address_error(data["address"])
    if error:
        return ("待修正", error), None
    if data["address"] != PAYER_ADDRESSES[data["holder"]]:
        return check(data, q, "地址待核验"), None
    return decision, recipient


def event(order, time, state, message):
    order["state"] = state
    order["events"].append([time, state, message])


def reserve(q, decision, outcome, enhanced=True):
    order = dict(id=uuid.uuid4().hex[:12].upper(), quote=q.copy(), outcome=outcome,
                 decision=decision, enhanced=enhanced, events=[], sent=0, debit="0.00",
                 refund="0.00", used_rate=None, open_success=False, step=0)
    state, msg = decision
    if enhanced:
        event(order, HOURS[q["hour"]], "已预约" if state == "已通过" else state, msg)
    else:
        event(order, "07:00", "直接提交", "对照组在开窗时提交。")
    return order


def remittance_precheck(data, quote_record):
    decision, _ = verify_recipient(data, quote_record)
    return {"quote_id": quote_record["ref"], "status": decision[0], "guidance": decision[1]}


def confirm_preorder(owner, payer, quote_record, check_result, parent=None):
    if check_result["quote_id"] != quote_record["ref"]:
        raise ValueError("Pre-check and quote references differ")
    decision = (check_result["status"], check_result["guidance"])
    if decision[0] in ("受限", "待修正"):
        return {"order_id": None, "error": decision[1]}
    order = reserve(quote_record, decision, "延迟回执")
    order.update(payer=payer, parent=parent)
    if quote_record["hour"] == 8:
        advance(order, 1)
    error = save(owner, order)
    return {"order_id": None if error else order["id"], "error": error}


def refund_settlement(order):
    if order["state"] != "退款在途":
        raise ValueError("Refund requires a pending bank return")
    fee = D(order["quote"]["fee"])
    return {"order_id": order["id"], "currency": "CNY",
            "amount": str(money(D(order["debit"]) - fee)), "retained_fee": str(fee)}


def advance(o, step):
    """幂等的银行时钟。1=07:00，2=07:05，3=11:00。"""
    q = o["quote"]
    if step >= 1 and o["step"] < 1 and o["state"] in ("已预约", "直接提交"):
        if o["outcome"] == "余额变动":
            event(o, "07:00", "未提交", "执行前余额不足，未扣款。")
        else:
            o["sent"] = 1
            event(o, "07:00", "已提交", "已发送至模拟银行。")
            if o["decision"][0] != "已通过" or o["outcome"] == "银行拒绝":
                event(o, "07:00", "已拒绝", "银行拒绝本次交易，未扣款。")
            else:
                o["debit"] = q["total"]
                o["used_rate"] = q["rate"]
                if o["outcome"] == "即时到账":
                    o["open_success"] = True
                    event(o, "07:00", "已到账", "收款行已确认入账。")
                else:
                    event(o, "07:00", "确认中", "付款行已扣款，尚待收款行回执。")
    if step >= 2 and o["step"] < 2 and o["state"] == "确认中":
        if o["outcome"] == "延迟回执":
            event(o, "07:05", "已到账", "原交易收到收款行入账回执。")
        else:
            event(o, "07:05", "退款在途", o.get("return_reason", "收款行退回，等待退款入账。"))
    if step >= 3 and o["step"] < 3 and o["state"] == "退款在途":
        o["refund"] = refund_settlement(o)["amount"]
        event(o, "11:00", "已退汇", "退款已入付款账户，原手续费不退。")
    o["step"] = max(o["step"], step)
    return o


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("CREATE TABLE IF NOT EXISTS orders(owner TEXT, id TEXT, body TEXT, PRIMARY KEY(owner,id))")
    return conn


def capacity(holder, records):
    balance, single, daily = ACCOUNTS[holder]
    used = D("0")
    for o in records:
        if o.get("payer", "张三") != holder:
            continue
        held = D(o["quote"]["total"]) if o["state"] == "已预约" else D("0")
        spent = held + D(o["debit"])
        balance += D(o["refund"]) - spent
        used += spent
    return max(D("0"), balance), single, max(D("0"), daily - used)


def limits_message(amount, available):
    labels = ("可用余额不足", "超过单笔转账额度", "超过当日剩余转账额度")
    return "；".join(f"{label}（可用 {money(limit)} CNY）"
                    for label, limit in zip(labels, available) if amount > limit)


@st.dialog(tr("收款账户核验"))
def missing_account_dialog():
    st.error(tr("未能查到收款账户"))
    st.write(tr("陈大文在中大银行没有登记账户，请选择香港银行。"))
    if st.button(tr("返回选择收款行")):
        st.rerun()


@st.dialog(tr("付款账户核验未通过"))
def limit_dialog(message):
    st.error(tr(message))
    st.write(tr("请降低付款金额，或返回表单选择其他付款账户。"))
    if st.button(tr("返回修改")):
        st.rerun()


def save(owner, order):
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        if order.get("payer") and order["decision"][0] == "已通过":
            records = (json.loads(row[0]) for row in con.execute("SELECT body FROM orders WHERE owner=?", (owner,)))
            error = limits_message(D(order["quote"]["total"]), capacity(order["payer"], records))
            if error:
                return error
        con.execute("INSERT OR IGNORE INTO orders VALUES(?,?,?)",
                    (owner, order["id"], json.dumps(order, ensure_ascii=False)))


def orders(owner, step=None, only=None):
    with connect() as con:
        if step is not None:
            con.execute("BEGIN IMMEDIATE")
        rows = con.execute("SELECT body FROM orders WHERE owner=? ORDER BY rowid DESC", (owner,))
        result = [json.loads(row[0]) for row in rows]
        for order in result:
            if step is not None and (only is None or only == order["id"]):
                # 旧版尚未执行的预约也使用统一时间线；已产生的银行流水保留。
                if order["state"] == "已预约" and order["step"] == 0:
                    order["outcome"] = "延迟回执"
                    order.pop("return_reason", None)
                advance(order, step)
                con.execute("UPDATE orders SET body=? WHERE owner=? AND id=?",
                            (json.dumps(order, ensure_ascii=False), owner, order["id"]))
        return result


def suspend_credit(owner, ident):
    """在银行回执到达前，将暂停入账通知关联到这一笔已提交订单。"""
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT body FROM orders WHERE owner=? AND id=?", (owner, ident)).fetchone()
        if row:
            order = json.loads(row[0])
            if order["state"] == "确认中" and order["step"] == 1:
                order["outcome"] = "退汇·仅手续费"
                order["return_reason"] = "收款行通知：提交后账户暂停入账，原路退回。"
                con.execute("UPDATE orders SET body=? WHERE owner=? AND id=?",
                            (json.dumps(order, ensure_ascii=False), owner, ident))


def inputs():
    return dict(name="演示客户", method="银行账户", number="1234567890")


def experiments():
    # 各组相同初始输入、额度及回执脚本。修正行为显式记录。
    cases = [
        ("成功支付", "正常预约", NORMAL, "即时到账", False, "已到账", "已到账"),
        ("服务限制", "币种不支持", "收款币种不支持", "即时到账", False, "已拒绝", "受限"),
        ("收款资料", "全角数字，提示后修正", NORMAL, "即时到账", True, "已拒绝", "已到账"),
        ("收款资料", "手机号无登记", "手机号未登记", "即时到账", False, "已拒绝", "待修正"),
        ("报价更新", "01:59 浏览，02:00 重新确认", NORMAL, "即时到账", False, "已到账", "已到账"),
        ("银行拒绝", "执行返回拒绝", NORMAL, "银行拒绝", False, "已拒绝", "已拒绝"),
        ("待确认", "07:05 获得回执", NORMAL, "延迟回执", False, "已到账", "已到账"),
        ("退汇", "仅损失原手续费", NORMAL, "退汇·仅手续费", False, "已退汇", "已退汇"),
        ("隐私异常", "银行留档资料需核验", "地址待核验", "即时到账", False, "已拒绝", "银行复核中"),
    ]
    results = []
    for category, title, issue, outcome, fix, control, improved in cases:
        for enhanced in (False, True):
            data = inputs()
            if fix:
                data["number"] = "１２３４５６７８９０"
            if issue == "手机号未登记":
                data.update(method="香港手机号", number="91234567")
            hour = (3 if category == "报价更新" else 0) if enhanced else 8
            q = quote(BANKS[0], hour, 5000, "HKD")
            initial = check(data, q, issue)
            corrected = enhanced and fix and initial[0] == "待修正"
            if corrected:
                data["number"] = "1234567890"
            o = reserve(q, check(data, q, issue), outcome, enhanced)
            if corrected:
                o["events"].insert(0, [HOURS[hour], "已修正", "客户按提示将全角账号改为半角。"])
            if category == "报价更新" and enhanced:
                o["events"].insert(0, ["02:00", "重新确认", "01:59 浏览的报价已到期，客户接受 02:00 新报价。"])
            for step in (1, 1, 2, 3):
                advance(o, step)
            expected = improved if enhanced else control
            checks = [o["state"] == expected, o["sent"] == int(not enhanced or expected in ("已到账","已退汇","已拒绝"))]
            if category == "退汇":
                expected_refund = D(q["total"]) - D(q["fee"])
                checks.append(D(o["refund"]) == expected_refund)
            if category == "报价更新" and enhanced:
                old = quote(BANKS[0], 2, 5000, "HKD")
                checks.extend([quote_changed(old, q), o["used_rate"] == q["rate"], q["net"] == str(money(D("499000") / D("92.62")))])
            checks.append(data["number"] not in json.dumps(o, ensure_ascii=False))
            results.append(dict(类型=category, 案例=title, 组别="增强组" if enhanced else "对照组",
                                订单=o["id"], 预检=initial[0] if enhanced else "未启用",
                                已纠错=corrected, 开窗成功=o["open_success"], 最终到账=o["state"]=="已到账",
                                提交次数=o["sent"], 预期=expected, 实际=o["state"], 通过=all(checks),
                                报价=q["ref"], 汇率=q["rate"], 退款=o["refund"], 事件=o["events"]))
    return results


@st.dialog(tr("锁价比较"))
def fx_dialog(o):
    q = o["quote"]
    opening = quote(q["bank"], 8, q["total"], q["currency"], q.get("receiving_bank", ""))
    delta = money(D(q["net"]) - D(opening["net"]))
    st.metric(tr("锁价相对开窗的到账差额") + " · " + q["currency"], f"{abs(delta):,.2f}")


def show_receipt(o):
    q = o["quote"]
    st.subheader(tr(o["state"]))
    st.caption(tr(f"交易参考编号 {o['id']} · {q['bank']} · 报价 {q['ref']}"))
    st.caption(tr("付款账户：" + o.get("payer", "张三")))
    if q.get("receiving_bank"):
        st.caption(tr(f"收款行：{q['receiving_bank']} · 收款手续费 {q['receiving_fee']} CNY（已计入总手续费）"))
    if o.get("parent"):
        st.caption(tr("关联原交易 " + o["parent"]))
    cols = st.columns(3)
    cols[0].metric(tr("确认扣款 · CNY"), o["debit"])
    cols[1].metric(tr("确认退回 · CNY"), o["refund"])
    credited = q["net"] if o["state"] == "已到账" else "0.00" if o["state"] in ("已退汇", "退款在途", "已拒绝", "未提交") else "待确认"
    cols[2].metric(tr(f"收款人实际到账 · {q['currency']}"), tr(credited))
    st.write(tr(f"预约报价 {rate_label(q)}　｜　实际执行汇率 {rate_label(q) if o['used_rate'] else '待执行'}　｜　提交次数 {o['sent']}"))
    if o["state"] == "已退汇":
        if D(o["refund"]) == D(o["debit"]) - D(q["fee"]):
            st.info(tr(f"原扣款 {o['debit']} − 原手续费 {q['fee']} = 实退 {o['refund']} CNY。"))
        else:
            st.caption(tr("历史回执 · 按原交易规则结算"))
    if o["state"] == "已到账":
        if st.button(tr("查看锁价比较"), key="fx_" + o["id"]):
            st.session_state.fx_opened = True
            fx_dialog(o)
    if o["sent"]:
        at_open = quote(q["bank"], 8, q["total"], q["currency"])
        st.caption(tr(f"07:00 市场参考汇率 {rate_label(at_open)} · 订单确认汇率 {rate_label(q)}"))
    for stamp, state, msg in o["events"]:
        st.write(tr(f"**{stamp}　{state}**　{msg}"))


def payment(owner, clock):
    st.header(tr("向香港汇款"))
    st.markdown(tr('<div class="route"><strong>中国内地</strong><span> ────── → </span><strong>中国香港</strong><small>跨境支付通 · 本人账户汇款 · 教学模拟</small></div>'), unsafe_allow_html=True)
    hour = clock
    left, right = st.columns(2)
    with left.container(border=True):
        st.subheader(tr("付款账户资料"))
        holder = st.selectbox(tr("付款账户"), list(ACCOUNTS), format_func=tr, key="ui_397")
        profile = PROFILES[holder]
        available = capacity(holder, orders(owner))
        st.metric(tr("可用余额 · CNY"), f"{available[0]:,.2f}")
        single, daily = st.columns(2)
        single.metric(tr("单笔额度") + " · CNY", f"{available[1]:,.2f}")
        daily.metric(tr("今日剩余额度") + " · CNY", f"{available[2]:,.2f}")
        address = st.text_input(tr("付款人登记地址（模拟）"), PAYER_ADDRESSES[holder], key="payer_address_" + holder)
        error = address_error(address)
        if error:
            st.error(tr(error))
        st.button("RemitGuide Account Profile Open API", disabled=True)
    with right.container(border=True):
        st.subheader(tr("收款人资料"))
        st.button("RemitGuide Remittance Open API", disabled=True)
        method = st.radio(tr("收款方式"), ("银行账户", "香港手机号"), horizontal=True, format_func=tr, key="ui_411")
        recipient_bank = st.selectbox(tr("香港收款银行"), list(RECEIVING_FEES),
            index=list(RECEIVING_FEES).index(profile["bank"]), key="recv_bank_"+holder, format_func=lambda b: tr(f"{b} · 收款手续费 {money(RECEIVING_FEES[b])} CNY")) if method == "银行账户" else ""
        name = st.text_input(tr("收款人英文登记姓名"), profile["name"], key="name_"+holder)
        document = st.selectbox(tr("收款人证件类型"), [r["document"] for r in RECIPIENTS], index=RECIPIENTS.index(profile), key="doc_"+holder, format_func=tr)
        sample_id = st.text_input(tr("收款人证件号码（仅输入手册中的虚构号码）"), profile["sample_id"], key="id_"+holder)
        number = st.text_input(tr("收款账号" if recipient_bank else "香港手机号（+852）"),
                               profile["account"] if recipient_bank else profile["phone"], key="number_"+holder+method)
        unavailable = recipient_bank == "中大银行" and (holder == "陈大文" or number == RECIPIENTS[1]["account"] or name.strip() == "CHENDAIWEN")
        if unavailable:
            st.error(tr("未能查到收款账户"))
            if not st.session_state.get("missing_account"):
                st.session_state.missing_account = True
                missing_account_dialog()
        else:
            st.session_state.missing_account = False
    with left.container(border=True):
        st.subheader(tr("汇款金额"))
        budget = st.number_input(tr("付款总额 · CNY（含手续费）"), 0.01, 1000000.0, 5000.0, step=100.0, key="ui_429")
        currency = st.selectbox(tr("收款币种"), ("HKD", "CNY"), format_func=tr, key="ui_430")
    with st.container(border=True):
        bank = st.selectbox(tr("报价银行"), BANKS, format_func=tr, key="quote_provider")
        st.button("RemitGuide FX Quotes Open API", disabled=True)
        st.table([{tr("付款银行"): tr(provider), tr("手续费 CNY"): offer["fee"],
                   tr("汇率"): rate_label(offer)}
                  for provider in BANKS for offer in [quote(provider, hour, budget, currency, recipient_bank)]])
        preview = quote(bank, hour, budget, currency, recipient_bank)
        st.metric(tr(f"预计实收 · {currency}"), f"{D(preview['net']):,.2f}")
    data = dict(holder=holder, name=name, method=method, number=number, bank=recipient_bank, address=address, document=document, sample_id=sample_id)
    fingerprint = (holder, bank, method, recipient_bank, name, number, budget, currency, address, document, sample_id)
    if st.button(tr("下一步 · 核对汇款"), type="primary", disabled=bool(error) or unavailable):
        problem = limits_message(money(budget), available)
        if problem:
            st.session_state.review = None
            limit_dialog(problem)
            return
        st.session_state.review = fingerprint
        st.session_state.quote_hour = hour
        st.session_state.pop("bank_choice", None)
    if st.session_state.get("review") != fingerprint:
        return
    st.divider()
    st.subheader(tr("核对汇款"))
    st.button("RemitGuide Confirmation Open API", disabled=True)
    choice = bank
    q = quote(choice, hour, budget, currency, recipient_bank)
    st.write(tr(f"**{choice}**　·　{method}尾号 {number[-4:]}"))
    cols = st.columns(3)
    cols[0].metric(tr("总扣款 · CNY"), q["total"])
    cols[1].metric(tr("手续费 · CNY"), q["fee"])
    cols[2].metric(tr(f"预计实收 · {currency}"), q["net"])
    st.caption(tr(f"付款行手续费 {money(D(q['fee'])-D(q['receiving_fee']))} CNY · 收款行手续费 {q['receiving_fee']} CNY"))
    st.caption(tr(f"兑换本金 {money(D(q['total'])-D(q['fee']))} CNY · 汇率 {rate_label(q)}。"
               f"报价 {q['ref']}，本小时有效；确认后保价至本次开窗。"))
    old = quote(choice, st.session_state.quote_hour, budget, currency, recipient_bank)
    if quote_changed(old, q):
        st.warning(tr(f"原报价已过期。原预计实收 {old['net']}，新预计实收 {q['net']} {currency}。"))
        if st.button(tr("接受本小时新报价")):
            st.session_state.quote_hour = hour
            st.rerun()
        return
    check_result = remittance_precheck(data, q)
    decision = (check_result["status"], check_result["guidance"])
    if decision[0] != "已通过":
        st.warning(tr(decision[1]))
    else:
        st.success(tr("自动预检已通过。"))
    if decision[0] in ("待修正", "受限"):
        return
    label = "保存待处理申请" if decision[0] != "已通过" else ("确认汇款" if hour == 8 else "确认预约并锁定报价")
    if st.button(tr(label), type="primary"):
        result = confirm_preorder(owner, holder, q, check_result, st.session_state.get("retry_parent"))
        if result["error"]:
            limit_dialog(result["error"])
            return
        st.session_state.pop("retry_parent", None)
        st.session_state.review = None
        st.session_state.page = "汇款记录"
        st.rerun()


def history(owner):
    st.header(tr("汇款记录"))
    rows = orders(owner)
    if not rows:
        st.info(tr("尚无预约。请先填写汇款。"))
        return
    by_id = {o["id"]:o for o in rows}
    ident = st.selectbox(tr("选择订单"), list(by_id), format_func=lambda k: tr(k+" · "+by_id[k]["state"]), key="ui_498")
    o = by_id[ident]
    show_receipt(o)
    if o["state"] == "确认中" and o["step"] == 1:
        with st.expander(tr("模拟收款行通知")):
            if o.get("return_reason"):
                st.info(tr(o["return_reason"]))
            elif st.button(tr("通知此笔交易暂停入账")):
                suspend_credit(owner, ident)
                st.rerun()
    if o["state"] in ("确认中", "退款在途"):
        st.info(tr("模拟银行当前状态：" + o["state"]))
    if o["state"] in ("已拒绝", "未提交", "待授权", "待补资料", "银行复核中", "待核实"):
        st.caption(tr("补充资料或联系银行完成处理后，可重新填写申请。"))
        if st.button(tr("修改后重新预约")):
            st.session_state.retry_parent = ident
            st.session_state.page = "向香港汇款"
            st.session_state.review = None
            st.rerun()


def orders_by_id(owner, ident):
    return next(o for o in orders(owner) if o["id"] == ident)


@st.dialog(tr("确定清空汇款记录？"))
def confirm_clear(owner):
    st.write(tr("将删除当前演示的全部汇款记录。清空后无法恢复。"))
    left, right = st.columns(2)
    if left.button(tr("取消")):
        st.rerun()
    def erase():
        with connect() as con:
            con.execute("DELETE FROM orders WHERE owner=?", (owner,))
        for key in ("review", "retry_parent"):
            st.session_state.pop(key, None)

    if right.button(tr("确定清空"), type="primary", on_click=erase):
        st.rerun()


def main():
    st.set_page_config(page_title="RemitGuide", page_icon="💱", layout="wide")
    st.markdown("""<style>[data-testid="stSidebar"] {background:#edf4f4} h1,h2,h3 {color:#164853} [data-testid="stMainBlockContainer"] {max-width:78rem;padding-top:3rem} [data-testid="stMetricValue"] {color:#126963}.route {background:linear-gradient(110deg,#103b49,#24575b);padding:1.3rem 1.6rem;border-radius:16px;color:white;margin-bottom:.8rem}.route strong{font-size:1.35rem}.route span{color:#97d8ca}.route small{display:block;margin-top:.5rem;color:#d4e8e4}[data-testid="stMetric"]{padding:.7rem 1rem;border-left:4px solid #30938b;background:#eff7f5;border-radius:0 12px 12px 0;color:#173f46}[data-testid="stVerticalBlockBorderWrapper"]{box-shadow:0 4px 18px rgba(22,72,83,.07)} [data-testid="stMainBlockContainer"]{padding-bottom:4rem} .route{border-bottom:4px solid #68baaa;background:radial-gradient(ellipse at 90% 10%,#347672,transparent 50%),#103b49}.route span{letter-spacing:.14em} [data-testid="stMetricValue"]{font-variant-numeric:tabular-nums} [data-testid="stExpander"]{border-radius:14px;overflow:hidden} [data-testid="stMain"]{background:linear-gradient(145deg,#f2f7f6,#fff 65%)} [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-color:#dbe6e3;border-radius:18px} .route{position:relative;isolation:isolate;overflow:hidden;padding:1.55rem 2rem}.route:after{content:"";position:absolute;z-index:-1;right:-3rem;top:-8rem;width:27rem;height:27rem;border-radius:50%;border:1px solid #74b0a8;box-shadow:0 0 0 2rem #ffffff0d,0 0 0 4rem #ffffff09}.route strong{font-size:clamp(1.2rem,2.5vw,1.85rem)} [data-testid="stBaseButton-primary"]{background:#116757;border-color:#116757;border-radius:12px;font-weight:650} [data-testid="stToolbar"], #MainMenu, [data-testid="stMainMenu"] {display:none!important} .route{background:linear-gradient(110deg,#103b49,#24575b);min-height:9rem}.route:after{display:none}[data-testid="stColumn"] [data-testid="stColumn"] [data-testid="stMetricValue"]{font-size:clamp(1rem,2vw,1.65rem)}
    [data-testid="stApp"] {background:linear-gradient(115deg,#edf5f2cf,#edf5f288),url('https://upload.wikimedia.org/wikipedia/commons/2/23/Hong_Kong_Skyline_Restitch_-_Dec_2007.jpg') center/cover fixed;}
    [data-testid="stMain"], [data-testid="stHeader"] {background:transparent}
    [data-testid="stSidebar"] {background:rgba(240,247,246,.91)}
    [data-testid="stMainBlockContainer"] {background:rgba(255,255,255,.76);border-radius:18px}
    </style>""", unsafe_allow_html=True)
    owner = st.query_params.get("demo", "")
    if not re.fullmatch("[a-f0-9]{32}", owner):
        owner = uuid.uuid4().hex
        st.query_params["demo"] = owner
    st.session_state.setdefault("page", "向香港汇款")
    st.sidebar.title("RemitGuide")
    if st.sidebar.button("切换中文" if st.session_state.get("english") else "Switch to English"):
        st.session_state.english = not st.session_state.get("english", False)
        st.rerun()
    st.sidebar.caption(tr("个人银行 · 教学模拟"))
    st.session_state.setdefault("confirmed_time", "23:00")
    with st.sidebar.form("demo_time"):
        entered = st.text_input(tr("香港演示时间（HH:MM）"), "23:00", key="draft_demo_time")
        if st.form_submit_button(tr("确定时间")):
            if re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", entered.strip()):
                st.session_state.confirmed_time = entered.strip()
            else:
                st.error(tr("请输入有效的 24 小时时间，例如 07:03。"))
    stamp = st.session_state.confirmed_time
    h, m = map(int, stamp.split(":"))
    minutes = h * 60 + m
    step = 0 if minutes >= 1380 or minutes < 420 else 1 if minutes < 425 else 2 if minutes < 660 else 3
    st.sidebar.caption(tr(f"已确认 {stamp} · " + ("夜间预约", "开窗提交", "银行回执", "退汇处理")[step]))
    st.session_state.fx_opened = False
    st.session_state.clear_opened = False
    if st.sidebar.button(tr("清空记录")):
        st.session_state.clear_opened = True
        confirm_clear(owner)
    if step == 0:
        for title in ("向香港汇款", "汇款记录"):
            if st.sidebar.button(tr(title)):
                st.session_state.page = title
    with st.sidebar:
        st.markdown(tr("**官方参考汇率（模拟）**"))
        st.caption(tr("每 100 港元所需人民币 · 香港时间"))
        points = pd.DataFrame({"时间": HOURS, "参考汇率": [float(rate) for rate in REFERENCE]})
        chart = alt.Chart(points).mark_line(color="#176BA0", strokeWidth=3, opacity=0.78, point=True).encode(
            x=alt.X("时间:O", sort=list(HOURS), title=None,
                    axis=alt.Axis(values=list(HOURS[::2]), labelAngle=0)),
            y=alt.Y("参考汇率:Q", title=None, scale=alt.Scale(zero=False),
                    axis=alt.Axis(format=".2f", tickCount=4)),
            tooltip=[alt.Tooltip("时间:O", title=tr("时间")), alt.Tooltip("参考汇率:Q", title=tr("参考汇率"), format=".2f")])
        chart = chart.properties(background="transparent", height=165).configure_view(fill="transparent", strokeOpacity=0).configure_axis(gridOpacity=.14, domain=False)
        st.altair_chart(chart, theme=None)
    if step:
        advanced = orders(owner, step)
    if step == 1:
        history(owner)
        return
    if step >= 2:
        st.header(tr("07:05 银行回执"))
        submitted = [o for o in advanced if o["sent"]]
        if not submitted:
            st.info(tr("无有效订单"))
        for o in submitted:
            events = [e for e in o["events"] if e[0] != "11:00"]
            receipt = dict(o, events=events, state=events[-1][1], refund="0.00")
            with st.expander(tr("订单 " + o["id"] + " · " + receipt["state"]), expanded=True):
                show_receipt(receipt)
        unseen = [o for o in submitted if o["state"] == "已到账" and o["id"] not in st.session_state.get("fx_seen", set())]
        if unseen and not st.session_state.get("fx_opened") and not st.session_state.get("clear_opened"):
            st.session_state.fx_seen = st.session_state.get("fx_seen", set()) | {o["id"] for o in unseen}
            fx_dialog(unseen[0])
        returned = [o for o in submitted if o["state"] == "已退汇"]
        if step == 3 and returned:
            st.divider()
            st.header(tr("11:00 退回记录"))
            st.button("RemitGuide Refund Open API", disabled=True)
            for o in returned:
                with st.expander(tr("退款入账 · " + o["id"]), expanded=True):
                    show_receipt(dict(o, events=[e for e in o["events"] if e[0] == "11:00"]))
        return
    clock = 0 if h == 23 else h + 1
    if st.session_state.page == "向香港汇款":
        payment(owner, clock)
    elif st.session_state.page == "汇款记录":
        history(owner)
    else:
        st.session_state.page = "向香港汇款"
        payment(owner, clock)


if __name__ == "__main__":
    main()
