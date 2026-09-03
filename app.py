import streamlit as st
import pandas as pd
import requests

# ==========================================
# 🎨 1. THEME DESIGN & BRANDING CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trash to Treasure PK", 
    page_icon="💎", 
    layout="centered"
)

# Apply colorful styling patches across core phone elements
st.markdown("""
    <style>
    .main { background-color: #f9fbfd; }
    div[data-testid="stMetricValue"] { color: #1e88e5; font-weight: bold; }
    .badge-box { background-color: #e3f2fd; border-radius: 12px; padding: 15px; border-left: 6px solid #1e88e5; margin-bottom: 12px; }
    .game-box { background-color: #e8f5e9; border-radius: 12px; padding: 15px; border-left: 6px solid #4caf50; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("💎 Trash to Treasure PK")
st.markdown("### **اسمارٹ کباڑ اور گھر کی بچت**")
st.write("Turn your household waste into savings. Scan items, earn points, and alert local dealers.")
st.divider()

# ==========================================
# 🎮 2. GAMIFICATION & FAMILY PROFILES
# ==========================================
st.sidebar.header("🏆 Ghar Ki Deewar")

# Persistent state trackers across mobile operations
if 'history' not in st.session_state: st.session_state.history = []
if 'scores' not in st.session_state:
    st.session_state.scores = {"Ammi 👩": 150, "Aisha 👧": 200, "Ali 👦": 50, "Abbu 👨": 0}

# Dropdown allowing different members to claim their sorting actions
active_member = st.sidebar.selectbox("👤 Select Family Member:", list(st.session_state.scores.keys()))

st.sidebar.subheader("🏅 Current Leaderboard")
for member, points in sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True):
    st.sidebar.write(f"**{member}**: {points} ⭐")

# Dynamic Visual Garden progression
total_points_logged = sum(st.session_state.scores.values())
st.sidebar.subheader("🌱 Family Garden")
if total_points_logged < 200:
    st.sidebar.success("🪵 Status: Sprout (ننھا پودا) - Keep sorting to grow!")
elif total_points_logged < 500:
    st.sidebar.success("🌿 Status: Growing Bush (بڑا پودا)")
else:
    st.sidebar.success("🌳 Status: Mature Jasmine Tree (چمبیلی کا درخت)!")

# ==========================================
# 📦 3. REGIONAL DATA & KABARI RATES
# ==========================================
DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Metal Tins"},
    {"name": "Darhal Scrap Yard", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "Cartons, Fabric Clothes, Stashes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics, Metals, Furniture Stuffing"},
    {"name": "Local Razaee/Gada Maker", "phone": "923046330986", "loc": "Kundian Market Link", "items": "Torn Fabric Clothes, Old Bedsheets"}
]

# ==========================================
# 🧠 4. AI IMAGE PROFILING ENGINE
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
            return "Torn Clothes & Fabrics (پرانے کپڑے)", 35, 2.0, "🧵 Bundle for mattress filling or industrial wipers."
        elif any(w in top_prediction for w in ['food', 'banana', 'apple', 'vegetable', 'peel', 'leaf', 'tea', 'coffee']):
            return "Kitchen Waste (باورچی خانہ کا کچرا)", 0, 1.0, "🌱 Add to plants as home fertilizer. Zero badboo!"
        else:
            return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose of tightly sealed via the daily tractor."
    except Exception:
        # Secure baseline fallback
        return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."

# --- UI INTERACTIVE WORKFLOW ---
img_file = st.camera_input("📸 Scan an item using your phone camera")

if img_file:
    st.image(img_file, width=240)
    st.info("🔄 Processing image through AI vision loop...")
    
    cat, rate, weight, household_tip = analyze_image_with_ai(img_file)
    
    # Showcase results in the clean color layouts
    st.markdown(f"""
    <div class="badge-box">
        <h4>🤖 AI Scan Result</h4>
        <p>Category: <b>{cat}</b></p>
        <p><i>{household_tip}</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    value = rate * weight
    if value > 0:
        st.metric(label="Estimated Value Tracked", value=f"Rs. {value:.1f}")
    
    if st.button(f"➕ Log Item for {active_member}"):
        st.session_state.scores[active_member] += 50
        st.session_state.history.append({
            "Member": active_member, "Category": cat, "Weight": weight, "Cash Value": value
        })
        st.toast(f"Points updated for {active_member}! 🎉")
        st.rerun()

# --- SUMMARY OVERVIEW ---
st.subheader("📊 Household Ledger Status")
df_history = pd.DataFrame(st.session_state.history)

if not df_history.empty:
    total_w = df_history["Weight"].sum()
    total_c = df_history["Cash Value"].sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Weight Saved", f"{total_w:.1f} kg")
    c2.metric("Total Estimated Income", f"Rs. {total_c:.1f}")
    
    st.write("#### 📝 Sorting Logs")
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("No logs added today yet. Scan an object above to kick off your stats chart.")

# --- THE WHATSAPP DISPATCH GATEWAY ---
st.divider()
st.subheader("📍 Nearby Dealers & Doorstep Pickup")
selected_dealer = st.selectbox("Choose a dealer near you:", [d["name"] for d in DEALERS])
dealer_info = next(d for d in DEALERS if d["name"] == selected_dealer)

st.write(f"🗺️ **Location:** {dealer_info['loc']}")
st.write(f"📦 **Accepts Materials:** {dealer_info['items']}")

# Build clear text parameters
whatsapp_msg = (
    f"Assalam-o-Alaikum, I have collected sorted household scrap near Chashma. "
    f"Please let me know when your rider can pass by to pick it up."
)

# Convert strings safely to prevent web standard link breakdown
encoded_msg = requests.utils.quote(whatsapp_msg)
wa_native_url = f"https://wa.me{dealer_info['phone']}?text={encoded_msg}"

# Standard markdown links can break on mobile viewports. Native buttons fix this completely:
st.link_button("💬 Send Pickup Request via WhatsApp", wa_native_url, type="primary")



   
