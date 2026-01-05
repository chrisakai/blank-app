# retirement_approval_ui.py
import streamlit as st
import requests
import json
from datetime import datetime
import uuid

# 页面配置
st.set_page_config(
    page_title="员工退休方案审批系统",
    page_icon="🏢",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        margin: 5px 0;
    }
    .approval-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .pending {
        border-left: 5px solid #ff9800;
    }
    .approved {
        border-left: 5px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

def parse_request_data():
    """从查询参数或session state中解析Dify发送的数据"""
    try:
        # 方法1: 从查询参数获取（如果Dify通过URL传递数据）
        query_params = st.experimental_get_query_params()
        
        if 'data' in query_params:
            # 假设数据通过base64编码在URL中
            import base64
            encoded_data = query_params['data'][0]
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            return json.loads(decoded_data)
        
        # 方法2: 直接从session state获取（如果数据已存储）
        if 'dify_request_data' in st.session_state:
            return st.session_state.dify_request_data
            
    except Exception as e:
        st.error(f"解析请求数据时出错: {str(e)}")
    
    return None

def load_request_data():
    """加载Dify发送的请求数据"""
    # 检查是否已有数据
    if 'request_data_loaded' in st.session_state and st.session_state.request_data_loaded:
        return st.session_state.pending_employees
    
    # 尝试从不同方式获取数据
    request_data = parse_request_data()
    
    if request_data:
        # 存储Dify回调信息
        st.session_state.dify_callback_url = request_data.get('callback_url')
        st.session_state.dify_api_key = request_data.get('api_key')
        st.session_state.workflow_run_id = request_data.get('workflow_run_id')
        
        # 处理员工数据
        employees = request_data.get('employees', [])
        
        # 为每个员工生成唯一的选择键，避免重复
        for emp in employees:
            emp['choice_key'] = f"choice_{emp['id']}_{uuid.uuid4().hex[:8]}"
            emp['submit_key'] = f"submit_{emp['id']}_{uuid.uuid4().hex[:8]}"
        
        # 保存到session state
        st.session_state.pending_employees = employees
        st.session_state.request_data_loaded = True
        
        return employees
    else:
        # 如果没有数据，显示空列表
        st.session_state.pending_employees = []
        return []

def send_approval_to_dify(employee_id, choice):
    """发送单条审批结果回Dify"""
    if 'dify_callback_url' not in st.session_state or 'dify_api_key' not in st.session_state:
        st.error("请确保Dify已发送完整的请求数据")
        return False
    
    callback_url = st.session_state.dify_callback_url
    api_key = st.session_state.dify_api_key
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 根据Dify Workflow的输入变量配置
    payload = {
        "inputs": {
            "employee_id": employee_id,
            "approval_choice": choice,
            "action": "manager_approval",
            "timestamp": datetime.now().isoformat()
        },
        "response_mode": "blocking",
        "user": "retirement_system"
    }

    try:
        response = requests.post(callback_url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            
            # 保存到历史记录
            if 'approval_history' not in st.session_state:
                st.session_state.approval_history = []

            st.session_state.approval_history.append({
                "employee_id": employee_id,
                "choice": choice,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dify_response": result.get('data', {})
            })
            
            # 更新员工状态
            for emp in st.session_state.pending_employees:
                if emp['id'] == employee_id:
                    emp['status'] = 'approved'
                    emp['approved_choice'] = choice
                    emp['approved_time'] = datetime.now().isoformat()
                    break
            
            return True
        else:
            st.error(f"提交失败 (状态码: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        st.error(f"连接错误: {str(e)}")
        return False

def batch_send_to_dify(approvals):
    """批量发送审批结果回Dify"""
    if 'dify_callback_url' not in st.session_state or 'dify_api_key' not in st.session_state:
        st.error("请确保Dify已发送完整的请求数据")
        return False
    
    callback_url = st.session_state.dify_callback_url
    api_key = st.session_state.dify_api_key
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "batch_approvals": json.dumps(approvals),
            "action": "batch_manager_approval",
            "total_count": len(approvals),
            "timestamp": datetime.now().isoformat()
        },
        "response_mode": "blocking",
        "user": "retirement_system"
    }

    try:
        response = requests.post(callback_url, headers=headers, json=payload)
        if response.status_code == 200:
            return True
        else:
            st.error(f"批量提交失败: {response.text}")
            return False
    except Exception as e:
        st.error(f"连接错误: {str(e)}")
        return False

def main():
    st.title("🏢 员工退休方案审批系统")
    st.markdown("---")
    
    # 显示当前审批批次
    st.sidebar.header("📅 审批批次")
    batch_date = st.sidebar.date_input("选择审批日期", datetime.now())
    
    # Dify信息显示（从请求中获取）
    st.sidebar.header("🔗 Dify 连接信息")
    if 'workflow_run_id' in st.session_state:
        st.sidebar.info(f"Workflow Run ID: `{st.session_state.workflow_run_id}`")
    
    # 手动配置（备用）
    st.sidebar.header("⚙️ API 配置（备用）")
    dify_api_key = st.sidebar.text_input("Dify API Key", 
                                        value=st.session_state.get('dify_api_key', ''),
                                        type="password")
    dify_callback_url = st.sidebar.text_input("Dify Callback URL",
                                             value=st.session_state.get('dify_callback_url', ''))
    
    # 如果通过备用方式配置，则更新session state
    if dify_api_key and dify_api_key != st.session_state.get('dify_api_key', ''):
        st.session_state.dify_api_key = dify_api_key
    if dify_callback_url and dify_callback_url != st.session_state.get('dify_callback_url', ''):
        st.session_state.dify_callback_url = dify_callback_url
    
    # 数据加载部分
    st.header("📋 待审批员工列表")
    
    # 加载Dify发送的数据
    pending_employees = load_request_data()
    
    if not pending_employees:
        st.warning("等待Dify发送审批数据...")
        st.info("""
        ### 如何接收Dify数据：
        1. Dify Workflow需要发送POST请求到本应用的URL
        2. 请求体应包含员工审批数据
        3. 数据格式示例：
        ```json
        {
          "workflow_run_id": "xxx",
          "callback_url": "https://api.dify.ai/...",
          "api_key": "your-api-key",
          "employees": [...]
        }
        ```
        """)
        
        # 演示模式开关
        if st.checkbox("启用演示模式（仅测试）"):
            demo_data = {
                "workflow_run_id": "demo-workflow-123",
                "callback_url": "https://api.dify.ai/v1/workflows/demo/run",
                "api_key": "demo-key",
                "employees": [
                    {
                        "id": "EMP001",
                        "name": "张三",
                        "gender": "男",
                        "age": 60.0,
                        "employee_type": "白领",
                        "manager_name": "张经理",
                        "manager_email": "zhang.manager@company.com",
                        "qualification": "男性 ≥59.5岁",
                        "branch": "123",
                        "status": "pending"
                    }
                ]
            }
            st.session_state.dify_request_data = demo_data
            st.session_state.request_data_loaded = False
            st.rerun()
        
        return
    
    # 显示待审批员工
    approved_count = 0
    for emp in pending_employees:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                status_class = "approved" if emp.get('status') == 'approved' else "pending"
                st.markdown(f"""
                <div class='approval-card {status_class}'>
                    <h3>{emp['name']} ({emp['gender']}, {emp['age']}岁)</h3>
                    <p><strong>员工ID:</strong> {emp['id']}</p>
                    <p><strong>员工类型:</strong> {emp['employee_type']}</p>
                    <p><strong>符合条件:</strong> {emp['qualification']}</p>
                    <p><strong>对应经理:</strong> {emp['manager_name']} ({emp['manager_email']})</p>
                    <p><strong>分支:</strong> {emp['branch']}</p>
                    {f'<p><strong>✅ 已审批:</strong> {emp.get("approved_choice", "")} ({emp.get("approved_time", "")})</p>' if emp.get('status') == 'approved' else ''}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if emp.get('status') != 'approved':
                    st.markdown("### 选择方案")

                    # 根据分支显示不同选项
                    if emp['branch'] == '123':
                        option = st.radio(
                            "请选择:",
                            ["Flexible retirement", "Retire at legal age", "Rehire"],
                            key=emp['choice_key'],
                            index=None
                        )
                    else:
                        option = st.selectbox(
                            "分支4方案:",
                            ["待定方案1", "待定方案2", "待定方案3"],
                            key=emp['choice_key'],
                            index=None
                        )

                    # 提交按钮
                    if st.button(f"提交 {emp['name']}", key=emp['submit_key']):
                        if option:
                            success = send_approval_to_dify(emp['id'], option)
                            if success:
                                st.success(f"✅ 已提交 {emp['name']} 的审批: {option}")
                                st.rerun()
                        else:
                            st.warning("请先选择审批方案")
                else:
                    st.success("✅ 已审批")
                    st.info(f"方案: {emp.get('approved_choice', '未知')}")
        
        # 统计已审批数量
        if emp.get('status') == 'approved':
            approved_count += 1
    
    # 批量审批区域
    st.markdown("---")
    st.header("📤 批量提交")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ 提交所有待审批", type="primary"):
            # 获取所有选择
            approvals = []
            for emp in pending_employees:
                if emp.get('status') != 'approved':
                    # 获取选项值
                    choice = st.session_state.get(emp['choice_key'])
                    if choice:
                        approvals.append({
                            "employee_id": emp['id'],
                            "employee_name": emp['name'],
                            "choice": choice,
                            "timestamp": datetime.now().isoformat(),
                            "branch": emp['branch']
                        })
            
            if approvals:
                success = batch_send_to_dify(approvals)
                if success:
                    st.success(f"✅ 已批量提交 {len(approvals)} 条审批")
                    # 更新状态
                    for emp in pending_employees:
                        if emp.get('status') != 'approved':
                            choice = st.session_state.get(emp['choice_key'])
                            if choice:
                                emp['status'] = 'approved'
                                emp['approved_choice'] = choice
                    st.rerun()
            else:
                st.warning("没有待提交的审批")

    with col2:
        st.metric("待审批", len([e for e in pending_employees if e.get('status') != 'approved']))

    with col3:
        st.metric("已审批", approved_count)

    # 审批历史
    st.markdown("---")
    with st.expander("📜 审批历史记录"):
        if 'approval_history' in st.session_state and st.session_state.approval_history:
            for record in st.session_state.approval_history:
                st.write(f"**{record['timestamp']}** - {record.get('employee_id', '未知ID')}: {record['choice']}")
        else:
            st.info("暂无审批历史")
    
    # 调试信息（可选）
    with st.expander("🔍 调试信息"):
        st.json({
            "total_employees": len(pending_employees),
            "approved_count": approved_count,
            "has_callback_url": 'dify_callback_url' in st.session_state,
            "has_api_key": 'dify_api_key' in st.session_state,
            "workflow_run_id": st.session_state.get('workflow_run_id', '未设置')
        })

if __name__ == "__main__":
    # 初始化session state
    if 'request_data_loaded' not in st.session_state:
        st.session_state.request_data_loaded = False
    
    main()
