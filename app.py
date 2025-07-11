import streamlit as st
import requests
import streamlit.components.v1 as components
import uuid
from warnings import filterwarnings
filterwarnings("ignore")

st.set_page_config(page_title="Chatbot", layout="wide")

# --- Tạo vùng HTML để lấy session_id từ localStorage ---
components.html(
    """
    <script>
    const sidKey = "session_id";
    let sid = localStorage.getItem(sidKey);
    if (!sid) {
        sid = self.crypto.randomUUID();
        localStorage.setItem(sidKey, sid);
    }
    const streamlitInput = window.parent.document.querySelectorAll('iframe[srcdoc]')[0].contentWindow;
    streamlitInput.postMessage({type: 'streamlit:setComponentValue', value: sid}, '*');
    </script>
    """,
    height=0,
)

# --- Dùng st.experimental_get_query_params để lấy dữ liệu gửi về từ JS ---
session_id = st.query_params.get("session_id", [None])[0]

# --- Nếu không lấy được qua URL, fallback: tự tạo tạm session_id ---
if not session_id:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    session_id = st.session_state.session_id

# Khởi tạo bộ nhớ lưu chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hàm gửi/nhận phản hồi dạng stream
def stream_chat_style(user_message, session_id):
    url = "https://tekup.dongnamduocgl.com/gplus-chatbot/generate-message"
    payload = {
        "user_message": user_message,
        "session_id": session_id
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        assistant_msg = data.get("assistant_reply_message", {}).get("data", "")
        tour_msg = data.get("tour_message", {}).get("data", None)

        return assistant_msg, tour_msg
    except Exception as e:
        return f"❌ Lỗi khi gửi yêu cầu: {str(e)}", None
    
def display_tour_message(tour_msgs):
    for tour_msg in tour_msgs:
        st.markdown(f"# Tour ID: {tour_msg['id']}")
        st.markdown(f"# Tên Tour: {tour_msg['name']}")
        day, night = tour_msg['duration'].split("-")
        st.markdown(f'# Thời lượng: {day} ngày {night} đêm')
        st.markdown(f'# Các chi phí theo ngày:')
        for key in tour_msg['schedule'].keys():
            st.markdown(f"## Ngày {key}")
            for item in tour_msg['schedule'][key]:
                if item['type'] == 0:
                    st.markdown(f"# Hoạt động tham quan:")
                    st.markdown(f"{item['name']}|Giá: {item['price']}")
                if item['type'] == 1:
                    st.markdown(f"# Nhà hàng ăn trưa: ")
                    st.markdown(f"Loại nhà hàng: {item['star']} sao|Giá: {item['price']}")
                if item['type'] == 2:
                    st.markdown(f"# Nhà hàng ăn tối: ")
                    st.markdown(f"Loại nhà hàng: {item['star']} sao|Giá: {item['price']}")
                if item['type'] == 3:
                    st.markdown(f"# Khách sạn: ")
                    st.markdown(f"Loại khách sạn: {item['star']} sao|Giá: {item['price']}")
        st.markdown("# Chi phí xe:")
        for car in tour_msg['car']:
            st.markdown(f"- {car['type']}|Giá: {car['price']}")
        st.markdown(f"# Chi phí nhân viên điều hành: {tour_msg['employee_control_price']}")
        st.markdown(f"# Giá HDV 1 ngày: {tour_msg['tour_guide']}")
        st.markdown(f"# Các chi phí khác:")
        for key in tour_msg['others']:
            st.markdown(f"# - {key}|Giá: {tour_msg['others'][key]['price']}|Số ngày: {tour_msg['others'][key]['number_of_days']}")
        
        st.markdown(f"# Chí phí tour 1 người theo từng nhóm:")
        for key in tour_msg["final_price"]:
            st.markdown(f"## Nhóm {key}")
            st.markdown(f"- Chi phí 1 người: {tour_msg['final_price'][key]['price']}")
            st.markdown(f"- Phụ thu ngủ đơn: {tour_msg['final_price'][key]['single_room_price']}")
            try:
                st.markdown(f"- Thêm 1 trưởng đoàn: {tour_msg['final_price'][key]['additional_tour_lead_price']}")
            except:
                pass

col1, col2 = st.columns(2)
# Hiển thị lịch sử chat
with col1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Nhập tin nhắn
    user_message = st.chat_input("Nhập tin nhắn")

    if user_message:
        # Hiển thị tin nhắn người dùng
        st.chat_message("user").markdown(user_message)
        st.session_state.messages.append({"role": "user", "content": user_message})

        # Phản hồi của bot
        bot_response = st.chat_message("assistant")
        message_box = bot_response.empty()
        
        assistant_msg, tour_msg = stream_chat_style(user_message, session_id)
        message_box.write(assistant_msg)
        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

        with col2:
            if tour_msg:
                display_tour_message(tour_msg)


# Auto scroll xuống dưới
st.markdown("""
    <script>
        const chatArea = window.parent.document.querySelector('.main');
        if (chatArea) {
            chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });
        }
    </script>
""", unsafe_allow_html=True)
