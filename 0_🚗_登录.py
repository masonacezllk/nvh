import streamlit as st
from syslink import SysLink

st.set_page_config(
    layout='wide',
    page_title="登录",
    page_icon="👋",
)

st.write("# NVH小程序 👋")

st.sidebar.success("选择页面开始.")

# 创建SysLink实例
syslink = SysLink()

# 登录表单
with st.form("login_form"):
    st.subheader("登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    submit_button = st.form_submit_button("登录")

if submit_button:
    if username and password:
        # 调用syslink的login函数
        loginAuthorization, task_number_list, task_result, login_flag, login_msg = syslink.login(username, password)
        
        if login_flag:
            st.session_state['authentication_status'] = True
            st.session_state['name'] = username
            st.session_state['loginAuthorization'] = loginAuthorization
            st.session_state['task_number_list'] = task_number_list
            st.session_state['task_result'] = task_result
            
            # 登录成功后跳转到大纲取号页面
            st.success(f"登录成功！正在跳转到大纲取号页面...")
            st.switch_page("pages/1_📋_大纲取号.py")
        else:
            st.session_state['authentication_status'] = False
            st.error(f"登录失败: {login_msg}")
    else:
        st.warning("请输入用户名和密码")

# 显示登录状态
if st.session_state.get('authentication_status'):
    if st.button("退出登录"):
        st.session_state['authentication_status'] = False
        st.session_state['name'] = None
        st.session_state['loginAuthorization'] = None
        st.rerun()
    
elif st.session_state.get('authentication_status') is False:
    st.error('用户名或密码不正确')
else:
    st.warning('请输入用户名和密码')
