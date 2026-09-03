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

st.title("💎 TRASH TO TREASURE PK")
st.markdown("### **اسمارٹ کباڑ اور گھر کی بچت**")
st.write("Turn your household waste into savings. Scan items, earn points, and alert local dealers.")
st.divider()

# ==========================================
# 📦 2. REGIONAL KABARI YARD DATA (ALWAYS ACCESSIBLE)
# ==========================================
DEALERS = [
    {"name": "Kabar Shop (Kundian)", "phone": "923017800615", "loc": "Garnely Road, Kundian", "items": "Plastics, Paper, Metal Tins"},
    {"name": "Darhal Scrap Yard", "phone": "923327656648", "loc": "Chashma Road, Khanqah Sirajia", "items": "Cartons, Fabric Clothes, Mixed Stashes"},
    {"name": "Shah G Scrap Dealers", "phone": "923706000509", "loc": "Eid Gah Road, Mianwali", "items": "Bulk Plastics, Metals, Appliances Stuffing"},
    {"name": "Local Razaee/Gada Maker", "phone": "923046330986", "loc": "Kundian Market Link", "items": "Torn Fabric Clothes, Old Sheets"}
]

# ==========================================
# 🔑 3. DATA ISOLATION ENGINE (GHAR KA CODE)
# ==========================================
if 'global_db' not in st.session_state:
    st.session_state.global_db = {}

st.sidebar.header("🔑 Household Access")
st.sidebar.write("Create or enter a unique code for your house to keep your profile private.")

household_code = st.sidebar.text_input("Enter Household Code (گھر کا کوڈ):", placeholder="e.g., khan-house-chashma").strip().lower()

current_cash_total = 0.0

if not household_code:
    st.warning("👋 Welcome! Please type a unique Household Code in the sidebar to load your private, customized space.")
    st.info("💡 Tip: You can invent any code you want (like your name or house number). Just remember it so your family can log back in later!")
else:
    if household_code not in st.session_state.global_db:
        st.session_state.global_db[household_code] = {
            "scores": {},      
            "history": []       
        }
        st.sidebar.success(f"🆕 New private space initialized for code: {household_code}!")
    else:
        st.sidebar.success(f"🔓 Private space unlocked for: {household_code}")

    my_house = st.session_state.global_db[household_code]
    left_col, right_col = st.columns(2)

    with left_col:
        st.write("### 📸 AI Intelligent Waste Scanner")
        st.markdown("#### **1. Register Family Members**")
        
        new_member = st.text_input("Add a family member's name to your private space:", placeholder="Type name here (e.g., Ali, Aisha)...")
        if st.button("✨ Register Member") and new_member:
            clean_name = new_member.strip()
            if clean_name and clean_name not in my_house["scores"]:
                my_house["scores"][clean_name] = 0
                st.toast(f"Profile for '{clean_name}' created in your house! 🎉")
                st.rerun()
        
        if my_house["scores"]:
            active_member = st.selectbox("Select who is scanning this item:", list(my_house["scores"].keys()))
        else:
            st.warning("⚠️ No profiles found in your house yet. Enter a family name above to unlock scanning features!")
            active_member = None

    def analyze_image_with_ai(uploaded_file):
        image_bytes = uploaded_file.getvalue()
        API_URL = "https://huggingface.co"
        
        try:
            response = requests.post(API_URL, data=image_bytes, timeout=10)
            results = response.json()
            
            top_prediction = ""
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
            elif any(w in top_prediction for w in ['cloth', 'fabric', 'shirt', 'jeans', 'textile', 'towel', 'dress', 'blanket', 'coat', 'jersey', 'sweater', 'rag', 'wool', 'cotton', 'red', 'maroon', 'velvet', 'silk', 'garment', 'apparel']):
                return "Torn Clothes & Fabrics (پرانے کپڑے)", 35, 1.0, "🧵 Save for mattress filling or industrial wipers."
            elif any(w in top_prediction for w in ['food', 'banana', 'apple', 'vegetable', 'peel', 'leaf', 'tea', 'coffee', 'orange', 'fruit', 'waste', 'garbage', 'scraps']):
                return "Kitchen Waste (باورچی خانہ کا کچرا)", 0, 0.5, "🌱 Add to plants as fertilizer. Zero badboo!"
            else:
                return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."
        except Exception:
            return "Landfill Waste (عام کچرا)", 0, 0.5, "🗑️ Dispose tightly via the daily vehicle."

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

    with right_col:
        st.write("### 👨‍👩‍👧‍👦 Ghar Ka Saliqa")
        st.write("Working together to keep your kitchen clean and collect bachat!")
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

    st.divider()
    df_history = pd.DataFrame(my_house["history"])
    
    if not df_history.empty:
        st.subheader("📊 Your Private Savings Ledger")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Gross Weight Saved", f"{df_history['Weight'].sum():.1f} kg")
        col_m2.metric("Gross Revenue Earned", f"Rs. {df_history['Cash Value'].sum():.1f}")
        st.dataframe(df_history, use_container_width=True)
        current_cash_total = df_history['Cash Value'].sum()
    else:
        st.info("Your savings ledger table is empty. Create profiles and scan items to record your stats!")

# ==========================================
# 📲 8. MAIN PLATFORM BASE DIRECTORY & WHATSAPP GATEWAY (PERMANENT)
# ==========================================
st.divider()
st.subheader("📍 Doorstep Dispatches to Local Chashma/Kundian Yards")
selected_dealer = st.selectbox("Select a local scrap merchant to contact:", [d["name"] for d in DEALERS])
dealer_info = next(d for d in DEALERS if d["name"] == selected_dealer)

st.write(f"📍 **Address:** {dealer_info['loc']} | 📦 **Accepts:** {dealer_info['items']}")

raw_text_payload = (
    f"Assalam-o-Alaikum, I have sorted household recycling packages ready near Chashma. "
    f"Total estimated ledger value is Rs. {current_cash_total:.1f}. Please confirm pickup window."
)
clean_url_parameters = requests.utils.quote(raw_text_payload)

final_wa_url = "https://wa.me" + str(dealer_info['phone']) + "?text=" + str(clean_url_parameters)
st.link_button("💬 Launch WhatsApp Mobile Dispatch", final_wa_url, type="primary", use_container_width=True)
