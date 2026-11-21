import streamlit as st
import pandas as pd
import random
import time

st.set_page_config(page_title="RemitGuide A/B Test", page_icon="📊", layout="wide")

st.title("📊 RemitGuide: 场景实验与量化对比 (A/B Test)")
st.markdown("*FTEC 5510 - 针对跨境支付通 (Payment Connect) 的预检机制效能验证*")
st.divider()

# ==========================================
# 1. 后台数据生成与处理引擎 (Data Engine)
# ==========================================
@st.cache_data
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
            exp_success = False # 实验组同样失败，但属于“事前安全阻断”，不进入清算网络
            
        data.append({
            "交易流水号": f"TXN_2026_{i:03d}",
            "触发场景": scenario,
            "控制组 (传统) 结果": "✅ 成功" if control_success else "❌ 失败 (底层拒单)",
            "实验组 (RemitGuide) 结果": "✅ 成功" if exp_success else "🛡️ 拦截 (前置阻断)"
        })
    return pd.DataFrame(data)

with st.spinner("正在生成并处理 80 笔合成交易数据..."):
    time.sleep(0.5)
    df_experiment = generate_synthetic_data()

# ==========================================
# 2. 动态计算指标 (Dynamic Calculation)
# ==========================================
total_cases = len(df_experiment)
control_success_count = len(df_experiment[df_experiment["控制组 (传统) 结果"] == "✅ 成功"])
exp_success_count = len(df_experiment[df_experiment["实验组 (RemitGuide) 结果"] == "✅ 成功"])

control_rate = control_success_count / total_cases * 100
exp_rate = exp_success_count / total_cases * 100
improvement = exp_rate - control_rate

# ==========================================
# 3. 渲染宏观指标大盘
# ==========================================
st.header("宏观量化成果 (基于 80 笔合成数据)")

m1, m2, m3, m4 = st.columns(4)
m1.metric("07:00 AM 交易成功率", f"{exp_rate:.1f}%", f"较对照组提升 {improvement:.1f}%")
m2.metric("基础录入错误拦截率", "100%", "拦截 100% 格式错误")
m3.metric("隐私异常场景脱敏率", "100%", "符合最小数据交换原则")
m4.metric("汇率过期引发纠纷数", "0 起", "消除汇率时间差客诉")

with st.expander("📊 查看底层 80 笔合成测试数据集 (Synthetic Dataset)", expanded=False):
    st.dataframe(df_experiment, use_container_width=True, hide_index=True)

st.divider()

# ==========================================
# 4. 微观场景双屏推演
# ==========================================
st.header("微观场景双屏推演 (8 大场景还原)")

scenario = st.selectbox("请选择要演示的极端/典型测试场景", [
    "1. 正常支付流 (Control & Exp: 均成功)", 
    "3. 收款人信息缺失/错误 (如全角字符/中文标点)", 
    "4. 汇率更新与过期 (Exp: 自动重载避免纠纷)", 
    "5. 显式银行拒绝 (AML 拦截)", 
    "8. 隐私例外与脱敏 (账户不符时的安全披露)"
])

c_left, c_right = st.columns(2)

if "3. 收款人信息缺失/错误" in scenario:
    with c_left:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("🕒 **23:30** - 银行 App 提示“服务未开启”。")
        st.write("🕒 **07:00** - 用户终于可以填单，地址手滑输入了中文逗号。")
        st.error("💥 **07:01** - 提交后，被清算系统底层（FPS/IBPS）直接拒单。导致资金退回。")
        
    with c_right:
        st.markdown("### 🟢 实验组 (RemitGuide)")
        st.write("🕒 **23:30** - 录入信息，**Pre-flight 引擎瞬间发现中文逗号，直接红字拦截并提示修改**。")
        st.write("🕒 **23:32** - 用户改为半角，预检 Pass，进入加密待发队列。")
        st.success("🎉 **07:00** - 自动调用 API 提交，无格式错误，一次性成功到账。")
        
elif "4. 汇率更新与过期" in scenario:
    with c_left:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("🕒 **06:55** - 用户打开 App，看到汇率 A，准备填单。")
        st.write("🕒 **07:05** - 填单耗时 10 分钟，此时汇率 A 已过期，刷新为汇率 B。")
        st.error("💥 **结果** - 银行按提交时的汇率 B 扣款，用户发现退款/实际到账金额与最初看到的严重不符，引发客诉纠纷。")
        
    with c_right:
        st.markdown("### 🟢 实验组 (RemitGuide)")
        st.write("🕒 **23:30** - 用户选定汇率 A 并提交预约。")
        st.write("🕒 **07:00** - 自动引擎启动，检测到汇率 A 已过有效期。")
        st.success("🎉 **结果** - 系统拦截旧报价，重新通过 API 拉取最新汇率并向用户发送更新通知后执行划转，消除信息差纠纷。")
        
elif "8. 隐私例外与脱敏" in scenario:
    with c_left:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("🕒 **07:01** - 交易因“收款人地址与开户行留存不符”被收款行拒绝。")
        st.error("💥 **结果** - 因隐私法限制，银行 App 只能模糊提示“收款人信息有误被拒”。用户陷入盲目试错。")
        
    with c_right:
        st.markdown("### 🟢 实验组 (RemitGuide)")
        st.write("🕒 **23:30** - 夜间预审 (Pre-flight Check) 发送脱敏查验请求。")
        st.success("🎉 **结果** - 获得特定状态码，在**不泄露真实开户地址**的前提下，精准提示：“请核对并重新输入收款人开户详细地址（含区/街道）。”")
        
elif "5. 显式银行拒绝" in scenario:
    with c_left:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("🕒 **07:01** - 资金盲目进入清算网络。")
        st.error("💥 **结果** - 收款行执行 AML 审查，命中制裁名单。交易被阻断，进入人工挂账，增加银行合规运营成本。")
        
    with c_right:
        st.markdown("### 🟢 实验组 (RemitGuide)")
        st.write("🕒 **23:30** - Pre-flight 引擎执行基础 AML 预检。")
        st.success("🎉 **结果** - 命中名单，订单标记为 Fail。事前拦截，阻止非法指令进入清算网络，缓释基础设施风险。")

else:
    with c_left:
        st.markdown("### 🔴 控制组 (传统流程)")
        st.write("🕒 **07:00** - 正常提交，交易成功。")
    with c_right:
        st.markdown("### 🟢 实验组 (RemitGuide)")
        st.write("🕒 **23:30** - 预检通过。")
        st.write("🕒 **07:00** - 自动提交，交易成功。")
