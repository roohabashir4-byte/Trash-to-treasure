import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
import google.generativeai as genai

# ==========================================
# 🎨 1. THEME DESIGN & BRANDING CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trash to Treasure PK", 
    page_icon="💎", 
    layout="wide"
)

# Advanced CSS injects handling theme layouts, flashing alerts, and custom visual cards
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-weight: bold; }
    .badge-box { background-color: #ffffff; border-radius: 14px; padding: 20px; border-left: 6px solid #2e7d32; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .title-banner { background: linear-gradient(135deg, #1b5e20, #4caf50); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .illustration-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; text-align: center; border: 2px dashed #4caf50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    .price-flash-green {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #4caf50;
        font-weight: bold;
        text-align: center;
        animation: pulse-green 2s infinite;
        margin-bottom: 15px;
    }
    .sidebar-rate-text {
        font-size: 14px;
        margin: 5px 0;
        padding: 6px;
        background-color: #ffffff;
        border-radius: 6px;
        border: 1px solid #eee;
    }
    </style>
""", unsafe_allow_html=True)

# 🌍 BRANDING BANNER LOGO
st.markdown("""
    <div class="title-banner">
        <h1 style="margin:0; font-size:38px;">💎 TRASH TO TREASURE PK</h1>
        <p style="margin:5px 0 0 0; font-size:18px;"><b>اسمارٹ کباڑ اور گھر کی بچت</b></p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 📦 2. REGIONAL KABARI YARD DATA (ALWAYS ANCHORED)
# ==========================================
DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Metal Tins"},
    {"name": "Darhal Scrap Yard", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "Cartons, Fabric Clothes, Mixed Stashes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics, Metals, Appliances Stuffing"},
    {"name": "Local Razaee/Gada Maker", "phone": "923046330986", "loc": "Kundian Market Link", "items": "Torn Fabric Clothes, Old Sheets"}
]

# ==========================================
# 📈 3. LIVE WEBSCRAPER & CACHE PROTECTION (://getscraprate.com)
# ==========================================
@st.cache_data(ttl=3600)  
def fetch_live_pakistan_rates():
    url = "https://://getscraprate.com"
    defaults = {"plastic": 62.25, "raddi": 43.51, "cardboard": 30.98, "textile": 35.00}
    try:
        req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            text_data = soup.get_text().lower()
            
            def extract_rate(item_name, default_val):
                if item_name in text_data:
                    parts = text_data.split(item_name)
                    for part in parts[1:]:
                        words = part.split()
                        for word in words:
                            clean_word = "".join(c for c in word if c.isdigit() or c == '.')
                            if clean_word:
                                try:
                                    val = float(clean_word)
                                    if 10 < val < 200: return val
                                except ValueError: continue
                return default_val
            
            return {
                "plastic": extract_rate("plastic", defaults["plastic"]),
                "raddi": extract_rate("newspaper", defaults["raddi"]),
                "cardboard": extract_rate("cardboard", defaults["cardboard"]),
                "textile": defaults["textile"]
            }
    except Exception:
        pass
    return defaults

LIVE_RATES = fetch_live_pakistan_rates()

# ==========================================
# 🔑 4. SIDEBAR ACCESS, FLASHING ALERTS & LIVE MARKET TICKER
# ==========================================
st.sidebar.header("🔑 Household Access")
household_code = st.sidebar.text_input("Enter Household Code (گھر کا کوڈ):", placeholder="e.g., khan-house-chashma").strip().lower()

st.sidebar.divider()
st.sidebar.subheader("📈 Today's Punjab Bazar (لائیو ریٹ)")

if LIVE_RATES["plastic"] >= 60.0 or LIVE_RATES["raddi"] >= 40.0:
    st.sidebar.markdown("""
        <div class="price-flash-green">
            📈 Bazar Up: Good Time to Sell!<br><span style="font-size:12px; font-weight:normal;">(آج ریٹ تیز ہے - مال بیچیں)</span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
        <div style="background-color:#fff3cd; color:#856404; padding:12px; border-radius:8px; border-left:5px solid #ffc107; font-weight:bold; text-align:center; margin-bottom:15px;">
            ⚠️ Bazar Normal: Hold or Compare<br><span style="font-size:12px; font-weight:normal;">(مارکیٹ مستحکم ہے)</span>
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown(f"""
    <div class="sidebar-rate-text">🍾 <b>Plastics & Cans:</b> Rs. {LIVE_RATES['plastic']:.2f} / kg</div>
    <div class="sidebar-rate-text">📦 <b>Raddi Newspaper:</b> Rs. {LIVE_RATES['raddi']:.2f} / kg</div>
    <div class="sidebar-rate-text">🗂️ <b>Cardboard Box:</b> Rs. {LIVE_RATES['cardboard']:.2f} / kg</div>
    <div class="sidebar-rate-text">🧵 <b>Fabric Clothes:</b> Rs. {LIVE_RATES['textile']:.2f} / kg</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.subheader("🧠 Google AI Studio Configuration")
gemini_api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password", help="Get a free key from Google AI Studio website.")

current_cash_total = 0.0

if 'global_db' not in st.session_state:
    st.session_state.global_db = {}

if not household_code:
    st.warning("👋 Welcome! Please type a unique Household Code in the sidebar to load your private, customized space.")
    st.info("💡 *Tip: You can invent any code you want (like your name or house number). Just remember it so your family can log back in later!*")
else:
    if household_code not in st.session_state.global_db:
        st.session_state.global_db[household_code] = {
            "scores": {},      
            "history": []       
        }
        st.sidebar.success(f"🆕 Private space created: **{household_code}**!")
    else:
        st.sidebar.success(f"🔓 Private space unlocked for: **{household_code}**")

    my_house = st.session_state.global_db[household_code]
    left_col, right_col = st.columns(2)

    # ==========================================
    # 🎮 5. USER REGISTRATION INTERFACE
    # ==========================================
    with left_col:
        st.write("### 📸 AI Intelligent Waste Scanner")
        st.markdown("#### **1. Register Family Members**")
        
        new_member = st.text_input("Add a family member's name:", placeholder="Type name here (e.g., Ali, Aisha)...")
        if st.button("✨ Register Member") and new_member:
            clean_name = new_member.strip()
            if clean_name and clean_name not in my_house["scores"]:
                my_house["scores"][clean_name] = 0
                st.toast(f"Profile for '{clean_name}' created successfully! 🎉")
                st.rerun()
        
        if my_house["scores"]:
            active_member = st.selectbox("Select who is scanning this item:", list(my_house["scores"].keys()))
        else:
            st.warning("⚠️ No profiles found in your house yet. Enter a family name above to unlock scanning features!")
            active_member = None

    # ==========================================
    # 🧠 6. ADVANCED GOOGLE GEMINI 1.5 FLASH ENGINE
    # ==========================================
    def analyze_image_with_gemini(uploaded_file, api_key):
        if not api_key:
            return "Raddi & Cardboard (ردی اور گتہ)", LIVE_RATES["raddi"], 5.0, "⚠️ Please provide your free Gemini API Key in the sidebar to unlock real AI features!"
            
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            
            # Formulate flattened layout prompt to prevent literal nesting breaks
            prompt = "Look at this household waste item from Pakistan. Classify it into exactly ONE of these categories: 'raddi' (books, newspaper, cardboard), 'plastic' (drink bottle, cans, tin), 'textile' (torn clothing, rags, fabrics), 'kitchen' (peels, tea leaves, organic), or 'landfill' (diapers, shoppers, wrappers). Respond ONLY in this exact format with a pipeline separator, no quotes or symbols: category_keyword|short_urdu_and_english_household_tip"
            
            response = model.generate_content([prompt, img])
            ai_output = response.text.strip().lower()
            
            if "|" in ai_output:
                parts = ai_output.split("|")
                key = parts[0].strip()
                tip = parts[1].strip()
            else:
                key = "raddi"
                tip = "📦 Save dry for monthly resale."

            if "raddi" in key:
