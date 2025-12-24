# retirement_approval_ui.py
import streamlit as st
import requests
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

    # 显示当前审批批次
    st.sidebar.header("📅 审批批次")
    batch_date = st.sidebar.date_input("选择审批日期", datetime.now())

    # Dify API 配置
    st.sidebar.header("⚙️ API 配置")
    dify_api_key = st.sidebar.text_input("Dify API Key", type="password")
    dify_workflow_id = st.sidebar.text_input("Workflow ID")
    callback_url = st.sidebar.text_input("Dify Callback URL",
                                         value="https://api.dify.ai/v1/workflows/run")

    # 获取待审批员工列表（从Dify API）
    st.header("📋 待审批员工列表")

    # 模拟数据 - 实际中从Dify API获取
    pending_employees = [
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
        },
        {
            "id": "EMP003",
            "name": "王五",
            "gender": "女",
            "age": 50.2,
            "employee_type": "蓝领",
            "manager_name": "王经理",
            "manager_email": "wang.manager@company.com",
            "qualification": "女性蓝领 ≥49.5岁",
            "branch": "4",
            "status": "pending"
        }
    ]

    # 显示待审批员工
    approved_count = 0
    for emp in pending_employees:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div class='approval-card pending'>
                    <h3>{emp['name']} ({emp['gender']}, {emp['age']}岁)</h3>
                    <p><strong>员工类型:</strong> {emp['employee_type']}</p>
                    <p><strong>符合条件:</strong> {emp['qualification']}</p>
                    <p><strong>对应经理:</strong> {emp['manager_name']} ({emp['manager_email']})</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("### 选择方案")

                # 根据分支显示不同选项
                if emp['branch'] == '123':
                    option = st.radio(
                        "请选择:",
                        ["Flexible retirement", "Retire at legal age", "Rehire"],
                        key=f"option_{emp['id']}",
                        index=None
                    )
                else:
                    option = st.selectbox(
                        "分支4方案:",
                        ["待定方案1", "待定方案2", "待定方案3"],
                        key=f"option_{emp['id']}",
                        index=None
                    )

                # 提交按钮
                if st.button(f"提交 {emp['name']}", key=f"submit_{emp['id']}"):
                    # 发送审批结果到Dify
                    send_approval_to_dify(
                        emp['id'],
                        option,
                        dify_api_key,
                        dify_workflow_id,
                        callback_url
                    )
                    st.success(f"✅ 已提交 {emp['name']} 的审批: {option}")
                    emp['status'] = 'approved'
                    approved_count += 1

    # 批量审批区域
    st.markdown("---")
    st.header("📤 批量提交")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ 提交所有审批", type="primary"):
            # 获取所有选择
            approvals = []
            for emp in pending_employees:
                # 这里需要获取实际的选项值
                option = st.session_state.get(f"option_{emp['id']}")
                if option:
                    approvals.append({
                        "employee_id": emp['id'],
                        "employee_name": emp['name'],
                        "choice": option,
                        "timestamp": datetime.now().isoformat()
                    })

            # 批量发送到Dify
            if approvals:
                batch_send_to_dify(approvals, dify_api_key, dify_workflow_id, callback_url)
                st.success(f"✅ 已批量提交 {len(approvals)} 条审批")

    with col2:
        st.metric("待审批", len(pending_employees))

    with col3:
        st.metric("已审批", approved_count)

    # 审批历史
    st.markdown("---")
    with st.expander("📜 审批历史记录"):
        if 'approval_history' in st.session_state:
            for record in st.session_state.approval_history:
                st.write(f"{record['timestamp']} - {record['employee_name']}: {record['choice']}")
        else:
            st.info("暂无审批历史")


def send_approval_to_dify(employee_id, choice, api_key, workflow_id, callback_url):
    """发送单条审批结果到Dify"""
    if not api_key or not workflow_id:
        st.warning("请先配置Dify API信息")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "employee_id": employee_id,
            "approval_choice": choice,
            "action": "manager_approval"
        },
        "response_mode": "blocking"
    }

    try:
        response = requests.post(callback_url, headers=headers, json=payload)
        if response.status_code == 200:
            # 保存到历史记录
            if 'approval_history' not in st.session_state:
                st.session_state.approval_history = []

            st.session_state.approval_history.append({
                "employee_id": employee_id,
                "choice": choice,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            return True
        else:
            st.error(f"提交失败: {response.text}")
            return False
    except Exception as e:
        st.error(f"连接错误: {str(e)}")
        return False


def batch_send_to_dify(approvals, api_key, workflow_id, callback_url):
    """批量发送审批结果到Dify"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "batch_approvals": json.dumps(approvals),
            "action": "batch_manager_approval"
        },
        "response_mode": "blocking"
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


if __name__ == "__main__":
    main()
