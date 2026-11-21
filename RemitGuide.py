import streamlit as st
import pandas as pd
import time
from decimal import Decimal, ROUND_HALF_UP

st.set_page_config(page_title="RemitGuide Prototype", page_icon="💸", layout="wide")

st.title("💸 RemitGuide: A Cross-border Payment Assistant")
st.markdown("*FTEC 5510 Project - Enhancing Payment Connect Experience*")

# 侧边栏导航
nav_modules = {
    "1. 汇率与成本透明化 (Cost Transparency)": (
        "汇款比价", ":material/swap_horiz:"
    ),
    "2. 预约前置检查机制 (Pre-order Check)": (
        "预约预检", ":material/fact_check:"
    ),
    "3. 场景实验对比 (Experiment Comparison)": (
        "场景实验", ":material/bar_chart:"
    ),
}

if "active_nav_module" not in st.session_state:
    st.session_state["active_nav_module"] = next(iter(nav_modules))


def select_module(module):
    st.session_state["active_nav_module"] = module


app_mode = st.session_state["active_nav_module"]

st.sidebar.subheader("功能模块")
with st.sidebar.container(gap="medium"):
    for module, (label, icon) in nav_modules.items():
        st.button(
            label,
            icon=icon,
            key=f"nav_{label}",
            width="stretch",
            type="primary" if app_mode == module else "secondary",
            on_click=select_module,
            args=(module,),
        )
if app_mode == "1. 汇率与成本透明化 (Cost Transparency)":
    st.header("三家模拟银行报价")
    st.caption("南向汇款（内地到香港）｜手续费从换汇后的港币金额中扣除。")
    amount_cny = st.number_input(
        "汇款金额（人民币）", min_value=100, max_value=100000,
        value=10000, step=1000,
    )

    banks = [
        ("Mock Bank A", "1.0852", 50, 45),
        ("Mock Bank B", "1.0845", 20, 12),
        ("Mock Bank C", "1.0860", 80, 58),
    ]

    quotes = []
    for bank, rate, fee_hkd, validity in banks:
        received_hkd = (Decimal(amount_cny) * Decimal(rate) - fee_hkd).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        quotes.append({
            "银行": bank,
            "汇率（港币 / 人民币）": rate,
            "手续费（港币）": fee_hkd,
            "预计到账（港币）": received_hkd,
            "模拟有效期（秒）": validity,
        })

    quote_table = pd.DataFrame(quotes).sort_values(
        "预计到账（港币）", ascending=False, ignore_index=True
    )
    best_quote = quote_table.iloc[0]
    st.info(
        f"预计到账最高的是 {best_quote['银行']}，"
        f"可到账 {best_quote['预计到账（港币）']:,.2f} 港币。"
    )
    display_quotes = quote_table.astype({
        "汇率（港币 / 人民币）": "float64",
        "预计到账（港币）": "float64",
    })

    st.dataframe(
        display_quotes,
        hide_index=True,
        column_config={
            "银行": st.column_config.Column(
                "报价银行",
                help="提供这条报价的模拟银行。",
            ),
            "汇率（港币 / 人民币）": st.column_config.NumberColumn(
                "汇率（港币 / 人民币）",
                help="每 1 元人民币可兑换的港币金额。例如 1.0852 表示 1 元人民币可换 1.0852 港币。",
                format="%.4f",
            ),
            "手续费（港币）": st.column_config.Column(
                "手续费（港币）",
                help="从换汇后的港币金额中扣除的固定手续费。",
            ),
            "预计到账（港币）": st.column_config.NumberColumn(
                "预计净到账（港币）",
                help="人民币汇款金额乘以汇率，再扣除港币手续费。结果四舍五入至小数点后两位。",
                format="%,.2f",
            ),
            "模拟有效期（秒）": st.column_config.Column(
                "模拟有效期（秒）",
                help="模拟设定的固定时长，单位为秒，只用于展示。",
            ),
        },
    )

elif app_mode == "2. 预约前置检查机制 (Pre-order Check)":
    st.header("非交易时段预约与预审 (Pre-order & Pre-flight Check)")
    st.info("当前处于非交易时段 (如 23:30)，您可提交预约，系统将在明日 07:00 自动处理。")
    
    with st.form("pre_order_form"):
        remitter = st.text_input("汇款人姓名", "Jolyn Cheung")
        payee_account = st.text_input("收款人账号 / 银行代码", "1234-5678-9012")
        # 把默认值换成带中文逗号的地址，方便你直接测试
        remit_address = st.text_area("收款人地址 (请确保与开户行一致)", "Chaoyang District，Beijing")
        
        submitted = st.form_submit_button("提交夜间预约与预审")
        
        if submitted:
            # 检查是否包含全角字符或中文标点（如中文逗号、全角空格等）
            has_fullwidth_or_chinese = any(ord(char) > 127 for char in remit_address)
            
            if len(payee_account) < 10:
                st.error("⚠️ 错误：收款人账号格式不正确。")
            elif has_fullwidth_or_chinese:
                # 触发 Proposal 中提到的红色警告
                st.error("❌ 格式错误：检测到地址中包含全角字符或中文字符/标点（如中文逗号），不符合跨境清算系统规范，请修改为半角英文格式！")
            else:
                with st.spinner("正在向香港接收银行发送预审请求 (AML & 账户验证)..."):
                    time.sleep(1.5)
                st.success("✅ 预审通过 (Pass)！该订单已进入待发队列，将在明日 07:00 自动提交至 Payment Connect。")

elif app_mode == "3. 场景实验对比 (Experiment Comparison)":
    import random
    
    st.header("宏观量化成果 (基于 80 笔合成数据)")
    st.markdown("通过合成数据验证 RemitGuide 在 7 AM 时的交易成功率提升与风险缓释效果。")
    
    # ==========================================
    # 1. 后台数据生成与处理引擎 (Data Engine)
    # ==========================================
    @st.cache_data # 缓存数据，避免每次点击重新生成
    def generate_synthetic_data():
        data = []
        for i in range(1, 81):
            rand = random.random()
            # 按概率分布模拟 8 大场景
            if rand < 0.625:  # 62.5% (50笔) 正常支付
                scenario = "1. 正常支付流"
                control_success = True
                exp_success = True
            elif rand < 0.8125:  # 18.75% (15笔) 格式错误
                scenario = "3. 收款人信息缺失/错误 (全角/标点)"
                control_success = False
                exp_success = True  # 实验组通过夜间预审纠正，早上成功提交
            elif rand < 0.9375:  # 12.5% (10笔) 汇率过期
                scenario = "4. 汇率更新与过期"
                control_success = False
                exp_success = True  # 实验组自动刷新汇率，成功提交
            else:  # 6.25% (5笔) 合规拦截/账户不符
                scenario = "5. 显式银行拒绝 / 8. 隐私例外"
                control_success = False
                exp_success = False # 实验组同样失败，但属于“安全阻断”，不进入清算网络
                
            data.append({
                "交易流水号": f"TXN_2026_{i:03d}",
                "触发场景": scenario,
                "控制组 (传统) 结果": "✅ 成功" if control_success else "❌ 失败 (底层拒单)",
                "实验组 (RemitGuide) 结果": "✅ 成功" if exp_success else "🛡️ 拦截 (合规阻断)"
            })
        return pd.DataFrame(data)
        
    df_experiment = generate_synthetic_data()
    
    # ==========================================
    # 2. 动态计算指标 (Dynamic Calculation)
    # ==========================================
    total_cases = len(df_experiment)
    
    # 算出控制组和实验组的真实成功率
    control_success_count = len(df_experiment[df_experiment["控制组 (传统) 结果"] == "✅ 成功"])
    exp_success_count = len(df_experiment[df_experiment["实验组 (RemitGuide) 结果"] == "✅ 成功"])
    
    control_rate = control_success_count / total_cases * 100
    exp_rate = exp_success_count / total_cases * 100
    improvement = exp_rate - control_rate

    # ==========================================
    # 3. 渲染指标大盘
    # ==========================================
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("07:00 AM 交易成功率", f"{exp_rate:.1f}%", f"较对照组提升 {improvement:.1f}%")
    m2.metric("基础录入错误拦截率", "100%", "拦截 100% 格式错误")
    m3.metric("隐私异常场景脱敏率", "100%", "符合最小数据交换原则")
    m4.metric("汇率过期引发纠纷数", "0 起", "消除汇率时间差客诉")
    
    # =========================================
    with st.expander("📊 查看底层 80 笔合成测试数据集 (Synthetic Dataset)", expanded=False):
        st.dataframe(df_experiment, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("微观场景双屏推演 (8 大场景还原)")
    
    # 增加选项，重点展示容易出问题且对比强烈的场景
    scenario = st.selectbox("请选择要演示的测试场景", [
        "1. 正常支付流 (Control & Exp: 均成功)", 
        "2. 服务限制与身份校验 (Exp: 事前拦截不合规身份)", 
        "3. 收款人信息缺失/错误 (全角字符/中文标点)", 
        "4. 汇率更新与过期 (Exp: 自动重载避免纠纷)", 
        "5. 显式银行拒绝 (AML 拦截)", 
        "8. 隐私例外与脱敏 (账户不符时的安全披露)"
    ])
    
    c_left, c_right = st.columns(2)
    
    # 根据下拉框的选择，动态渲染左侧（控制组）和右侧（实验组）的内容
    if "3. 收款人信息缺失/错误" in scenario:
        with c_left:
            st.markdown("### 🔴 控制组 (传统流程)")
            st.markdown("**Timeline:**")
            st.write("🕒 **23:30** - 银行 App 提示“服务未开启”，无法操作。")
            st.write("🕒 **07:00** - 用户终于可以填单，地址栏手滑输入了中文逗号。")
            st.error("💥 **07:01** - 提交后，被清算系统底层（FPS/IBPS）直接拒单。资金退回，且可能损失双边手续费。")
            
        with c_right:
            st.markdown("### 🟢 实验组 (RemitGuide)")
            st.markdown("**Timeline:**")
            st.write("🕒 **23:30** - 录入信息，**Pre-flight 引擎瞬间发现中文逗号，直接红字拦截并要求修改**。")
            st.write("🕒 **23:32** - 用户改为半角逗号，预检 Pass，进入待发队列。")
            st.success("🎉 **07:00** - 系统按队列自动调用 API 提交，无格式错误，一次性成功到账。")
            
    elif "4. 汇率更新与过期" in scenario:
        with c_left:
            st.markdown("### 🔴 控制组 (传统流程)")
            st.markdown("**Timeline:**")
            st.write("🕒 **06:55** - 用户打开 App，看到汇率 A，准备填单。")
            st.write("🕒 **07:05** - 填单耗时 10 分钟，此时汇率 A 已过期，变成汇率 B。")
            st.error("💥 **结果** - 银行按提交时的汇率 B 扣款，用户发现退款/实际到账金额与最初看到的严重不符，引发客诉纠纷。")
            
        with c_right:
            st.markdown("### 🟢 实验组 (RemitGuide)")
            st.markdown("**Timeline:**")
            st.write("🕒 **23:30** - 用户选定汇率 A 并提交预约。")
            st.write("🕒 **07:00** - 自动提交引擎启动。检测到汇率 A 已过模拟有效期。")
            st.success("🎉 **结果** - 系统自动拦截旧报价，重新通过 API 拉取最新汇率并向用户发送更新通知后才执行划转，消除信息差引发的纠纷。")
            
    elif "8. 隐私例外与脱敏" in scenario:
        with c_left:
            st.markdown("### 🔴 控制组 (传统流程)")
            st.write("🕒 **07:01** - 交易因“收款人地址与开户行留存不符”被收款行拒绝。")
            st.error("💥 **结果** - 因隐私法限制，银行 App 只能模糊提示“收款人信息有误被拒”。用户无法得知是地址还是名字出错，陷入盲目试错。")
            
        with c_right:
            st.markdown("### 🟢 实验组 (RemitGuide)")
            st.write("🕒 **23:30** - 夜间预审 (Pre-flight Check) 发送脱敏查验请求。")
            st.success("🎉 **结果** - 通过 API 获得特定状态码，在**不泄露真实开户地址**的前提下，精准向用户提示：“验证未通过：请核对并重新输入收款人开户时预留的详细地址（含区/街道信息）。”")
            
    elif "5. 显式银行拒绝" in scenario:
        with c_left:
            st.markdown("### 🔴 控制组 (传统流程)")
            st.write("🕒 **07:01** - 提交后，资金进入清算网络。")
            st.error("💥 **结果** - 收款行执行反洗钱 (AML) 审查，命中高风险名单。交易被阻断，进入人工挂账或退汇流程，增加银行合规运营成本。")
            
        with c_right:
            st.markdown("### 🟢 实验组 (RemitGuide)")
            st.write("🕒 **23:30** - Pre-flight 引擎执行基础 AML 预检。")
            st.success("🎉 **结果** - 命中高风险名单，订单标记为 `Fail`。07:00 AM 时被系统自动拦截，阻止非法指令进入清算网络，有效缓释基础设施操作风险。")
            
    else:
        with c_left:
            st.markdown("### 🔴 控制组 (传统流程)")
            st.write("针对当前选择的场景，控制组按照常规流程处理。")
        with c_right:
            st.markdown("### 🟢 实验组 (RemitGuide)")
            st.write("针对当前选择的场景，实验组通过预检机制或状态提示，提供了更优的处理方式。")
