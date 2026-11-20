import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="RemitGuide Prototype", page_icon="💸", layout="wide")

st.title("💸 RemitGuide: A Cross-border Payment Assistant")
st.markdown("*FTEC 5510 Project - Enhancing Payment Connect Experience*")

# 侧边栏导航
st.sidebar.header("导航栏")
app_mode = st.sidebar.selectbox("选择功能模块", [
    "0. 适用性查询与客户自查 (Service Applicability)",
    "1. 汇率与成本透明化 (Cost Transparency)",
    "2. 预约前置检查机制 (Pre-order Check)",
    "3. 场景实验对比 (Experiment Comparison)"
])

if app_mode == "0. 适用性查询与客户自查 (Service Applicability)":
    st.header("服务适用性查询与汇前客户自查")
    st.caption("基于 Payment Connect 模拟规则演示：先查通道适用性，再逐项完成汇前自查。")

    tab1, tab2, tab3 = st.tabs([
        "📋 客户汇前自助核查表",
        "🧭 适用性前置自检向导",
        "📊 场景适用性实例矩阵"
    ])

    with tab1:
        st.subheader("RemitGuide 跨境汇款客户自助核查表（汇前必看）")
        st.info("请逐项核对以下 7 项汇前条件；全部勾选确认后，即可解锁后续比价或预约预审提示。")

        c1 = st.checkbox("1. 【通道与方向】已明确本次汇款方向（南向：内地→香港 / 北向：香港→内地），且所选银行支持对应 Payment Connect 互联服务。")
        c2 = st.checkbox("2. 【身份资质】发起人持有符合对应汇款方向要求的有效证件（如内地身份证或香港身份证）。")
        c3 = st.checkbox("3. 【双方账户状态】汇出账户与收款账户均处于有效状态，且已开通对应跨境收付功能。")
        c4 = st.checkbox("4. 【发起时间窗口】已确认当前发起时段（南向常规实时时段为 07:00–23:00；若在 23:00–次日 07:00 发起，将使用预约前置检查排队）。")
        c5 = st.checkbox("5. 【收款人信息】已核对收款人姓名、银行代码（BIC/银行编号）、账号或 FPS 识别码填写完整且无误。")
        c6 = st.checkbox("6. 【字符与地址规范】姓名与地址与开户登记信息一致，且全部使用半角英文/数字，不含中文标点（如中文逗号 `，`）或全角空格。")
        c7 = st.checkbox("7. 【汇率与费用认知】已了解需在报价有效期内确认汇款，且若发生退汇，因汇率波动与时间差，退回金额可能与原扣款金额存在差异。")

        checklist_items = [c1, c2, c3, c4, c5, c6, c7]
        completed_count = sum(checklist_items)
        st.progress(completed_count / len(checklist_items))
        st.write(f"当前核查完成进度：**{completed_count} / {len(checklist_items)}** 项")

        if all(checklist_items):
            st.success("✅ 所有汇前自查项已确认完成！请通过左侧导航栏进入「1. 汇率与成本透明化」对比报价，或前往「2. 预约前置检查机制」提交夜间预约。")
        else:
            st.warning("⚠️ 尚有未确认的自查项，建议核对无误后再发起汇款，以降低退汇与汇兑损失风险。")

    with tab2:
        st.subheader("适用性前置自检向导")
        col1, col2 = st.columns(2)
        with col1:
            direction = st.selectbox("汇款方向", ["南向 (Mainland -> HK)", "北向 (HK -> Mainland)"])
            user_id_type = st.selectbox("发起人身份类型（模拟）", ["内地居民身份证", "香港居民身份证", "其他身份 / 未核验"])
            bank_support = st.selectbox("银行与收款方式支持度（模拟）", ["参与行 + 支持的收款方式 (账号/FPS识别码)", "非参与行 / 不支持的收款方式"])
        with col2:
            acct_ready = st.selectbox("账户跨境收付开通状态（模拟）", ["已开通对应跨境功能", "未开通 / 账户类型受限"])
            payee_match = st.selectbox("收款侧规则匹配状态（模拟）", ["收款侧状态与规则正常匹配", "收款侧账户状态或规则不匹配"])
            time_window = st.selectbox("当前发起时段（模拟）", ["交易时段内 (07:00 - 23:00)", "非交易时段 (如 23:30，待次日 07:00)"])

        if st.button("开始适用性检测"):
            reasons = []
            suggestions = []

            if bank_support != "参与行 + 支持的收款方式 (账号/FPS识别码)":
                reasons.append("所选银行或收款方式未接入当前 FPS–IBPS 互联服务。")
                suggestions.append("请切换至参与银行或受支持的收款方式（如银行账号 / FPS 识别码）。")

            if acct_ready != "已开通对应跨境功能":
                reasons.append("当前账户类型不支持跨境收付功能，或尚未开通对应权限。")
                suggestions.append("请先向开户行申请开通跨境收付权限，或切换至合规账户。")

            if direction == "南向 (Mainland -> HK)" and user_id_type != "内地居民身份证":
                reasons.append("南向通道对发起人身份资质有明确要求，当前模拟身份类型不符合南向业务规则。")
                suggestions.append("请核实身份资质是否满足南向规则，或改用银行常规跨境电汇通道。")

            if direction == "北向 (HK -> Mainland)" and user_id_type != "香港居民身份证":
                reasons.append("北向通道对发起人身份资质有明确要求，当前模拟身份类型不符合北向业务规则。")
                suggestions.append("请核实身份资质是否满足北向规则，或改用银行常规跨境电汇通道。")

            if payee_match != "收款侧状态与规则正常匹配":
                reasons.append("收款侧账户状态或规则不匹配（基于隐私保护与最小数据暴露原则，不展示收款人开户地址等敏感明细）。")
                suggestions.append("请与收款人本人核实收款账户状态及登记信息后再试。")

            if reasons:
                st.error("❌ 判定结果：不适用 / 暂不可提交")
                st.markdown("**原因说明：**")
                for r in reasons:
                    st.write(f"- {r}")
                st.markdown("**下一步建议：**")
                for s in suggestions:
                    st.write(f"- {s}")
            else:
                if "非交易时段" in time_window and direction == "南向 (Mainland -> HK)":
                    st.warning("⚠️ 判定结果：条件受限（可转预约前置检查）")
                    st.write("- **原因说明**：传统南向通道仅限 07:00–23:00 受理且不支持直接预下单。")
                    st.write("- **下一步建议**：请进入左侧「2. 预约前置检查机制」，完成格式与 AML/收款人预审后，系统将于次日 07:00 自动提交。")
                else:
                    st.success("✅ 判定结果：适用（可正常进入比价与汇款流程）")
                    st.write("- **下一步建议**：满足身份、账户及通道要求，可直接进入「1. 汇率与成本透明化」对比报价。")

    with tab3:
        st.subheader("适用性判定实例对照表（模拟规则库）")
        cases_df = pd.DataFrame([
            {
                "场景编号": "CASE-01",
                "汇款方向": "南向 (Mainland → HK)",
                "身份与账户条件（模拟）": "内地身份证 + 支持跨境收付账户",
                "银行 / 币种 / 收款方式": "参与行 A / CNY→HKD / FPS 识别码",
                "发起时段": "07:00–23:00（交易时段）",
                "适用性判定": "✅ 适用",
                "系统展示原因与下一步指引": "满足身份、账户及通道要求；可直接进入多银行汇率与费用比价流程。"
            },
            {
                "场景编号": "CASE-02",
                "汇款方向": "南向 (Mainland → HK)",
                "身份与账户条件（模拟）": "内地身份证 + 支持跨境收付账户",
                "银行 / 币种 / 收款方式": "参与行 A / CNY→HKD / FPS 识别码",
                "发起时段": "23:30（非交易时段）",
                "适用性判定": "⚠️ 条件受限（可转预约预审）",
                "系统展示原因与下一步指引": "传统南向通道仅限 07:00–23:00 受理且不支持预下单；引导进入 RemitGuide 预约前置检查，预审通过后于次日 07:00 自动提交。"
            },
            {
                "场景编号": "CASE-03",
                "汇款方向": "北向 (HK → Mainland)",
                "身份与账户条件（模拟）": "香港身份证 + 支持跨境收付账户",
                "银行 / 币种 / 收款方式": "参与行 B / HKD→CNY / 银行账号",
                "发起时段": "14:00（交易时段）",
                "适用性判定": "✅ 适用",
                "系统展示原因与下一步指引": "符合北向准入条件；提示南北向规则存在差异，请确认汇率报价有效期后提交。"
            },
            {
                "场景编号": "CASE-04",
                "汇款方向": "南向 (Mainland → HK)",
                "身份与账户条件（模拟）": "其他身份类型 / 未完成合规身份核验",
                "银行 / 币种 / 收款方式": "参与行 A / CNY→HKD / FPS 识别码",
                "发起时段": "10:30（交易时段）",
                "适用性判定": "❌ 不适用",
                "系统展示原因与下一步指引": "发起人身份类型不符合该方向业务规则；建议核实身份资质或改用常规跨境电汇通道。"
            },
            {
                "场景编号": "CASE-05",
                "汇款方向": "北向 (HK → Mainland)",
                "身份与账户条件（模拟）": "香港身份证 + 未开通跨境权限账户",
                "银行 / 币种 / 收款方式": "参与行 C / HKD→CNY / 银行账号",
                "发起时段": "16:00（交易时段）",
                "适用性判定": "❌ 不适用",
                "系统展示原因与下一步指引": "当前账户类型不支持跨境收付功能；请先向开户行申请开通权限或切换至合规账户。"
            },
            {
                "场景编号": "CASE-06",
                "汇款方向": "南向 (Mainland → HK)",
                "身份与账户条件（模拟）": "内地身份证 + 支持跨境收付账户",
                "银行 / 币种 / 收款方式": "非参与行 / 不支持的收款方式",
                "发起时段": "11:00（交易时段）",
                "适用性判定": "❌ 不适用",
                "系统展示原因与下一步指引": "所选银行或收款方式未接入当前 FPS–IBPS 互联服务；建议切换至参与银行或受支持的收款方式。"
            },
            {
                "场景编号": "CASE-07",
                "汇款方向": "南向 (Mainland → HK)",
                "身份与账户条件（模拟）": "内地身份证 + 支持跨境收付账户",
                "银行 / 币种 / 收款方式": "参与行 B / CNY→HKD / 银行账号",
                "发起时段": "09:15（交易时段）",
                "适用性判定": "❌ 暂不可提交（校验未通过）",
                "系统展示原因与下一步指引": "提示“收款侧账户状态或规则不匹配，请与收款人核实”；遵循隐私保护与最小数据暴露原则，不泄露收款人开户地址等敏感明细。"
            }
        ])
        st.dataframe(cases_df, use_container_width=True, hide_index=True)

elif app_mode == "1. 汇率与成本透明化 (Cost Transparency)":
    st.header("多银行汇率与费用实时比价")
    col1, col2 = st.columns(2)
    with col1:
        send_amount = st.number_input("汇款金额 (CNY/HKD)", min_value=100, max_value=100000, value=10000, step=1000)
    with col2:
        transfer_dir = st.selectbox("汇款方向", ["南向 (Mainland -> HK)", "北向 (HK -> Mainland)"])
    
    st.subheader("各参与银行报价比较")
    # 模拟多银行 API 返回数据
    mock_quotes = pd.DataFrame({
        "银行名称": ["Mock Bank A", "Mock Bank B", "Mock Bank C"],
        "汇率 (CNY/HKD)": [1.0852, 1.0845, 1.0860],
        "手续费 (HKD)": [50.0, 20.0, 80.0],
        "预计到账": [
            f"{send_amount / 1.0852 - 50.0:,.2f} HKD",
            f"{send_amount / 1.0845 - 20.0:,.2f} HKD",
            f"{send_amount / 1.0860 - 80.0:,.2f} HKD"
        ],
        "报价有效期": ["45s", "12s (即将过期)", "58s"]
    })
    st.table(mock_quotes)
    if st.button("选择最优报价并继续"):
        st.success("已锁定 Mock Bank B 的最优报价！")

elif app_mode == "2. 预约前置检查机制 (Pre-order Check)":
    st.header("非交易时段预约与预审 (Pre-order & Pre-flight Check)")
    st.info("当前处于非交易时段 (如 23:30)，您可提交预约，系统将在明日 07:00 自动处理。")
    
    with st.form("pre_order_form"):
        remitter = st.text_input("汇款人姓名", "Jolyn Zhang")
        payee_account = st.text_input("收款人账号 / 银行代码", "1234-5678-9012")
        remit_address = st.text_area("收款人地址 (请确保与开户行一致)", "Chaoyang District，Beijing")
        
        submitted = st.form_submit_button("提交夜间预约与预审")
        
        if submitted:
            has_fullwidth_or_chinese = any(ord(char) > 127 for char in remit_address)
            
            if len(payee_account) < 10:
                st.error("⚠️ 错误：收款人账号格式不正确。")
            elif has_fullwidth_or_chinese:
                st.error("❌ 格式错误：检测到地址中包含全角字符或中文字符/标点（如中文逗号），不符合跨境清算系统规范，请修改为半角英文格式！")
            else:
                with st.spinner("正在向香港接收银行发送预审请求 (AML & 账户验证)..."):
                    time.sleep(1.5)
                st.success("✅ 预审通过 (Pass)！该订单已进入待发队列，将在明日 07:00 自动提交至 Payment Connect。")

elif app_mode == "3. 场景实验对比 (Experiment Comparison)":
    st.header("控制组 vs 实验组 (8大场景测试)")
    st.markdown("通过合成数据验证 RemitGuide 在 7 AM 时的交易成功率提升。")
    
    scenario = st.selectbox("选择测试场景", [
        "1. 正常支付流", "2. 服务限制与身份校验", "3. 收款人信息缺失/错误", 
        "4. 汇率更新与过期", "5. 显式银行拒绝", "6. 未确认/挂起交易", "7. 退款差异处理", "8. 隐私例外与脱敏"
    ])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("- 无夜间预审机制")
        st.write("- 7:00 准时直接提交")
        st.error("结果：因存在全角字符或格式错误，直接被银行拒单，导致延误与汇兑损失。")
    with c2:
        st.markdown("### 🟢 实验组 (RemitGuide 增强版)")
        st.write("- 夜间完成预审与纠错提示")
        st.write("- 7:00 自动提交合规订单")
        st.success("结果：交易一次性成功，成功率 100%。")
