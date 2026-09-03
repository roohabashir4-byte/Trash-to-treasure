import streamlit as st
import pandas as pd
import requests

# 1. Page Configuration
st.set_page_config(page_title="Trash to Treasure PK", page_icon="💎")

st.markdown("""
    <style>
    .badge-box { background-color: #e3f2fd; border-radius: 10px; padding: 15px; border-left: 5px solid #2196f3; margin-bottom: 10px; }
    </style>
""", unsafe_html=True)

# 2. Session States
if 'points' not in st.session_state: st.session_state.points = 0
if 'total_cash' not in st.session_state: st.session_state.total_cash = 0.0
if 'total_weight' not in st.session_state: st.session_state.total_weight = 0.0
if 'history' not in st.session_state: st.session_state.history = []

DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Tins"},
    {"name": "Darhal Scrap Dealer", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "All Mixed Scrap, Clothes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics & Metals"}
]

MARKET_RATES = {
    "Raddi / Books (ردی)": {"rate": 45, "unit_w": 5.0},
    "Plastic Bottles (کباڑ پلاسٹک)": {"rate": 50, "unit_w": 0.5},
    "Torn Clothes / Rags (پرانے کپڑے)": {"rate": 30, "unit_w": 2.5},
    "Kitchen Organic (باورچی خانہ کچرا)": {"rate": 0, "unit_w": 1.0}
}

st.sidebar.title("🏡 Menu")
page = st.sidebar.radio("Go to:", ["📸 AI Waste Scanner", "📊 Household Ledger & Garden", "📍 Local Dealer Contact"])

if page == "📸 AI Waste Scanner":
    st.title("📸 AI Waste Scanner")
    img_file = st.camera_input("Scan your trash item")
    if img_file:
        detected_item = "Plastic Bottles (کباڑ پلاسٹک)"
        st.success(f"Detected: **{detected_item}**")
        qty = st.number_input("Enter Quantity:", min_value=1, value=1)
        user_name = st.text_input("Who is sorting this item?", value="Ali")
        if st.button("Log to Wallet"):
            item_stats = MARKET_RATES[detected_item]
            added_w = item_stats["unit_w"] * qty
            added_cash = item_stats["rate"] * added_w
            added_pts = int(added_w * 10) if added_cash > 0 else 50
            st.session_state.points += added_pts
            st.session_state.total_cash += added_cash
            st.session_state.total_weight += added_w
            st.session_state.history.append({"User": user_name, "Item": detected_item, "Weight (kg)": added_w, "Value (Rs.)": added_cash})
            st.success("Logged successfully!")

elif page == "📊 Household Ledger & Garden":
    st.title("📊 Ghar Ki Deewar")
    col1, col2, col4 = st.columns(3)
    col1.metric("Total Cash", f"Rs. {st.session_state.total_cash:.1f}")
    col2.metric("Total Weight", f"{st.session_state.total_weight:.1f} kg")
    col4.metric("Points", f"{st.session_state.points} pts")
    st.progress(min(st.session_state.points / 1000, 1.0))
    if st.session_state.history: st.dataframe(pd.DataFrame(st.session_state.history))

elif page == "📍 Local Dealer Contact":
    st.title("📍 Local Dealer Connection")
    selected_dealer = st.selectbox("Select local dealer:", [d["name"] for d in DEALERS])
    dealer_info = next(d for d in DEALERS if d["name"] == selected_dealer)
    address = st.text_input("Enter your home address:")
    msg = f"Assalam-o-Alaikum, I want to recycle {st.session_state.total_weight:.1f}kg of scrap value. Address: {address}"
    encoded_msg = requests.utils.quote(msg)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={dealer_info['phone']}&text={encoded_msg}"
    if st.button("Send WhatsApp"):
        st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;">Open WhatsApp</button></a>', unsafe_html=True)
