"""English display strings. Order data and simulation states retain their original keys."""
import re
import streamlit as st

_STRINGS = """
每 100 港元所需人民币 · 香港时间|CNY per 100 HKD · Hong Kong time
锁价消除的模拟到账波动区间|Simulated credit range removed by locking
按预约至开窗各时点预计到账的最高值减最低值计算。锁价后区间为零；该值不是节省金额。|Highest minus lowest projected credit from booking to opening. Locking fixes the range at zero. This measures variability, not savings.
海湾银行|Bay Bank
明港银行|Minggang Bank
远洋银行|Ocean Bank
中大银行|CU Bank
香港银行|Hong Kong Bank
张三|Zhang San
陈大文|Chen Daiwen
香港居民身份证|Hong Kong identity card
中国大陆居民身份证|Mainland resident ID
护照|Passport
选择登记地址，或输入新地址进行核验。|Select a registered address or type an address to verify.
请检查地址格式：使用英文、半角逗号和一个空格，门牌写作 No.77。|Use English, a comma followed by one space, and a street number such as No.77.
无效地址：请核对地区、区域与 Hong Kong 的组合。|Invalid address. Check the district, region and Hong Kong suffix.
请填写收款人姓名。|Enter the recipient's name.
本模拟路线要求半角数字，手机号为 8 位，账号为 8 至 16 位。|Use digits 0–9. Enter 8 digits for a phone number or 8–16 for an account.
付款总额须大于手续费。|The total must exceed the fees.
此号码未取得可用收款登记。请核对或改用银行账户。|No registration matches this phone number. Check it or use a bank account.
请通过付款银行核对本人留档资料。|Contact the paying bank to verify your registered details.
收款资料未能核实，请与收款人确认。|Recipient details could not be verified.
未能查到收款账户|Receiving account not found
收款账户与付款人登记身份不一致，请使用本人的收款资料。|The receiving account belongs to another person. Use your own details.
请使用英文拼音：|Enter the registered pinyin name. 
需要全部大写并无空格。|Use uppercase letters without spaces.
请核对英文姓名拼写。|Check the spelling of the English name.
收款人英文姓名与登记资料不匹配。|The name does not match the registration. 
证件类型与该收款人的演示档案不匹配。|Document type does not match the profile.
请检查证件号码格式，参照使用手册中的虚构示例。|Check the document number format against the fictional example in the guide.
证件号码与收款人的演示档案不匹配。|Document number does not match the profile.
自动预检已通过。|Pre-check passed.
已预约|Booked
已提交|Submitted
已到账|Credited
已拒绝|Rejected
确认中|Pending confirmation
退款在途|Refund pending
已退汇|Refunded
未提交|Not submitted
待修正|Correction needed
已通过|Verified
待核实|Awaiting verification
银行复核中|Under bank review
受限|Restricted
待授权|Authorization required
待补资料|Details required
直接提交|Submitted at opening
对照组在开窗时提交。|Baseline payment submitted at opening.
执行前余额不足，未扣款。|Insufficient balance at execution. No debit made.
已发送至模拟银行。|Sent to the simulated bank.
银行拒绝本次交易，未扣款。|Bank rejected the transfer. No debit made.
收款行已确认入账。|Receiving bank confirmed credit.
付款行已扣款，尚待收款行回执。|Debited. Awaiting receiving bank confirmation.
原交易收到收款行入账回执。|Receiving bank confirmed credit for the original transfer.
收款行通知：提交后账户暂停入账，原路退回。|Receiving bank suspended credit after submission. Returning funds to the payer.
收款行退回，等待退款入账。|Payment returned. Refund pending.
退款已入付款账户，原手续费不退。|Refund credited to the payer. Original fees retained.
可用余额不足|Insufficient balance
超过单笔转账额度|Per-transfer limit exceeded
超过当日剩余转账额度|Remaining daily limit exceeded
（可用| (available
收款账户核验|Receiving account check
陈大文在中大银行没有登记账户，请选择香港银行。|Chen Daiwen has no CU Bank account. Select Hong Kong Bank.
返回选择收款行|Change receiving bank
付款账户核验未通过|Funding account check failed
请降低付款金额，或返回表单选择其他付款账户。|Reduce the amount or choose another funding account.
返回修改|Edit transfer
锁价比较|Rate lock comparison
锁定报价|Locked rate
开窗报价|Opening rate
锁价实收|Credit at locked rate
开窗提交预计实收|Estimated credit at opening
锁价相对开窗的到账差额|Credit difference vs opening
本笔按人民币到账，无汇率敞口。|This payment settles in CNY and has no FX exposure.
锁价提前确定了到账金额。正数表示锁价多收，负数表示锁价少收。比较采用同一银行、金额和手续费。|Locking fixed the amount in advance. A positive difference means more received and a negative one means less. Bank, amount and fees are held constant.
交易参考编号|Transaction ID
关联原交易|Original transaction
确认扣款|Amount debited
确认退回|Refund credited
收款人实际到账|Recipient credited
预约报价|Booked rate
实际执行汇率|Execution rate
提交次数|Submissions
待执行|Pending
待确认|Not yet confirmed
原扣款|Original debit
原手续费|Original fees
实退|Refund
历史回执 · 按原交易规则结算|Historical receipt · settled under earlier terms
查看锁价比较|View rate lock comparison
市场参考汇率|Opening bank rate
订单确认汇率|Locked rate
向香港汇款|Transfer to Hong Kong
中国内地|Mainland China
中国香港|Hong Kong
跨境支付通 · 本人账户汇款 · 教学模拟|Payment Connect · Own-account transfer · Simulation
付款账户资料|Funding account
付款账户|Payer
可用余额|Available balance
单笔额度|Per-transfer limit
今日剩余额度|Daily limit remaining
报价银行|Quoting bank
付款人登记地址（模拟）|Registered payer address (simulated)
收款人资料|Recipient
收款方式|Receiving method
银行账户|Bank account
香港手机号|Hong Kong mobile
香港收款银行|Receiving bank
收款手续费|Receiving fee
收款人英文登记姓名|Registered English name
收款人证件类型|Document type
收款人证件号码（仅输入手册中的虚构号码）|Document number (use fictional examples only)
收款账号|Account number
汇款金额|Transfer amount
付款总额 · CNY（含手续费）|Total debit · CNY (fees included)
收款币种|Receiving currency
下一步 · 核对汇款|Review transfer
核对汇款|Review transfer
比较其他可用银行|Compare available banks
选择付款银行|Select paying bank
付款银行|Paying bank
扣款|Debit
手续费|Fees
预计实收|Estimated credit
总扣款|Total debit
付款行手续费|Sending fee
收款行手续费|Receiving fee
兑换本金|Conversion principal
本小时有效；确认后保价至本次开窗。|Valid for this hour. Confirmation locks the rate until opening.
原报价已过期。原预计实收|Previous quote expired. Previous estimated credit
新预计实收|New estimated credit
接受本小时新报价|Accept updated quote
保存待处理申请|Save for review
确认汇款|Confirm transfer
确认预约并锁定报价|Book and lock rate
汇款记录|Transfer history
尚无预约。请先填写汇款。|No bookings yet. Enter a transfer first.
选择订单|Select transfer
模拟收款行通知|Simulate receiving bank notice
通知此笔交易暂停入账|Suspend credit for this transfer
请查询原交易；该笔付款已扣款。查询只读取银行的最新回执。|Payment debited. Check the original transfer for the latest bank receipt.
查询原交易|Check original transfer
模拟银行当前状态|Simulated bank status
补充资料或联系银行完成处理后，可重新填写申请。|Update your details or contact the bank, then rebook.
修改后重新预约|Edit and rebook
确定清空汇款记录？|Clear transfer history?
将删除当前演示的全部汇款记录。清空后无法恢复。|All transfers in this demo will be deleted. This cannot be undone.
取消|Cancel
确定清空|Confirm deletion
个人银行 · 教学模拟|Personal banking · Simulation
香港演示时间（HH:MM）|Hong Kong demo time (HH:MM)
确定时间|Apply time
请输入有效的 24 小时时间，例如 07:03。|Enter a 24-hour time such as 07:03.
已确认|Confirmed
夜间预约|Night booking
开窗提交|Opening submissions
银行回执|Bank receipts
退汇处理|Refund processing
清空记录|Clear records
官方参考汇率（模拟）|Official reference rate (simulated)
1 元人民币可兑换的港元数 · 香港时间|HKD per CNY · Hong Kong time
参考汇率|Reference rate
时间|Time
无有效订单|No submitted transfers
退回记录|Refund records
无订单|No transfers
退款入账|Refund credited
订单|Transfer
报价|Quote
尾号| ending in
实收|Credit
汇率|Rate
收款行|Receiving bank
（已计入总手续费）| (included in fees)
"""
_TERMS = dict(line.split("|", 1) for line in _STRINGS.strip().splitlines())
_PATTERN = re.compile("|".join(map(re.escape, sorted(_TERMS, key=len, reverse=True))))


# Normalize old event messages as well as current interface copy.
_PUBLIC_COPY = {
    " · 教学模拟": "", "（模拟）": "", "模拟": "", "香港演示时间": "香港时间",
    "（仅输入手册中的虚构号码）": "", "，参照使用手册中的虚构示例": "",
    "演示档案": "登记档案", "当前演示的": "当前的",
}
_PUBLIC_EN = {
    " · Simulation": "", " (simulated)": "", "Simulated ": "", "simulated ": "",
    "Simulate receiving bank notice": "Receiving bank notice",
    "Hong Kong demo time": "Hong Kong time", " (use fictional examples only)": "",
    " against the fictional example in the guide": "", "in this demo": "in this workspace",
}


def tr(value):
    if not isinstance(value, str):
        return value
    english = st.session_state.get("english", False)
    if english:
        value = _PATTERN.sub(lambda m: _TERMS[m.group()], value).translate(
            str.maketrans({"：": ":", "；": ";", "。": ".", "（": "(", "）": ")", "，": ",", "｜": "|"})
        )
    for old, new in (_PUBLIC_EN if english else _PUBLIC_COPY).items():
        value = value.replace(old, new)
    return value
