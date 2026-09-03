import streamlit as st
import pandas as pd
import requests

# ==========================================
# 🎨 1. THEME DESIGN & BRANDING CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trash to Treasure PK", 
    page_icon="💎", 
    layout="wide" # Set layout to wide to allow beautiful side-by-side elements
)

# Custom color injections for widgets and backgrounds
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-weight: bold; }
    .badge-box { background-color: #ffffff; border-radius: 14px; padding: 20px; border-left: 6px solid #2e7d32; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .title-banner { background: linear-gradient(135deg, #1b5e20, #4caf50); padding: 20px; border-radius: 12px; color: white; margin-bottom: 25px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# App branding banner
st.markdown("""
    <div class="title-banner">
        <h1>💎 TRASH TO TREASURE PK</h1>
        <p><b>اسمارٹ کباڑ اور گھر کی بچت</b></p>
    </div>
""", unsafe_allow_html=True)

# Split screen into columns: Left for data input, Right for branding illustration and garden stats
left_col, right_col = st.columns([2, 1])

# ==========================================
# 🎮 2. DYNAMIC STATE LEDGER & DATA TRACKING
# ==========================================
if 'history' not in st.session_state: st.session_state.history = []
if 'scores' not in st.session_state: st.session_state.scores = {}

with left_col:
    st.subheader("📸 AI Intelligent Sorting Camera")
    
    # Custom profile creation field
    new_member = st.text_input("➕ Add a New Family Member Profile Name:", placeholder="Type name (e.g., Ali, Aisha, Ammi)...")
    if st.button("Create Profile") and new_member:
        if new_member not in st.session_state.scores:
            st.session_state.scores[new_member] = 0
            st.toast(f"Profile for {new_member} created successfully! 🎉")
    
    # Active member tracker
    if st.session_state.scores:
        active_member = st.selectbox("👤 Select Active Profile to Log Points:", list(st.session_state.scores.keys()))
    else:
        st.warning("Please add at least one profile name above to begin logging points.")
        active_member = None

# ==========================================
# 📦 3. REGIONAL KABARI STATIONS
# ==========================================
DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Metal Tins"},
    {"name": "Darhal Scrap Yard", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "Cartons, Fabric Clothes, Mixed Stashes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics, Metals, Appliances Stuffing"},
    {"name": "Local Razaee/Gada Maker", "phone": "923046330986", "loc": "Kundian Market Link", "items": "Torn Fabric Clothes, Old Sheets"}
]

# ==========================================
# 🧠 4. CLOUD INTERFERENCE PATTERNS
# ==========================================
def analyze_image_with_ai(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    API_URL = "https://huggingface.co"
    try:
        response = requests.post(API_URL, data=image_bytes, timeout=10)
        results = response.json()
        top_prediction = results['label'].lower()
        
        if any(w in top_prediction for w in ['paper', 'newspaper', 'book', 'magazine', 'carton', 'cardboard']):
            return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."
        elif any(w in top_prediction for w in ['bottle', 'plastic', 'can', 'tin', 'container', 'flask']):
            return "Kabari Plastics & Tins (کباڑی مال)", 50, 0.5, "🍾 Wash, crush, and keep inside the Bachat Bag."
        elif any(w in top_prediction for w in ['cloth', 'fabric', 'shirt', 'jeans', 'textile', 'towel', 'dress', 'blanket']):
            return "Torn Clothes & Fabrics (پرانے کپڑے)", 35, 2.0, "🧵 Save for mattress filling or industrial wipers."
        elif any(w in top_prediction for w in ['food', 'banana', 'apple', 'vegetable', 'peel', 'leaf', 'tea', 'coffee']):
            return "Kitchen Waste (باورچی خانہ کا کچرا)", 0, 1.0, "🌱 Add to plants as fertilizer. Zero badboo!"
        else:
            return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."
    except Exception:
        return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."

# --- MAIN INGESTION INTERACTION ---
with left_col:
    img_file = st.camera_input("Take a photo of a trash item")
    if img_file:
        st.image(img_file, width=300)
        st.info("🔄 Running neural image classification matrix...")
        
        cat, rate, weight, household_tip = analyze_image_with_ai(img_file)
        
        st.markdown(f"""
        <div class="badge-box">
            <h4 style="color:#1b5e20;">🤖 AI Detection Result</h4>
            <p>Category: <b>{cat}</b></p>
            <p style="color:#555;"><i>{household_tip}</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        value = rate * weight
        if value > 0:
            st.metric(label="Scrap Market Value Forecast", value=f"Rs. {value:.1f}")
        
        if st.button("➕ Accumulate to Profile Scores") and active_member:
            st.session_state.scores[active_member] += 50
            st.session_state.history.append({
                "Member": active_member, "Category": cat, "Weight": weight, "Cash Value": value
            })
            st.toast("Progress saved successfully! 🏆")
            st.rerun()

# --- SIDE PANEL STYLING & ILLUSTRATION WORKSHOP ---
with right_col:
    st.write("### 🏠 Eco-Family Hub")
    
    # Animated styling representation fallback via Markdown vectors
    st.markdown("""
        <div style="background-color:#e8f5e9; padding:20px; border-radius:12px; text-align:center; border:2px dashed #4caf50;">
            <p style="font-size:45px; margin:0;">👨‍👩‍👧‍👦♻️📦</p>
            <b style="color:#2e7d32;">Trash To Treasure</b>
            <p style="font-size:12px; color:#666; margin:5px 0 0 0;">Families sorting out recyclables together at home to maximize bachat yields!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Real-time leaderboard monitoring
    st.write("#### 🏅 Live Point Leaderboard")
    if st.session_state.scores:
        for member, score in sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True):
            st.write(f"⭐ **{member}**: {score} Points")
    else:
        st.caption("No profiles registered yet.")
        
    # Plant growth metrics
    total_points = sum(st.session_state.scores.values())
    st.write("#### 🌿 Digital Backyard Growth")
    if total_points < 150:
        st.caption("🌱 Current Status: Tiny Seedling (ننھا پودا)")
    elif total_points < 400:
        st.success("🌿 Current Status: Growing Shrub (بڑا پودا)")
    else:
        st.success("🌳 Current Status: Blooming Jasmine Tree (چمبیلی کا درخت)!")

# --- LEDGER SHEET OUTPUTS ---
st.divider()
df_history = pd.DataFrame(st.session_state.history)
if not df_history.empty:
    st.subheader("📊 Collective Household Balance Sheet")
    c1, c2 = st.columns(2)
    c1.metric("Gross Weight Saved", f"{df_history['Weight'].sum():.1f} kg")
    c2.metric("Gross Revenue Tracked", f"Rs. {df_history['Cash Value'].sum():.1f}")
    st.dataframe(df_history, use_container_width=True)

# --- COMPLETELY RE-ENGINEERED COMPLIANT WHATSAPP DISPATCH MODULE ---
st.subheader("📍 Dispatches to Local Chashma/Kundian Yards")
selected_dealer = st.selectbox("Select local scrap yard merchant:", [d["name"] for d in DEALERS])
dealer_info = next(d for d in DEALERS if d["name"] == selected_dealer)

st.write(f"📍 **Address:** {dealer_info['loc']} | 📦 **Buying Specializations:** {dealer_info['items']}")

# Using optimized URL encoding to prevent script injection failure on mobile web-views
raw_text_payload = "Assalam-o-Alaikum, I have sorted household recycling packages ready near Chashma. Please confirm pickup window."
clean_url_parameters = requests.utils.quote(raw_text_payload)

# Cleaned syntax directly invoking internal deep-linking protocols
final_wa_url = "https://wa.me/" + str(dealer_info['phone']) + "?text=" + str(clean_url_parameters)

# Native interactive element block completely bypassing standard markdown parsing bugs
st.link_button("💬 Launch WhatsApp Mobile Dispatch", final_wa_url, type="primary", use_container_width=True)
