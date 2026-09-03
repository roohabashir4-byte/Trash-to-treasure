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

# Apply beautiful CSS styling accents across widgets and blocks at the absolute top layer
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-weight: bold; }
    .badge-box { background-color: #ffffff; border-radius: 14px; padding: 20px; border-left: 6px solid #2e7d32; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .title-banner { background: linear-gradient(135deg, #1b5e20, #4caf50); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .illustration-box { background-color: #e8f5e9; padding: 20px; border-radius: 12px; text-align: center; border: 2px dashed #4caf50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 🌍 BRANDING BANNER LOGO & VISUAL ILLUSTRATION BANNER
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
# 🧠 3. GLOBAL DEEP ANALYSIS IMAGE CLASSIFICATION ENGINE (PULLED TO TOP)
# ==========================================
def analyze_image_with_ai(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    API_URL = "https://huggingface.co"
    
    try:
        response = requests.post(API_URL, data=image_bytes, timeout=10)
        results = response.json()
        
        top_prediction = ""
        # ✅ FIXED: Explicitly checks and grabs index 0 of the list array safely
        if isinstance(results, list) and len(results) > 0:
            first_item = results[0]
            if isinstance(first_item, dict) and 'label' in first_item:
                top_prediction = first_item['label'].lower()
        elif isinstance(results, dict) and 'label' in results:
            top_prediction = results['label'].lower()
            
        if not top_prediction:
            top_prediction = "unknown"

        if any(w in top_prediction for w in ['paper', 'newspaper', 'book', 'magazine', 'carton', 'cardboard', 'envelope', 'notebook', 'packet']):
            return "Raddi & Cardboard (ردی اور گتہ)", 45, 5.0, "📦 Save dry for monthly resale."
        elif any(w in top_prediction for w in ['bottle', 'plastic', 'can', 'tin', 'container', 'flask', 'beaker', 'cup', 'glass', 'sprite', 'soda', 'pop', 'vessel']):
            return "Kabari Plastics & Tins (کباڑی مال)", 50, 0.1, "🍾 Wash, crush, and keep inside the Bachat Bag."
        elif any(w in top_prediction for w in ['cloth', 'fabric', 'shirt', 'jeans', 'textile', 'towel', 'dress', 'blanket', 'coat', 'jersey', 'sweater', 'rag', 'wool', 'cotton', 'red', 'maroon', 'velvet', 'silk', 'garment', 'apparel', 'handkerchief']):
            return "Torn Clothes & Fabrics (پرانے کپڑے)", 35, 1.0, "🧵 Save for mattress filling or industrial wipers."
        elif any(w in top_prediction for w in ['food', 'banana', 'apple', 'vegetable', 'peel', 'leaf', 'tea', 'coffee', 'orange', 'fruit', 'waste', 'garbage', 'scraps']):
            return "Kitchen Waste (باورچی خانہ کا کچرا)", 0, 0.5, "🌱 Add to plants as fertilizer. Zero badboo!"
        else:
            return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."
    except Exception:
        return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."

# ==========================================
# 🔑 4. DATA ISOLATION ENGINE (GHAR KA CODE)
# ==========================================
if 'global_db' not in st.session_state:
    st.session_state.global_db = {}

st.sidebar.header("🔑 Household Access")
st.sidebar.write("Create or enter a unique code for your house to keep your profile private.")

household_code = st.sidebar.text_input("Enter Household Code (گھر کا کوڈ):", placeholder="e.g., khan-house-chashma").strip().lower()

# Global placeholder for the baseline metrics scope
current_cash_total = 0.0

if not household_code:
    st.warning("👋 Welcome! Please type a unique Household Code in the sidebar to load your private, customized space.")
    st.info("💡 *Tip: You can invent any code you want (like your name or house number). Just remember it so your family can log back in later!*")
else:
    if household_code not in st.session_state.global_db:
        st.session_state.global_db[household_code] = {
            "scores": {},      
            "history": []       
        }
        st.sidebar.success(f"🆕 New private space initialized for code: **{household_code}**!")
    else:
        st.sidebar.success(f"🔓 Private space unlocked for: **{household_code}**")

    my_house = st.session_state.global_db[household_code]
    left_col, right_col = st.columns(2)

    # ==========================================
    # 🎮 5. DYNAMIC USER REGISTRATION HUB
    # ==========================================
    with left_col:
        st.write("### 📸 AI Intelligent Waste Scanner")
        st.markdown("#### **1. Register Family Members**")
        
        new_member = st.text_input("Add a family member's name to your private space:", placeholder="Type name here (e.g., Ali, Aisha)...")
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

    # --- IMAGE INGESTION WORKFLOW LOGIC ---
    if active_member:
        with left_col:
            img_file = st.camera_input("📸 Take a photo of your trash item")
            if img_file:
                st.image(img_file, width=280)
                st.info("🔄 Running neural image classification matrix...")
                
                cat, rate, weight, household_tip = analyze_image_with_ai(img_file)
                
                st.write(f"### 🤖 AI Detection Result")
                st.write(f"Category: **{cat}**")
                st.write(f"*{household_tip}*")
                
                value = rate * weight
                st.metric(label="Scrap Market Value Forecast", value=f"Rs. {value:.1f}")
                
                if st.button(f"➕ Accumulate Items to {active_member}'s Stats"):
                    my_house["scores"][active_member] += 50
                    my_house["history"].append({
                        "Member": active_member, "Category": cat, "Weight": weight, "Cash Value": value
                    })
                    st.toast(f"Points logged for {active_member}! 🏆")
                    st.rerun()

    # ==========================================
    # 🖼️ 6. SIDE PANEL ILLUSTRATION BANNER CARD & LEADERBOARD
    # ==========================================
    with right_col:
        st.markdown("""
            <div class="illustration-box">
                <p style="font-size:60px; margin:0; padding:0;">👨‍👩‍👧‍👦♻️📦</p>
                <h4 style="color:#1b5e20; margin:10px 0 5px 0; font-size:20px;"><b>Ghar Ka Saliqa</b></h4>
                <p style="font-size:13px; color:#555; margin:0; line-height:1.4;">
                    Your isolated household data stack. Working together to keep your kitchen clean and collect bachat!
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("### 🏆 Ghar Ki Deewar")
        st.write("#### **Your Family Leaderboard**")
        
        if my_house["scores"]:
            for member, score in sorted(my_house["scores"].items(), key=lambda x: x, reverse=True):
                st.markdown(f"⭐ **{member}** : `{score} Points`")
        else:
            st.info("Your leaderboard is empty. Add your family profiles above!")
            
        total_points = sum(my_house["scores"].values())
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
