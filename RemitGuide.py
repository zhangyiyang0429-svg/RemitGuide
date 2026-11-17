import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="RemitGuide Prototype", page_icon="💸", layout="wide")

st.title("💸 RemitGuide: A Cross-border Payment Assistant")
st.markdown("*FTEC 5510 Project - Enhancing Payment Connect Experience*")

# 侧边栏导航
st.sidebar.header("导航栏")
app_mode = st.sidebar.selectbox("选择功能模块", [
    "1. 汇率与成本透明化 (Cost Transparency)", 
    "2. 预约前置检查机制 (Pre-order Check)", 
    "3. 场景实验对比 (Experiment Comparison)"
])

if app_mode == "1. 汇率与成本透明化 (Cost Transparency)":
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
        "预计到账": ["9,214.90 HKD", "9,220.84 HKD", "9,207.21 HKD"],
        "报价有效期": ["45s", "12s (即将过期)", "58s"]
    })
    st.table(mock_quotes)
    if st.button("选择最优报价并继续"):
        st.success("已锁定 Mock Bank B 的最优报价！")

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