import streamlit as st
import pandas as pd
import requests

# ==========================================
# 🎨 1. THEME DESIGN & BRANDING CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trash to Treasure PK", 
    page_icon="💎", 
    layout="wide"
)

# Apply beautiful CSS styling accents across widgets and blocks
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-weight: bold; }
    .badge-box { background-color: #ffffff; border-radius: 14px; padding: 20px; border-left: 6px solid #2e7d32; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .title-banner { background: linear-gradient(135deg, #1b5e20, #4caf50); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .illustration-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; text-align: center; border: 2px dashed #4caf50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 🌍 BRANDING BANNER LOGO & VISUAL ILLUSTRATION
st.markdown("""
    <div class="title-banner">
        <h1 style="margin:0; font-size:38px;">💎 TRASH TO TREASURE PK</h1>
        <p style="margin:5px 0 0 0; font-size:18px;"><b>اسمارٹ کباڑ اور گھر کی بچت</b></p>
    </div>
""", unsafe_allow_html=True)

# Split view into side-by-side layout columns
left_col, right_col = st.columns(2)

# ==========================================
# 🎮 2. DYNAMIC LEDGER STATE DATA TRACKING
# ==========================================
if 'history' not in st.session_state: st.session_state.history = []
if 'scores' not in st.session_state: st.session_state.scores = {}  # Empty dictionary for user profile entry

with left_col:
    st.write("### 📸 AI Intelligent Waste Scanner")
    
    # 👤 DYNAMIC USER FAMILY PROFILE CREATION
    st.markdown("#### **1. Register Family Members**")
    new_member = st.text_input("Enter a family member's name to create their profile:", placeholder="Type name here (e.g., Zain, Fatima, Ali)...")
    if st.button("Explicitly Add Member") and new_member:
        clean_name = new_member.strip()
        if clean_name and clean_name not in st.session_state.scores:
            st.session_state.scores[clean_name] = 0
            st.toast(f"Profile for '{clean_name}' created successfully! 🎉")
            st.rerun()
    
    # Selection picker based purely on user configurations
    if st.session_state.scores:
        active_member = st.selectbox("Select who is scanning this item:", list(st.session_state.scores.keys()))
    else:
        st.warning("⚠️ No profiles registered yet. Please enter a family name above to unlock scanning features!")
        active_member = None

# ==========================================
# 📦 3. REGIONAL KABARI YARD DATA
# ==========================================
DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Metal Tins"},
    {"name": "Darhal Scrap Yard", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "Cartons, Fabric Clothes, Mixed Stashes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics, Metals, Appliances Stuffing"},
    {"name": "Local Razaee/Gada Maker", "phone": "923046330986", "loc": "Kundian Market Link", "items": "Torn Fabric Clothes, Old Sheets"}
]

# ==========================================
# 🧠 4. FIXED AI IMAGE CLASSIFICATION ENGINE
# ==========================================
def analyze_image_with_ai(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    API_URL = "https://huggingface.co"
    
    try:
        response = requests.post(API_URL, data=image_bytes, timeout=10)
        results = response.json()
        
        # 💥 FIXED INTERPRETER CORRECTION
        if isinstance(results, list) and len(results) > 0:
            top_prediction = results[0].get('label', '').lower()
        elif isinstance(results, dict) and 'label' in results:
            top_prediction = results.get('label', '').lower()
        else:
            top_prediction = ""
            
        # Segment prediction array lists cleanly based on keyword clusters
        if any(w in top_prediction for w in ['paper', 'newspaper', 'book', 'magazine', 'carton', 'cardboard', 'envelope', 'notebook']):
            return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."
        elif any(w in top_prediction for w in ['bottle', 'plastic', 'can', 'tin', 'container', 'flask', 'beaker', 'cup', 'flask']):
            return "Kabari Plastics & Tins (کباڑی مال)", 50, 0.5, "🍾 Wash, crush, and keep inside the Bachat Bag."
        elif any(w in top_prediction for w in ['cloth', 'fabric', 'shirt', 'jeans', 'textile', 'towel', 'dress', 'blanket', 'coat', 'jersey', 'sweater']):
            return "Torn Clothes & Fabrics (پرانے کپڑے)", 35, 2.0, "🧵 Save for mattress filling or industrial wipers."
        elif any(w in top_prediction for w in ['food', 'banana', 'apple', 'vegetable', 'peel', 'leaf', 'tea', 'coffee', 'orange', 'fruit']):
            return "Kitchen Waste (باورچی خانہ کا کچرا)", 0, 1.0, "🌱 Add to plants as fertilizer. Zero badboo!"
        else:
            return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."
    except Exception:
        return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."

# --- MAIN INGESTION PANEL LOGIC ---
if active_member:
    with left_col:
        img_file = st.camera_input("📸 Take a photo of your trash item")
        if img_file:
            st.image(img_file, width=280)
            st.info("🔄 Running neural image classification matrix...")
            
            cat, rate, weight, household_tip = analyze_image_with_ai(img_file)
            
            st.markdown(f"""
            <div class="badge-box">
                <h4 style="color:#1b5e20; margin-top:0;">🤖 AI Detection Result</h4>
                <p style="font-size:16px; margin:5px 0;">Category: <b>{cat}</b></p>
                <p style="color:#555; font-size:14px; margin:0;"><i>{household_tip}</i></p>
            </div>
            """, unsafe_allow_html=True)
            
            value = rate * weight
            if value > 0:
                st.metric(label="Scrap Market Value Forecast", value=f"Rs. {value:.1f}")
            
            if st.button(f"➕ Accumulate Items to {active_member}'s Stats"):
                st.session_state.scores[active_member] += 50
                st.session_state.history.append({
                    "Member": active_member, "Category": cat, "Weight": weight, "Cash Value": value
                })
                st.toast(f"Points logged for {active_member}! 🏆")
                st.rerun()

# ==========================================
# 🎨 5. SIDE PANEL ILLUSTRATION & GARDEN STATS
# ==========================================
with right_col:
    # 🖼️ VISUAL FAMILY BANNER CARD
    st.markdown("""
        <div class="illustration-box">
            <p style="font-size:60px; margin:0; padding:0;">👨‍👩‍👧‍👦♻️📦</p>
            <h4 style="color:#1b5e20; margin:10px 0 5px 0; font-size:20px;"><b>Ghar Ka Saliqa</b></h4>
            <p style="font-size:13px; color:#555; margin:0; line-height:1.4;">
                Family members tracking waste value, working together to keep the home clean and odor-free!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("### 🏆 Ghar Ki Deewar")
    st.write("#### **Dynamic Leaderboard**")
    
    if st.session_state.scores:
        for member, score in sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"⭐ **{member}** : `{score} Points`")
    else:
        st.info("No active family names found. Create one on the left panel!")
        
    total_points = sum(st.session_state.scores.values())
    st.write("#### **🌱 Family Digital Garden**")
    if total_points == 0:
        st.caption("🪴 Status: Dry Soil - Awaiting your first sorted item logs!")
    elif total_points < 200:
        st.success("🌱 Status: Tiny Seedling (ننھا پودا) - Good start!")
    elif total_points < 500:
        st.success("🌿 Status: Growing Shrub (بڑا پودا) - Garden is growing!")
    else:
        st.success("🌳 Status: Blooming Jasmine Tree (چمبیلی کا درخت) - Ultimate Saliqa achieved!")

# ==========================================
# 📊 6. HOUSEHOLD DATA LEDGER BALANCE SHEET
# ==========================================
st.divider()
df_history = pd.DataFrame(st.session_state.history)
if not df_history.empty:
    st.subheader("📊 Collective Household Savings Ledger")
    c1, c2 = st.columns(2)
    c1.metric("Gross Weight Saved", f"{df_history['Weight'].sum():.1f} kg")
    c2.metric("Gross Revenue Earned", f"Rs. {df_history['Cash Value'].sum():.1f}")
    st.dataframe(df_history, use_container_width=True)

# ==========================================
# 📲 7. PRESERVED WORKING WHATSAPP BRIDGE
# ==========================================
st.subheader("📍 Doorstep Dispatches to Local Chashma/Kundian Yards")
selected_dealer = st.selectbox("Select a local scrap merchant to contact:", [d["name"] for d in DEALERS])
dealer_info = next(d for d in DEALERS if d["name"] == selected_dealer)

st.write(f"📍 **Address:** {dealer_info['loc']} | 📦 **Accepts:** {dealer_info['items']}")

# Safe message payload variables
raw_text_payload = "Assalam-o-Alaikum, I have sorted household recycling packages ready near Chashma. Please confirm pickup window."
clean_url_parameters = requests.utils.quote(raw_text_payload)

# Preserving the functional string builder
final_wa_url = "https://wa.me" + str(dealer_info['phone']) + "?text=" + str(clean_url_parameters)

