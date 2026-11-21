"""RemitGuide · 南向汇款教学模拟。启动：streamlit run demo.py"""
import hashlib
import json
import os
import re
import sqlite3
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import streamlit as st

D = Decimal
BANKS = ("海湾银行 A", "明港银行 B", "远洋银行 C")
HOURS = ("23:00",) + tuple(f"{h:02}:00" for h in range(8))
BASE = tuple(map(D, ("1.0800", "1.0780", "1.0820", "1.0850", "1.0830",
                    "1.0810", "1.0770", "1.0790", "1.0750")))
NORMAL = "正常"
ISSUES = (NORMAL, "手机号未登记", "收款币种不支持", "证件过期", "地址待核验",
          "收款资料无法核实", "超过累计额度", "账户受限", "授权失效",
          "用途资料待补充", "银行风险复核", "登记查询超时")
OUTCOMES = ("即时到账", "余额变动", "银行拒绝", "延迟回执", "退汇·仅手续费", "退汇·含汇差")
DB = Path(os.getenv("REMITGUIDE_DB", str(Path.home() / ".remitguide" / "demo.sqlite3")))


def money(value):
    return D(str(value)).quantize(D(".01"), rounding=ROUND_HALF_UP)


def quote(bank, hour, budget, currency):
    i = BANKS.index(bank)
    amount = money(budget)
    fee = (D("10"), money(max(D("2"), amount * D(".0015"))), D("18"))[i]
    rate = BASE[hour] + (D("0"), D("-.0012"), D(".0020"))[i] if currency == "HKD" else D("1")
    net = money(max(D("0"), amount - fee) * rate)
    key = f"{bank}|{hour}|{amount}|{currency}|{rate}|{fee}"
    return dict(bank=bank, hour=hour, total=str(amount), fee=str(money(fee)),
                rate=str(rate), net=str(net), currency=currency,
                ref=hashlib.sha256(key.encode()).hexdigest()[:10].upper())


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
    if D(q["total"]) > 50000 or issue == "超过累计额度":
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
            event(o, "07:05", "退款在途", "收款行退回，等待退款入账。")
    if step >= 3 and o["step"] < 3 and o["state"] == "退款在途":
        principal = D(q["total"]) - D(q["fee"])
        rate = D(q["rate"])
        if o["outcome"] == "退汇·含汇差" and q["currency"] == "HKD":
            rate += D(".0060")
            principal = D(q["net"]) / rate
        o["return_rate"] = str(rate)
        o["refund"] = str(money(principal))
        event(o, "11:00", "已退汇", "退款已入付款账户，原手续费不退。")
    o["step"] = max(o["step"], step)
    return o


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("CREATE TABLE IF NOT EXISTS orders(owner TEXT, id TEXT, body TEXT, PRIMARY KEY(owner,id))")
    return conn


def save(owner, order):
    with connect() as con:
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
                advance(order, step)
                con.execute("UPDATE orders SET body=? WHERE owner=? AND id=?",
                            (json.dumps(order, ensure_ascii=False), owner, order["id"]))
        return result


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
        ("退汇", "原手续费及汇差", NORMAL, "退汇·含汇差", False, "已退汇", "已退汇"),
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
                expected_refund = money(D(q["net"]) / (D(q["rate"])+D(".0060"))) if outcome.endswith("含汇差") else D("4990")
                checks.append(D(o["refund"]) == expected_refund)
            if category == "报价更新" and enhanced:
                old = quote(BANKS[0], 2, 5000, "HKD")
                checks.extend([quote_changed(old, q), o["used_rate"] == "1.0850", q["net"] == "5414.15"])
            checks.append(data["number"] not in json.dumps(o, ensure_ascii=False))
            results.append(dict(类型=category, 案例=title, 组别="增强组" if enhanced else "对照组",
                                订单=o["id"], 预检=initial[0] if enhanced else "未启用",
                                已纠错=corrected, 开窗成功=o["open_success"], 最终到账=o["state"]=="已到账",
                                提交次数=o["sent"], 预期=expected, 实际=o["state"], 通过=all(checks),
                                报价=q["ref"], 汇率=q["rate"], 退款=o["refund"], 事件=o["events"]))
    return results


def show_receipt(o):
    q = o["quote"]
    st.subheader(o["state"])
    st.caption(f"交易参考编号 {o['id']} · {q['bank']} · 报价 {q['ref']}")
    if o.get("parent"):
        st.caption("关联原交易 " + o["parent"])
    cols = st.columns(3)
    cols[0].metric("确认扣款 · CNY", o["debit"])
    cols[1].metric("确认退回 · CNY", o["refund"])
    cols[2].metric(f"预计实收 · {q['currency']}", q["net"])
    st.write(f"预约报价 {q['rate']}　｜　实际执行汇率 {o['used_rate'] or '待执行'}　｜　提交次数 {o['sent']}")
    if o["state"] == "已退汇":
        difference = money(D(o["debit"]) - D(o["refund"]))
        st.info(f"原扣款 {o['debit']} − 原手续费 {q['fee']} − 汇兑差额 "
                f"{money(difference-D(q['fee']))} = 实退 {o['refund']} CNY。退回汇率 {o['return_rate']}。")
    if o["sent"]:
        at_open = quote(q["bank"], 8, q["total"], q["currency"])
        st.caption(f"07:00 市场参考汇率 {at_open['rate']} · 订单确认汇率 {q['rate']}")
    for stamp, state, msg in o["events"]:
        st.write(f"**{stamp}　{state}**　{msg}")


def payment(owner):
    st.header("向香港汇款")
    st.caption("跨境支付通 · 内地 → 香港　｜　虚构账户和模拟银行报价")
    with st.expander("演示设置 · 时钟与模拟银行"):
        hour = st.select_slider("当前香港时间（23:00 至次日 07:00）", options=range(9),
                                format_func=lambda h: HOURS[h])
        issue = st.selectbox("银行预检场景", ISSUES)
        outcome = st.selectbox("执行及回执场景", OUTCOMES)
    st.caption(f"香港时间 {HOURS[hour]}　·　" + ("服务窗口开放" if hour == 8 else "可预约次日 07:00 汇款"))
    bank = st.selectbox("付款账户", BANKS, format_func=lambda b: b + (" · 常用人民币账户" if b == BANKS[0] else " · 人民币账户"))
    method = st.radio("收款方式", ("银行账户", "香港手机号"), horizontal=True)
    recipient_bank = st.selectbox("香港收款银行", ("演示收款行甲", "演示收款行乙")) if method == "银行账户" else ""
    name = st.text_input("收款人登记姓名（仅用虚构资料）", "演示客户")
    number = st.text_input("收款账号" if recipient_bank else "香港手机号（+852）",
                           "1234567890" if recipient_bank else "91234567", key="number_"+method)
    budget = st.number_input("付款总额 · CNY（含手续费）", 0.01, 1000000.0, 5000.0, step=100.0)
    currency = st.selectbox("收款币种", ("HKD", "CNY"))
    data = dict(name=name, method=method, number=number)
    fingerprint = (bank, method, recipient_bank, name, number, budget, currency)
    if st.button("下一步 · 核对汇款", type="primary"):
        st.session_state.review = fingerprint
        st.session_state.quote_hour = hour
        st.session_state.pop("bank_choice", None)
    if st.session_state.get("review") != fingerprint:
        return
    st.divider()
    st.subheader("核对汇款")
    choice = bank
    if st.checkbox("比较其他可用银行"):
        st.table([{"付款银行": b, "扣款 CNY": str(money(budget)), "手续费 CNY": r["fee"],
                   "汇率": r["rate"], f"实收 {currency}": r["net"]}
                  for b in BANKS for r in [quote(b, hour, budget, currency)]])
        choice = st.selectbox("选择付款银行", BANKS, index=BANKS.index(bank), key="bank_choice")
    q = quote(choice, hour, budget, currency)
    st.write(f"**{choice}**　·　{method}尾号 {number[-4:]}")
    cols = st.columns(3)
    cols[0].metric("总扣款 · CNY", q["total"])
    cols[1].metric("手续费 · CNY", q["fee"])
    cols[2].metric(f"预计实收 · {currency}", q["net"])
    st.caption(f"兑换本金 {money(D(q['total'])-D(q['fee']))} CNY × 汇率 {q['rate']}。"
               f"报价 {q['ref']}，本小时有效；确认后保价至本次开窗。")
    old = quote(choice, st.session_state.quote_hour, budget, currency)
    if quote_changed(old, q):
        st.warning(f"原报价已过期。原预计实收 {old['net']}，新预计实收 {q['net']} {currency}。")
        if st.button("接受本小时新报价"):
            st.session_state.quote_hour = hour
            st.rerun()
        return
    decision = check(data, q, issue)
    if decision[0] != "已通过":
        st.warning(decision[1])
    else:
        st.success("自动预检已通过。")
    if decision[0] in ("待修正", "受限"):
        return
    label = "保存待处理申请" if decision[0] != "已通过" else ("确认汇款" if hour == 8 else "确认预约并锁定报价")
    if st.button(label, type="primary"):
        o = reserve(q, decision, outcome)
        o["parent"] = st.session_state.pop("retry_parent", None)
        if hour == 8:
            advance(o, 1)
        save(owner, o)
        st.session_state.review = None
        st.session_state.page = "汇款记录"
        st.rerun()


def history(owner):
    st.header("汇款记录")
    rows = orders(owner)
    if not rows:
        st.info("尚无预约。请先填写汇款。")
        return
    with st.expander("演示时钟 · 推进全部现有订单"):
        cols = st.columns(3)
        for i, stamp in enumerate(("07:00 开窗", "07:05 回执", "11:00 退款"), 1):
            if cols[i-1].button(stamp):
                orders(owner, i)
                st.rerun()
    by_id = {o["id"]:o for o in rows}
    ident = st.selectbox("选择订单", list(by_id), format_func=lambda k: k+" · "+by_id[k]["state"])
    o = by_id[ident]
    show_receipt(o)
    if o["state"] in ("确认中", "退款在途"):
        st.info("请查询原交易；该笔付款已扣款。查询只读取银行的最新回执。")
        if st.button("查询原交易"):
            st.info("模拟银行当前状态：" + orders_by_id(owner, ident)["state"])
    if o["state"] in ("已拒绝", "未提交", "待授权", "待补资料", "银行复核中", "待核实"):
        st.caption("补充资料或联系银行完成处理后，可重新填写申请。")
        if st.button("修改后重新预约"):
            st.session_state.retry_parent = ident
            st.session_state.page = "向香港汇款"
            st.session_state.review = None
            st.rerun()


def orders_by_id(owner, ident):
    return next(o for o in orders(owner) if o["id"] == ident)


def evidence():
    st.header("对照实验")
    st.write("两组共用合成资料、模拟银行规则和回执。对照组在 07:00 直接提交，"
             "增强组可预检、响应纠错提示并提前锁价。结果仅描述本批合成案例。")
    if st.button("运行八类场景", type="primary"):
        st.session_state.results = experiments()
    rows = st.session_state.get("results", [])
    if not rows:
        return
    for group in ("对照组", "增强组"):
        group_rows = [r for r in rows if r["组别"] == group]
        n = len(group_rows)
        st.subheader(group)
        a,b,c = st.columns(3)
        for col, key in zip((a,b,c), ("开窗成功","最终到账","通过")):
            col.metric(key if key != "通过" else "测试通过", f"{sum(r[key] for r in group_rows)} / {n}")
        st.caption(f"自动预检直接通过 {sum(r['预检']=='已通过' for r in group_rows)} 笔 · "
                   f"主动修正 {sum(r['已纠错'] for r in group_rows)} / 1 个指定可纠错案例 · "
                   f"转人工复核 {sum(r['预检']=='银行复核中' for r in group_rows)} 笔。")
        for cat in ("报价更新", "退汇"):
            subset = [r for r in group_rows if r["类型"] == cat]
            st.caption(f"{cat}案例符合预期：{sum(r['通过'] for r in subset)} / {len(subset)}")
    st.dataframe([{k:v for k,v in r.items() if k!="事件"} for r in rows], hide_index=True)
    r = st.selectbox("追溯案例", rows, format_func=lambda r:f"{r['组别']} · {r['案例']} · {r['订单']}")
    st.table([dict(时间=t,状态=s,说明=m) for t,s,m in r["事件"]])
    st.download_button("下载本次实验结果", json.dumps(rows, ensure_ascii=False, indent=2),
                       "remitguide-results.json", "application/json")


def main():
    st.set_page_config(page_title="RemitGuide · 跨境汇款", page_icon="💱")
    owner = st.query_params.get("demo", "")
    if not re.fullmatch("[a-f0-9]{32}", owner):
        owner = uuid.uuid4().hex
        st.query_params["demo"] = owner
    st.session_state.setdefault("page", "向香港汇款")
    st.sidebar.title("RemitGuide")
    st.sidebar.caption("个人银行 · 教学模拟")
    for title in ("向香港汇款", "汇款记录", "对照实验"):
        if st.sidebar.button(title):
            st.session_state.page = title
    if st.session_state.page == "向香港汇款":
        payment(owner)
    elif st.session_state.page == "汇款记录":
        history(owner)
    else:
        evidence()


if __name__ == "__main__":
    main()
