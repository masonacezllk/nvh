import streamlit as st
import pandas as pd
import sqlite3
from syslink import SysLink

st.set_page_config(
    page_title="大纲取号",
    page_icon="📋",
)

# 检查登录状态
if not st.session_state.get('authentication_status'):
    st.error("请先登录")
    st.stop()
else:
    username = st.session_state['name']
    loginAuthorization = st.session_state['loginAuthorization']
    task_number_list = st.session_state['task_number_list']
    task_result = st.session_state['task_result']

# 获取登录信息
username = st.session_state.get('name')
loginAuthorization = st.session_state.get('loginAuthorization')

# 创建SysLink实例
syslink = SysLink()

# 数据库操作函数
def get_outline_data():
    """获取out_line表格数据"""
    try:
        conn = sqlite3.connect('instance/task.db')
        df = pd.read_sql_query("SELECT id, report_number, task_number, outline_number FROM out_line ORDER BY id DESC", conn)
        conn.close()
        
        # 隐藏id列，重命名表头
        if not df.empty:
            df = df.drop(columns=['id'])  # 隐藏id列
            df = df.rename(columns={
                'report_number': '报告号',
                'task_number': '任务号', 
                'outline_number': '大纲编号'
            })
        
        return df
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return pd.DataFrame()

def get_max_outline_number():
    """获取当前最大的outline_number"""
    try:
        conn = sqlite3.connect('instance/task.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(outline_number) FROM out_line")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] is not None else 0
    except Exception as e:
        st.error(f"获取最大大纲号失败: {e}")
        return 0

def check_duplicate_record(report_number, task_number):
    """检查是否已存在相同的任务号和报告号记录"""
    try:
        conn = sqlite3.connect('instance/task.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM out_line WHERE report_number = ? AND task_number = ?",
            (report_number, task_number)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        st.error(f"检查重复记录失败: {e}")
        return False

def add_outline_record(report_number, task_number):
    report_number = str(report_number)
    task_number = str(task_number)
    """添加新的out_line记录"""
    try:
        # 首先检查是否已存在相同的记录
        if check_duplicate_record(report_number, task_number):
            return False, "该任务号和报告号已预约，请勿重复预约"
        
        max_outline = get_max_outline_number()
        new_outline_number = max_outline + 1
        
        conn = sqlite3.connect('instance/task.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO out_line (report_number, task_number, outline_number) VALUES (?, ?, ?)",
            (report_number, task_number, new_outline_number)
        )
        conn.commit()
        conn.close()
        return True, str(new_outline_number)  # 确保返回字符串
    except Exception as e:
        st.error(f"添加记录失败: {e}")
        return False, str(e)

# 定义on_change回调函数
def on_task_selected():
    """当任务号选择变化时的回调函数"""
    selected_task = st.session_state.task_select
    if selected_task and task_number_list:
        task_index = task_number_list.index(selected_task)
        
        # 调用load_task函数获取报告号
        table_data, report_numbers, report_item_name, check_flag = syslink.load_task(
            loginAuthorization, username, task_index, task_result
        )
        if check_flag and report_numbers:
            st.session_state['report_numbers'] = report_numbers
            st.session_state['last_task_index'] = task_index
            st.session_state['table_data'] = table_data
            st.session_state['report_item_name'] = report_item_name
        else:
            st.session_state['report_numbers'] = []
            st.session_state['table_data'] = {}
            st.session_state['report_item_name'] = []

# 显示out_line表格
st.subheader("大纲取号记录表")
col1, col2 = st.columns(2)

# 第一个selectbox - 选择任务号（使用on_change回调）
if task_number_list:
    with col1:
        selected_task = st.selectbox(
            "选择任务号",
            options=task_number_list,
            index=0,
            key="task_select",
            on_change=on_task_selected
        )
    
    if not st.session_state.get('report_numbers'):
        st.session_state['report_numbers'] = []
        
    with col2:
        selected_report = st.selectbox(
            "选择报告号",
            options=st.session_state['report_numbers'],
            index=0,
            key="report_select"
        )
    
    # 预约按钮
    btn_book = st.button("预约", type="primary")
    
    # 处理预约按钮点击
    if btn_book and selected_task and selected_report:
        success, result = add_outline_record(selected_report, selected_task)
        if success:
            st.success(f"预约成功！新大纲号: {result}")
            # 刷新表格显示
            st.rerun()
        else:
            # 如果是重复预约，显示具体提示信息
            if "已预约" in result:
                st.warning(result)
            else:
                st.error(f"预约失败: {result}")
else:
    st.warning("没有可用的任务列表")
    
outline_df = get_outline_data()
if not outline_df.empty:
    st.dataframe(outline_df, width='stretch')
else:
    st.info("暂无大纲取号记录")
    
# 显示选中的报告号信息
col1,col2=st.columns(2)
if 'selected_report' in locals() and selected_report:
    st.success(f"已选择报告号: {selected_report}")
    
    # 显示任务信息
    if st.session_state.get('table_data'):
        with col1:
            st.subheader("任务信息")
            table_data = st.session_state['table_data']
            for key, value in table_data.items():
                if key != 'carInfo':  # 特殊处理carInfo
                    st.write(f"**{key}**: {value}")
        
        # 显示样车信息
        if 'carInfo' in table_data and table_data['carInfo']:
            with col2:
                st.subheader("样车信息")
                for i, car_info in enumerate(table_data['carInfo']):
                    st.write(f"**样车 {i+1}**:")
                    for car_key, car_value in car_info.items():
                        st.write(f"  - {car_key}: {car_value}")
# 退出登录按钮
if st.button("退出登录"):
    st.session_state['authentication_status'] = False
    st.session_state['name'] = None
    st.session_state['loginAuthorization'] = None
    st.session_state.pop('task_number_list', None)
    st.session_state.pop('task_result', None)
    st.session_state.pop('report_numbers', None)
    st.session_state.pop('last_task_index', None)
    st.session_state.pop('table_data', None)
    st.session_state.pop('report_item_name', None)
    st.rerun()
