# retirement_approval_ui.py
import streamlit as st
import requests
import json
from datetime import datetime
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
    .parameter-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .parameter-table td {
        border: 1px solid #ddd;
        padding: 8px;
    }
    .parameter-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
</style>
""", unsafe_allow_html=True)

def load_query_parameters():
    """从URL查询参数加载Dify发送的数据"""
    # 使用新的query_params API
    query_params = st.query_params.to_dict()
    
    employee_data = {}
    
    # 检查是否有必要的参数
    if query_params:
        # 基本信息 - 使用get方法避免KeyError
        name = query_params.get("name", "")
        
        # 如果连name都没有，说明是健康检查或无效请求
        if not name:
            return None, None
        
        employee_data = {
            "id": query_params.get("employee_id", f"EMP{datetime.now().strftime('%H%M%S')}"),
            "name": name,
            "gender": query_params.get("gender", ""),
            "age": query_params.get("age", ""),
            "employee_type": query_params.get("employee_type", "白领"),
            "qualification": query_params.get("qualification", ""),
            "branch": query_params.get("branch", ""),
            "manager_name": query_params.get("manager_name", ""),
            "manager_email": query_params.get("manager_email", ""),
            "status": "pending"
        }
        
        # Dify回调信息
        dify_info = {
            "callback_url": query_params.get("callback_url", ""),
            "api_key": query_params.get("api_key", ""),
            "workflow_run_id": query_params.get("workflow_run_id", ""),
            "action": query_params.get("action", "manager_approval")
        }
        
        # 尝试解析年龄为浮点数
        try:
            employee_data["age"] = float(employee_data["age"])
        except (ValueError, TypeError):
            employee_data["age"] = 0.0
    
    return employee_data if employee_data.get("name") else None, dify_info if employee_data.get("name") else None

def display_parameter_info(query_params):
    """显示接收到的参数信息"""
    if not query_params:
        return
    
    with st.sidebar.expander("📊 接收的参数", expanded=True):
        st.markdown(f"""
        <div class="data-info">
        <p><strong>参数数量:</strong> {len(query_params)}</p>
        <p><strong>接收时间:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 参数详情")
        
        # 创建参数表格
        param_table = "<table class='parameter-table'>"
        param_table += "<tr><td><strong>参数名</strong></td><td><strong>参数值</strong></td></tr>"
        
        for key, value in query_params.items():
            # 对于敏感信息进行部分隐藏
            if key in ['api_key', 'password', 'token'] and value:
                display_value = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
            else:
                display_value = value if value else ""
            
            param_table += f"<tr><td>{key}</td><td>{display_value}</td></tr>"
        
        param_table += "</table>"
        st.markdown(param_table, unsafe_allow_html=True)
        
        # 显示原始URL
        if st.checkbox("显示原始查询字符串"):
            param_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in query_params.items() if v])
            st.code(f"?{param_string}")

def render_single_employee_card(emp: Dict, dify_info: Dict):
    """渲染单个员工审批卡片"""
    st.header("📝 员工退休方案审批")
    
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            status_class = "approved" if emp.get('status') == 'approved' else "pending"
            
            st.markdown(f"""
            <div class='approval-card {status_class}'>
                <h2>{emp['name']} ({emp['gender']}, {emp['age']}岁)</h2>
                <p><strong>员工ID:</strong> {emp['id']}</p>
                <p><strong>员工类型:</strong> {emp['employee_type']}</p>
                <p><strong>符合条件:</strong> {emp['qualification']}</p>
                <p><strong>对应经理:</strong> {emp['manager_name']} ({emp['manager_email']})</p>
                <p><strong>分支:</strong> {emp['branch']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if emp.get('status') != 'approved':
                st.markdown("### 选择审批方案")
                
                # 根据分支显示不同选项
                if emp.get('branch') == '123':
                    options = ["Flexible retirement", "Retire at legal age", "Rehire"]
                else:
                    options = ["待定方案1", "待定方案2", "待定方案3"]
                
                # 创建选择框
                choice = st.selectbox(
                    "请选择方案:",
                    options,
                    key=f"choice_{emp['id']}",
                    index=None,
                    placeholder="选择审批方案..."
                )
                
                # 审批理由输入
                approval_reason = st.text_area(
                    "审批理由（可选）",
                    height=100,
                    placeholder="请输入审批理由...",
                    key=f"reason_{emp['id']}"
                )
                
                # 提交按钮
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("✅ 批准", type="primary", use_container_width=True, key=f"approve_{emp['id']}"):
                        if choice:
                            submit_approval(emp, choice, approval_reason, dify_info, "approved")
                        else:
                            st.warning("请先选择审批方案")
                
                with col_btn2:
                    if st.button("❌ 驳回", use_container_width=True, key=f"reject_{emp['id']}"):
                        if choice:
                            submit_approval(emp, choice, approval_reason, dify_info, "rejected")
                        else:
                            st.warning("请先选择审批方案")
                
                with col_btn3:
                    if st.button("⏸️ 暂存", use_container_width=True, key=f"save_{emp['id']}"):
                        st.info("已暂存当前选择")
                        
                        # 保存到session state
                        if 'draft_approvals' not in st.session_state:
                            st.session_state.draft_approvals = []
                        
                        st.session_state.draft_approvals.append({
                            "employee": emp,
                            "choice": choice,
                            "reason": approval_reason,
                            "timestamp": datetime.now().isoformat()
                        })
            else:
                st.success("✅ 已审批完成")
                st.info(f"**方案:** {emp.get('approved_choice', '未知')}")
                st.info(f"**理由:** {emp.get('approval_reason', '无')}")
                st.info(f"**时间:** {emp.get('approved_time', '')}")
                
                if st.button("🔄 重新审批", key=f"reapprove_{emp['id']}"):
                    emp['status'] = 'pending'
                    st.rerun()

def submit_approval(employee: Dict, choice: str, reason: str, dify_info: Dict, status: str = "approved"):
    """提交审批结果"""
    
    # 更新员工状态
    employee['status'] = status
    employee['approved_choice'] = choice
    employee['approval_reason'] = reason
    employee['approved_time'] = datetime.now().isoformat()
    
    # 保存到历史记录
    if 'approval_history' not in st.session_state:
        st.session_state.approval_history = []
    
    st.session_state.approval_history.append({
        "employee_id": employee['id'],
        "employee_name": employee['name'],
        "choice": choice,
        "reason": reason,
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 如果有Dify回调信息，发送到Dify
    if dify_info and dify_info.get('callback_url') and dify_info.get('api_key'):
        send_to_dify(employee, choice, reason, status, dify_info)
    
    st.success(f"✅ 已提交审批: {choice} ({status})")
    st.balloons()
    
    # 重新运行以更新界面
    st.rerun()

def send_to_dify(employee: Dict, choice: str, reason: str, status: str, dify_info: Dict):
    """发送审批结果到Dify"""
    
    callback_url = dify_info['callback_url']
    api_key = dify_info['api_key']
    workflow_run_id = dify_info.get('workflow_run_id', '')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建回调数据
    payload = {
        "workflow_run_id": workflow_run_id,
        "inputs": {
            "employee_id": employee['id'],
            "employee_name": employee['name'],
            "approval_choice": choice,
            "approval_reason": reason,
            "approval_status": status,
            "action": dify_info.get('action', 'manager_approval'),
            "timestamp": datetime.now().isoformat()
        },
        "response_mode": "blocking"
    }
    
    try:
        # 在实际部署中，取消注释下面的代码
        # response = requests.post(callback_url, headers=headers, json=payload)
        # response.raise_for_status()
        
        # 显示回调信息（模拟）
        with st.expander("📤 查看回调数据", expanded=True):
            st.info(f"**回调URL:** {callback_url}")
            st.info(f"**Workflow Run ID:** {workflow_run_id}")
            st.json(payload)
        
        st.success(f"✅ 审批结果已发送到Dify Workflow")
        return True
        
    except Exception as e:
        st.error(f"❌ 发送到Dify失败: {str(e)}")
        
        # 显示详细错误信息
        with st.expander("🔍 错误详情"):
            st.error(f"错误类型: {type(e).__name__}")
            st.error(f"错误信息: {str(e)}")
            st.info("**建议检查:**")
            st.info("1. Dify API Key是否正确")
            st.info("2. 回调URL是否可以访问")
            st.info("3. 网络连接是否正常")
        
        return False

def show_approval_history():
    """显示审批历史"""
    if 'approval_history' in st.session_state and st.session_state.approval_history:
        st.markdown("---")
        st.header("📜 审批历史记录")
        
        # 只显示最近5条
        recent_history = list(reversed(st.session_state.approval_history[-5:]))
        
        for idx, record in enumerate(recent_history):
            status_color = "🟢" if record['status'] == 'approved' else "🔴"
            
            with st.expander(f"{status_color} {record['timestamp']} - {record['employee_name']}", expanded=idx==0):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**员工ID:** {record['employee_id']}")
                    st.write(f"**审批状态:** {record['status']}")
                    st.write(f"**选择方案:** {record['choice']}")
                
                with col2:
                    st.write(f"**审批理由:** {record.get('reason', '无')}")
                    
                    # 显示操作按钮
                    if st.button(f"复制结果", key=f"copy_{idx}"):
                        result_json = json.dumps(record, ensure_ascii=False, indent=2)
                        st.code(result_json, language="json")

def show_draft_approvals():
    """显示暂存的审批"""
    if 'draft_approvals' in st.session_state and st.session_state.draft_approvals:
        st.markdown("---")
        st.header("💾 暂存审批")
        
        for idx, draft in enumerate(st.session_state.draft_approvals):
            with st.expander(f"暂存 {idx+1}: {draft['employee']['name']}"):
                st.write(f"**员工:** {draft['employee']['name']}")
                st.write(f"**方案:** {draft.get('choice', '未选择')}")
                st.write(f"**理由:** {draft.get('reason', '无')}")
                st.write(f"**暂存时间:** {draft['timestamp']}")
                
                if st.button(f"加载此暂存", key=f"load_draft_{idx}"):
                    st.info("加载暂存功能需要根据具体需求实现")

def main():
    st.title("🏢 员工退休方案审批系统")
    st.markdown("---")
    
    # 侧边栏
    st.sidebar.header("📅 系统信息")
    st.sidebar.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 从URL参数加载数据
    employee_data, dify_info = load_query_parameters()
    
    # 显示接收到的参数信息
    query_params = st.query_params.to_dict()
    if query_params:
        display_parameter_info(query_params)
    
    # 检查是否有数据
    if not employee_data:
        st.warning("等待Dify发送员工数据...")
        
        st.info("""
        ### 📋 如何从Dify接收数据：
        
        1. **在Dify Workflow中配置HTTP请求节点**
           - 方法: GET
           - 目标URL: `https://blank-app-4hx917t663u.streamlit.app`
        
        2. **在PARAMS中添加以下参数：**
           ```
           name=员工姓名
           gender=性别
           age=年龄
           branch=分支代码
           manager_name=经理姓名
           manager_email=经理邮箱
           callback_url=Dify回调URL（可选）
           api_key=Dify API Key（可选）
           workflow_run_id=工作流运行ID（可选）
           ```
        
        3. **示例URL：**
           ```
           https://blank-app-4hx917t663u.streamlit.app/?name=李四&gender=女&age=55.5&branch=123&manager_name=李经理&manager_email=li.manager@company.com
           ```
        """)
        
        # 演示模式
        if st.button("进入演示模式"):
            # 设置演示查询参数
            demo_params = {
                "name": "张三",
                "gender": "男",
                "age": "60.0",
                "employee_type": "白领",
                "qualification": "男性 ≥59.5岁",
                "branch": "123",
                "manager_name": "张经理",
                "manager_email": "zhang.manager@company.com",
                "callback_url": "https://api.dify.ai/v1/workflows/run",
                "api_key": "app-demo-key-123456",
                "workflow_run_id": "demo-workflow-001"
            }
            
            # 更新查询参数
            for key, value in demo_params.items():
                st.query_params[key] = value
            
            # 重新运行应用
            st.rerun()
        
        # 显示历史记录（如果有）
        show_approval_history()
        show_draft_approvals()
        
        # 显示当前的查询参数（调试用）
        with st.sidebar.expander("🔧 当前查询参数"):
            st.json(query_params)
        
        return
    
    # 渲染审批界面
    render_single_employee_card(employee_data, dify_info)
    
    # 显示历史记录
    show_approval_history()
    
    # 显示暂存审批
    show_draft_approvals()
    
    # 调试信息
    with st.sidebar.expander("🔧 调试选项"):
        if st.button("清除所有数据"):
            # 清除session state
            keys_to_clear = ['approval_history', 'draft_approvals']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 清除查询参数
            for key in list(st.query_params.keys()):
                del st.query_params[key]
            
            st.success("数据已清除")
            st.rerun()
        
        if st.button("查看当前session状态"):
            st.write("当前session keys:", list(st.session_state.keys()))
            
            if 'approval_history' in st.session_state:
                st.write("审批历史:", st.session_state.approval_history)
        
        # 显示测试URL
        st.markdown("---")
        st.markdown("### 测试URL示例")
        test_url = "https://blank-app-4hx917t663u.streamlit.app/?name=李四&gender=女&age=55.5&branch=123&manager_name=李经理&manager_email=li.manager@company.com"
        st.code(test_url)

if __name__ == "__main__":
    # 初始化session state
    if 'approval_history' not in st.session_state:
        st.session_state.approval_history = []
    
    if 'draft_approvals' not in st.session_state:
        st.session_state.draft_approvals = []
    
    main()
