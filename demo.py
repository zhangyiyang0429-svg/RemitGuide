import streamlit as st

st.set_page_config(page_title="RemitGuide", page_icon="💱")
st.title("RemitGuide 跨境汇款演示")
st.caption("南向汇款 · 模拟银行 · 香港时间")

times = ["23:30", "次日 06:59", "次日 07:00"]

if "stage" not in st.session_state:
    st.session_state.stage = 0
    st.session_state.events = []

stage = st.session_state.stage
events = st.session_state.events
st.metric("演示时钟", times[stage])

if stage == 0 and not events:
    st.write("收款资料已通过模拟预检，可以预约次日 07:00 提交。")
    if st.button("确认预约", type="primary"):
        events.append("23:30｜订单 DEMO-001 已预约，等待提交")
        st.rerun()

if events:
    st.subheader("订单 DEMO-001")
    for event in events:
        st.write(event)

    if stage < 2 and st.button(f"推进到{times[stage + 1]}"):
        st.session_state.stage += 1
        if st.session_state.stage == 2:
            events.append("07:00｜已向模拟银行提交订单 DEMO-001")
            events.append("07:00｜模拟银行返回成功回执")
        st.rerun()

if st.button("重新演示"):
    st.session_state.stage = 0
    st.session_state.events = []
    st.rerun()
