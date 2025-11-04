import streamlit as st
import sqlite3
from datetime import datetime, timedelta, date
import sys
import os
from streamlit_calendar import calendar
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from syslink import SysLink

def init_db():
    """初始化数据库连接"""
    conn = sqlite3.connect('instance/task.db')
    return conn

def get_calendar_events():
    """从数据库获取日历事件"""
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, start_date, end_date, task_name, user_name
        FROM my_calendar
    """)
    
    events = []
    for row in cursor.fetchall():
        event = {
            'id': row[0],
            'title': f"{row[3]}",
            'start': row[1],
            'end': row[2],
            'resourceId': 'a',
            'extendedProps': {
                'user_name': row[4],
                'task_name': row[3]
            }
        }
        events.append(event)
    
    conn.close()
    return events

def add_calendar_event(start_date, end_date, task_name, user_name):
    """添加新的日历事件到数据库"""
    conn = init_db()
    cursor = conn.cursor()
    
    # 获取下一个ID
    cursor.execute("SELECT MAX(id) FROM my_calendar")
    max_id = cursor.fetchone()[0]
    next_id = (max_id or 0) + 1
    
    cursor.execute("""
        INSERT INTO my_calendar (id, start_date, end_date, task_name, user_name)
        VALUES (?, ?, ?, ?, ?)
    """, (next_id, start_date, end_date, task_name, user_name))
    
    conn.commit()
    conn.close()
    return next_id

def delete_calendar_event(event_id):
    """删除日历事件"""
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM my_calendar WHERE id = ?", (event_id,))
    
    conn.commit()
    conn.close()
    return True

def get_calendar_event_by_details(start_date, end_date, task_name):
    """根据详细信息获取日历事件ID"""
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM my_calendar 
        WHERE start_date = ? AND end_date = ? AND task_name = ?
    """, (start_date, end_date, task_name))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

# 检查登录状态
if not st.session_state.get('authentication_status'):
    st.warning("请先在首页登录系统")
    st.stop()

# 获取登录信息
username = st.session_state.get('name')
task_number_list = st.session_state.get('task_number_list', [])
task_result = st.session_state.get('task_result')
loginAuthorization = st.session_state.get('loginAuthorization')

# 初始化SysLink实例
if 'syslink' not in st.session_state:
    st.session_state.syslink = SysLink()
syslink = st.session_state.syslink



# 显示日历
st.header("场地日历")

# 获取现有事件
events = get_calendar_events()
# 配置日历选项
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "slotMinTime": "06:00:00",
    "slotMaxTime": "22:00:00",
    "initialView": "dayGridMonth",
    "resourceGroupField": "building",
    "resources": [
        {"id": "a", "building": "场地A", "title": "场地A"},
    ],
    "initialDate": datetime.now().strftime("%Y-%m-%d"),
}

# 显示日历
calendar_result = calendar(
    events=events,
    options=calendar_options,
    custom_css="""
        .fc-event-past {
            opacity: 0.8;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc-event-title {
            font-weight: bold;
        }
        .fc-toolbar-title {
            font-size: 1.5em;
        }
    """
)

# 新增预约功能
st.header("新增预约")
# 预约表单

col1, col2, col3 = st.columns(3)

with col1:
    # 项目类型选择
    project_type = st.selectbox(
        "项目类型",
        ["R51", "R138"],
        key="project_type"
    )

with col2:
    # 任务单编号选择
    if task_number_list:
        task_number = st.selectbox(
            "任务单编号",
            task_number_list,
            key="task_number"
        )
    else:
        st.warning("暂无可用任务单")
        task_number = None

with col3:
    today = date.today()
    min_date = today
    max_date = today + timedelta(days=365)  # 1年范围
    
    reserveDate = st.date_input(
        "预约日期范围",
        (today, today),  # 默认选择当天作为范围
        min_date,
        max_date,
        format="YYYY-MM-DD",
    )

reserveBtn = st.button("新增预约")

# 处理预约逻辑
if reserveBtn:
    try:
        if not task_number:
            st.error("请选择任务单编号")
        elif not reserveDate:
            st.error("请选择预约日期")
        else:
            task_index = task_number_list.index(task_number)
            table_data, report_numbers, report_item_name, check_flag = syslink.load_task(
                loginAuthorization, username, task_index, task_result
            )
            
            # 检查是否选择了日期范围（两个日期）
            if isinstance(reserveDate, tuple) and len(reserveDate) == 2:
                start_date_obj, end_date_obj = reserveDate
            else:
                # 如果只选择了一个日期，则开始和结束日期相同
                start_date_obj = reserveDate
                end_date_obj = reserveDate
            
            # 构建任务名称
            factory_name = table_data['委托单位名称']
            tester_name = table_data['试验员']
            task_name = f"{tester_name},{project_type},{task_number},{factory_name}"
            
            # 设置开始和结束时间（假设预约全天）
            start_date = start_date_obj.strftime("%Y-%m-%d") + "T08:00:00"
            end_date = end_date_obj.strftime("%Y-%m-%d") + "T23:59:59"
            
            # 检查是否已有相同日期的预约
            existing_event_id = get_calendar_event_by_details(start_date, end_date, task_name)
            if existing_event_id:
                st.error(f"该日期已有相同任务的预约，预约ID: {existing_event_id}")
            else:
                # 添加新预约
                new_event_id = add_calendar_event(start_date, end_date, task_name, username)
                if new_event_id:
                    st.success(f"预约成功！预约ID: {new_event_id}")
                    st.rerun()
                else:
                    st.error("预约失败，请重试")
    except:
        st.error('预约日期请选两次，起始日期和终止日期，起始日期和终止日期可以为同一天。')



# 删除预约功能
st.header("删除预约")

events = get_calendar_events()
if events:
    # 创建删除选择框，按ID倒序排列
    event_options = {f"{event['id']}: {event['title']} ({event['start']})": event['id'] for event in events}
    event_keys = sorted(list(event_options.keys()), key=lambda x: int(x.split(':')[0]), reverse=True)
    selected_event = st.selectbox("选择要删除的预约", event_keys)
    
    if st.button("删除预约", type="secondary"):
        event_id = event_options[selected_event]
        if delete_calendar_event(event_id):
            st.success("预约删除成功！")
            st.rerun()
        else:
            st.error("删除失败")
else:
    st.info("暂无预约记录")

# 显示当前预约记录
st.header("当前预约记录")

events = get_calendar_events()
if events:
    # 转换为DataFrame显示，按ID倒序排列
    records = []
    for event in events:
        # 提取日期部分，去掉时间
        start_date = event['start'].split(' ')[0] if ' ' in event['start'] else event['start']
        end_date = event['end'].split(' ')[0] if ' ' in event['end'] else event['end']
        
        records.append({
            'ID': event['id'],
            '开始时间': start_date,
            '结束时间': end_date,
            '任务名称': event['title']
        })
    
    df = pd.DataFrame(records)
    df = df.sort_values('ID', ascending=False)  # 按ID倒序排列
    st.dataframe(df, width='stretch')
else:
    st.info("暂无预约记录")

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