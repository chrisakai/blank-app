# retirement_approval_ui.py
import streamlit as st
import json
from datetime import datetime

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

def main():
    st.title("🏢 员工退休方案审批系统")
    st.markdown("---")
    
    # 检查session state中是否有数据
    if 'employee_data' not in st.session_state:
        st.session_state.employee_data = None
    
    # 如果已有数据，直接显示
    if st.session_state.employee_data:
        employee_data = st.session_state.employee_data
        dify_info = st.session_state.get('dify_info', {})
        
        render_approval_interface(employee_data, dify_info)
        return
    
    # 否则显示数据输入表单
    st.subheader("📥 接收Dify数据")
    
    # 方法1：通过表单输入
    with st.form("dify_data_form"):
        st.markdown("### 方法1：手动输入Dify数据")
        
        # 基本员工信息
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("员工姓名", key="form_name")
            gender = st.selectbox("性别", ["男", "女"], key="form_gender")
            age = st.number_input("年龄", min_value=0.0, max_value=100.0, value=55.5, key="form_age")
        
        with col2:
            branch = st.text_input("分支代码", value="123", key="form_branch")
            manager_name = st.text_input("经理姓名", key="form_manager_name")
            manager_email = st.text_input("经理邮箱", key="form_manager_email")
        
        # Dify回调信息
        st.markdown("### Dify回调配置")
        callback_url = st.text_input("回调URL", value="", key="form_callback_url")
        api_key = st.text_input("API Key", type="password", key="form_api_key")
        workflow_run_id = st.text_input("Workflow Run ID", key="form_workflow_id")
        
        # 提交按钮
        submitted = st.form_submit_button("提交数据并开始审批")
        
        if submitted:
            if not name:
                st.error("请输入员工姓名")
            else:
                # 保存数据到session state
                st.session_state.employee_data = {
                    "id": f"EMP{datetime.now().strftime('%H%M%S')}",
                    "name": name,
                    "gender": gender,
                    "age": float(age),
                    "employee_type": "白领",
                    "qualification": "",
                    "branch": branch,
                    "manager_name": manager_name,
                    "manager_email": manager_email,
                    "status": "pending"
                }
                
                st.session_state.dify_info = {
                    "callback_url": callback_url,
                    "api_key": api_key,
                    "workflow_run_id": workflow_run_id,
                    "action": "manager_approval"
                }
                
                st.success("数据已接收，正在加载审批界面...")
                st.rerun()
    
    st.markdown("---")
    
    # 方法2：通过URL参数（简化版）
    st.markdown("### 方法2：通过URL链接（适用于Dify）")
    
    # 生成示例URL
    example_params = {
        "name": "张三",
        "gender": "男",
        "age": "60",
        "branch": "123",
        "manager_name": "张经理",
        "manager_email": "zhang@company.com"
    }
    
    # 构建URL
    param_string = "&".join([f"{k}={v}" for k, v in example_params.items()])
    example_url = f"https://blank-app-4hx917t663u.streamlit.app/?{param_string}"
    
    st.code(example_url)
    st.caption("将此URL设置为Dify的GET请求目标")
    
    # 检查是否有URL参数
    query_params = st.query_params.to_dict()
    if query_params and 'name' in query_params:
        # 处理URL参数
        st.info("检测到URL参数，正在处理...")
        
        employee_data = {
            "id": f"EMP{datetime.now().strftime('%H%M%S')}",
            "name": query_params.get('name', ''),
            "gender": query_params.get('gender', ''),
            "age": float(query_params.get('age', 0)),
            "employee_type": query_params.get('employee_type', '白领'),
            "qualification": query_params.get('qualification', ''),
            "branch": query_params.get('branch', ''),
            "manager_name": query_params.get('manager_name', ''),
            "manager_email": query_params.get('manager_email', ''),
            "status": "pending"
        }
        
        dify_info = {
            "callback_url": query_params.get('callback_url', ''),
            "api_key": query_params.get('api_key', ''),
            "workflow_run_id": query_params.get('workflow_run_id', ''),
            "action": query_params.get('action', 'manager_approval')
        }
        
        if employee_data['name']:
            st.session_state.employee_data = employee_data
            st.session_state.dify_info = dify_info
            st.rerun()

def render_approval_interface(employee_data, dify_info):
    """渲染审批界面"""
    st.header(f"📝 员工退休方案审批：{employee_data['name']}")
    
    # 显示员工信息
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"""
            <div class='approval-card pending'>
                <h2>{employee_data['name']} ({employee_data['gender']}, {employee_data['age']}岁)</h2>
                <p><strong>员工类型:</strong> {employee_data.get('employee_type', '白领')}</p>
                <p><strong>分支:</strong> {employee_data['branch']}</p>
                <p><strong>对应经理:</strong> {employee_data['manager_name']} ({employee_data['manager_email']})</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 审批操作")
            
            if employee_data.get('status') != 'approved':
                # 选择审批方案
                if employee_data['branch'] == '123':
                    options = ["Flexible retirement", "Retire at legal age", "Rehire"]
                else:
                    options = ["待定方案1", "待定方案2", "待定方案3"]
                
                choice = st.selectbox(
                    "选择审批方案:",
                    options,
                    key="approval_choice"
                )
                
                approval_reason = st.text_area(
                    "审批理由（可选）",
                    placeholder="请输入审批理由..."
                )
                
                # 提交按钮
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✅ 提交批准", type="primary", use_container_width=True):
                        handle_approval(employee_data, choice, approval_reason, dify_info, "approved")
                
                with col_btn2:
                    if st.button("❌ 提交驳回", use_container_width=True):
                        handle_approval(employee_data, choice, approval_reason, dify_info, "rejected")
                
                # 重置按钮
                if st.button("🔄 重新输入数据", use_container_width=True):
                    del st.session_state.employee_data
                    if 'dify_info' in st.session_state:
                        del st.session_state.dify_info
                    st.rerun()
            else:
                st.success("✅ 已审批完成")
                st.info(f"**方案:** {employee_data.get('approved_choice', '未知')}")
                st.info(f"**状态:** {employee_data.get('approval_status', '已批准')}")
                st.info(f"**时间:** {employee_data.get('approved_time', '')}")
                
                if st.button("🔄 重新审批", use_container_width=True):
                    employee_data['status'] = 'pending'
                    st.rerun()
    
    # Dify回调信息
    if dify_info.get('callback_url'):
        with st.expander("🔗 Dify回调配置"):
            st.info(f"**回调URL:** {dify_info['callback_url']}")
            if dify_info.get('workflow_run_id'):
                st.info(f"**Workflow Run ID:** {dify_info['workflow_run_id']}")

def handle_approval(employee_data, choice, reason, dify_info, status):
    """处理审批提交"""
    # 更新员工状态
    employee_data['status'] = 'approved'
    employee_data['approved_choice'] = choice
    employee_data['approval_reason'] = reason
    employee_data['approval_status'] = status
    employee_data['approved_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存到历史记录
    if 'approval_history' not in st.session_state:
        st.session_state.approval_history = []
    
    st.session_state.approval_history.append({
        "employee": employee_data['name'],
        "choice": choice,
        "reason": reason,
        "status": status,
        "timestamp": employee_data['approved_time']
    })
    
    # 显示提交成功
    st.success(f"✅ 已提交审批: {choice} ({status})")
    
    # 如果有Dify回调URL，显示回调信息
    if dify_info.get('callback_url') and dify_info.get('api_key'):
        show_dify_callback_info(employee_data, choice, reason, status, dify_info)
    
    st.balloons()
    
    # 等待2秒后重新渲染
    import time
    time.sleep(2)
    st.rerun()

def show_dify_callback_info(employee_data, choice, reason, status, dify_info):
    """显示Dify回调信息"""
    with st.expander("📤 Dify回调数据", expanded=True):
        # 构建回调数据
        callback_data = {
            "workflow_run_id": dify_info.get('workflow_run_id', 'unknown'),
            "inputs": {
                "employee_id": employee_data['id'],
                "employee_name": employee_data['name'],
                "approval_choice": choice,
                "approval_reason": reason,
                "approval_status": status,
                "action": "manager_approval",
                "timestamp": datetime.now().isoformat()
            },
            "response_mode": "blocking"
        }
        
        st.json(callback_data)
        
        st.info("**实际部署时，以下数据将发送到Dify:**")
        st.code(f"""
        POST {dify_info['callback_url']}
        Authorization: Bearer {dify_info['api_key'][:10]}...
        Content-Type: application/json
        
        {json.dumps(callback_data, indent=2, ensure_ascii=False)}
        """)

if __name__ == "__main__":
    main()
