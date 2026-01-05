# retirement_approval_ui.py
import streamlit as st
import requests
import json
from datetime import datetime
import base64
import urllib.parse
from typing import Dict, List, Optional

# 页面配置
st.set_page_config(
    page_title="员工退休方案审批系统",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .data-info {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def decode_url_data(encoded_data: str) -> Optional[Dict]:
    """解码URL参数中的数据"""
    try:
        # 先进行URL解码
        decoded_url = urllib.parse.unquote(encoded_data)
        
        # 然后进行Base64解码
        padding = 4 - len(decoded_url) % 4
        if padding != 4:
            decoded_url += "=" * padding
        
        # 替换URL安全的base64字符
        decoded_url = decoded_url.replace('-', '+').replace('_', '/')
        
        # 解码base64
        json_bytes = base64.b64decode(decoded_url)
        json_str = json_bytes.decode('utf-8')
        
        return json.loads(json_str)
    except Exception as e:
        st.error(f"数据解码失败: {str(e)}")
        return None

def load_dify_data():
    """从URL参数加载Dify发送的数据"""
    # 获取查询参数
    query_params = st.experimental_get_query_params()
    
    if 'data' in query_params:
        encoded_data = query_params['data'][0]
        return decode_url_data(encoded_data)
    
    return None

def initialize_session_state():
    """初始化session state"""
    if 'dify_data' not in st.session_state:
        st.session_state.dify_data = None
    if 'approval_history' not in st.session_state:
        st.session_state.approval_history = []
    if 'employee_choices' not in st.session_state:
        st.session_state.employee_choices = {}

def display_data_info(dify_data: Dict):
    """显示Dify数据信息"""
    with st.sidebar.expander("📦 数据信息", expanded=True):
        st.markdown(f"""
        <div class="data-info">
        <p><strong>数据来源:</strong> Dify Workflow</p>
        <p><strong>员工数量:</strong> {len(dify_data.get('employees', []))}</p>
        <p><strong>接收时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'workflow_run_id' in dify_data:
            st.code(f"Workflow ID: {dify_data['workflow_run_id']}")
        
        # 显示原始数据（调试用）
        if st.checkbox("显示原始数据"):
            st.json(dify_data)

def render_employee_card(emp: Dict, index: int):
    """渲染员工审批卡片"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        status_class = "approved" if emp.get('status') == 'approved' else "pending"
        approval_status = ""
        
        if emp.get('status') == 'approved':
            approval_status = f"<p><strong>✅ 已审批:</strong> {emp.get('approved_choice', '')}</p>"
        
        st.markdown(f"""
        <div class='approval-card {status_class}'>
            <h3>{emp['name']} ({emp['gender']}, {emp['age']}岁)</h3>
            <p><strong>员工ID:</strong> {emp['id']}</p>
            <p><strong>员工类型:</strong> {emp['employee_type']}</p>
            <p><strong>符合条件:</strong> {emp['qualification']}</p>
            <p><strong>对应经理:</strong> {emp['manager_name']} ({emp['manager_email']})</p>
            <p><strong>分支:</strong> {emp['branch']}</p>
            {approval_status}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if emp.get('status') != 'approved':
            st.markdown("### 选择方案")
            
            # 根据分支显示不同选项
            if emp['branch'] == '123':
                options = ["Flexible retirement", "Retire at legal age", "Rehire"]
            else:
                options = ["待定方案1", "待定方案2", "待定方案3"]
            
            # 创建选择框
            choice_key = f"choice_{emp['id']}_{index}"
            
            if choice_key not in st.session_state.employee_choices:
                st.session_state.employee_choices[choice_key] = None
            
            option = st.selectbox(
                "请选择方案:",
                options,
                key=choice_key,
                index=None,
                placeholder="选择审批方案..."
            )
            
            # 提交按钮
            if st.button(f"提交审批", key=f"submit_{emp['id']}_{index}"):
                if option:
                    # 模拟提交到Dify
                    st.session_state.employee_choices[choice_key] = option
                    emp['status'] = 'approved'
                    emp['approved_choice'] = option
                    emp['approved_time'] = datetime.now().isoformat()
                    
                    # 添加到历史记录
                    st.session_state.approval_history.append({
                        "employee_id": emp['id'],
                        "employee_name": emp['name'],
                        "choice": option,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    st.success(f"✅ 已提交 {emp['name']} 的审批: {option}")
                    st.rerun()
                else:
                    st.warning("请先选择审批方案")
        else:
            st.success("✅ 已审批")
            st.info(f"方案: {emp.get('approved_choice', '未知')}")

def send_approval_to_dify(employee_data: Dict, choice: str) -> bool:
    """发送审批结果回Dify（模拟实现）"""
    dify_data = st.session_state.dify_data
    
    if not dify_data or 'callback_url' not in dify_data:
        st.error("缺少Dify回调配置")
        return False
    
    callback_url = dify_data.get('callback_url')
    api_key = dify_data.get('api_key')
    
    if not callback_url or not api_key:
        st.error("Dify回调配置不完整")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "workflow_run_id": dify_data.get('workflow_run_id', 'unknown'),
        "inputs": {
            "employee_id": employee_data['id'],
            "employee_name": employee_data['name'],
            "approval_choice": choice,
            "action": "manager_approval",
            "timestamp": datetime.now().isoformat()
        },
        "response_mode": "blocking"
    }
    
    try:
        # 在实际使用中，取消注释下面的代码
        # response = requests.post(callback_url, headers=headers, json=payload)
        # if response.status_code == 200:
        #     return True
        # else:
        #     st.error(f"提交失败: {response.text}")
        #     return False
        
        # 模拟成功返回
        st.info(f"📤 已发送到Dify: {employee_data['name']} - {choice}")
        st.info(f"回调URL: {callback_url}")
        return True
    except Exception as e:
        st.error(f"连接错误: {str(e)}")
        return False

def main():
    st.title("🏢 员工退休方案审批系统")
    st.markdown("---")
    
    # 初始化session state
    initialize_session_state()
    
    # 侧边栏
    st.sidebar.header("📅 审批信息")
    batch_date = st.sidebar.date_input("审批日期", datetime.now())
    
    # 数据来源选择
    data_source = st.sidebar.radio(
        "数据来源:",
        ["Dify请求", "手动输入"],
        horizontal=True
    )
    
    # 加载数据
    if data_source == "Dify请求":
        # 从URL参数加载Dify数据
        if st.session_state.dify_data is None:
            dify_data = load_dify_data()
            if dify_data:
                st.session_state.dify_data = dify_data
                st.success("✅ 已成功加载Dify数据")
            else:
                # 显示如何使用
                st.info("""
                ### 如何从Dify接收数据：
                
                1. **在Dify Workflow中配置HTTP请求节点**
                   - 方法: GET
                   - URL: `https://blank-app-4hx917t663u.streamlit.app/?data=YOUR_BASE64_DATA`
                
                2. **数据格式示例：**
                ```json
                {
                  "workflow_run_id": "workflow-123",
                  "callback_url": "https://api.dify.ai/v1/workflows/run",
                  "api_key": "your-api-key",
                  "employees": [...]
                }
                ```
                
                3. **将数据Base64编码后添加到URL**
                ```python
                import base64, json, urllib.parse
                
                data = {...}
                json_str = json.dumps(data)
                base64_data = base64.b64encode(json_str.encode()).decode()
                # 转换为URL安全格式
                url_safe_data = base64_data.replace('+', '-').replace('/', '_')
                url = f"https://blank-app-4hx917t663u.streamlit.app/?data={url_safe_data}"
                ```
                """)
                
                # 演示按钮
                if st.button("加载演示数据"):
                    demo_data = {
                        "workflow_run_id": "demo-workflow-001",
                        "callback_url": "https://api.dify.ai/v1/workflows/run",
                        "api_key": "demo-api-key-123",
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
                            },
                            {
                                "id": "EMP002",
                                "name": "李四",
                                "gender": "女",
                                "age": 55.5,
                                "employee_type": "蓝领",
                                "manager_name": "李经理",
                                "manager_email": "li.manager@company.com",
                                "qualification": "女性 ≥54.5岁",
                                "branch": "123",
                                "status": "pending"
                            }
                        ]
                    }
                    st.session_state.dify_data = demo_data
                    st.rerun()
                
                return
        
        dify_data = st.session_state.dify_data
        
        # 显示数据信息
        display_data_info(dify_data)
        
        # 获取员工列表
        employees = dify_data.get('employees', [])
        
    else:  # 手动输入
        st.sidebar.header("⚙️ 手动配置")
        callback_url = st.sidebar.text_input("Dify回调URL")
        api_key = st.sidebar.text_input("API Key", type="password")
        workflow_id = st.sidebar.text_input("Workflow ID")
        
        # 演示员工数据
        employees = [
            {
                "id": "EMP001",
                "name": "测试员工",
                "gender": "男",
                "age": 60.0,
                "employee_type": "白领",
                "manager_name": "测试经理",
                "manager_email": "test@company.com",
                "qualification": "测试条件",
                "branch": "123",
                "status": "pending"
            }
        ]
    
    # 主界面
    st.header("📋 待审批员工列表")
    
    if not employees:
        st.warning("暂无待审批员工")
        return
    
    # 显示员工列表
    approved_count = 0
    for idx, emp in enumerate(employees):
        with st.container():
            render_employee_card(emp, idx)
            
            # 统计已审批数量
            if emp.get('status') == 'approved':
                approved_count += 1
    
    # 批量操作区域
    st.markdown("---")
    st.header("📤 批量操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ 提交所有待审批", type="primary"):
            pending_employees = [e for e in employees if e.get('status') != 'approved']
            
            if not pending_employees:
                st.info("没有待审批的员工")
                return
            
            approvals = []
            for emp in pending_employees:
                choice_key = f"choice_{emp['id']}_0"
                choice = st.session_state.employee_choices.get(choice_key)
                if choice:
                    approvals.append({
                        "employee_id": emp['id'],
                        "employee_name": emp['name'],
                        "choice": choice,
                        "timestamp": datetime.now().isoformat()
                    })
            
            if approvals:
                st.success(f"准备提交 {len(approvals)} 条审批")
                st.json(approvals)
                
                # 在实际使用中，这里应该调用批量发送到Dify的函数
                if data_source == "Dify请求" and dify_data:
                    st.info("在实际部署中，这里会批量发送到Dify")
            else:
                st.warning("请先为待审批员工选择方案")
    
    with col2:
        st.metric("待审批", len([e for e in employees if e.get('status') != 'approved']))
    
    with col3:
        st.metric("已审批", approved_count)
    
    # 审批历史
    if st.session_state.approval_history:
        st.markdown("---")
        st.header("📜 审批历史")
        
        for record in st.session_state.approval_history:
            with st.expander(f"{record['timestamp']} - {record['employee_name']}"):
                st.write(f"**员工ID:** {record['employee_id']}")
                st.write(f"**选择方案:** {record['choice']}")
    
    # 调试信息
    with st.sidebar.expander("🔧 调试信息"):
        st.write(f"Session状态: {list(st.session_state.keys())}")
        if st.button("清除数据"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
