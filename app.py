
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

# Apply beautiful CSS styling
st.markdown("""
    <style>
    .main {
        background-color: #f4f7f6;
    }

    div[data-testid="stMetricValue"] {
        color: #2e7d32;
        font-weight: bold;
    }

    .badge-box {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 20px;
        border-left: 6px solid #2e7d32;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    .title-banner {
        background: linear-gradient(135deg, #1b5e20, #4caf50);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    .illustration-box {
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 2px dashed #4caf50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    @keyframes pulse-green {
        0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
        }

        70% {
            box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
        }

        100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
        }
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


# ==========================================
# 🌍 BRANDING BANNER LOGO
# ==========================================
st.markdown("""
    <div class="title-banner">
        <h1 style="margin:0; font-size:38px;">
            💎 TRASH TO TREASURE PK
        </h1>

        <p style="margin:5px 0 0 0; font-size:18px;">
            <b>اسمارٹ کباڑ اور گھر کی بچت</b>
        </p>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# 📦 2. REGIONAL KABARI YARD DATA
# ==========================================
DEALERS = [
    {
        "name": "Kabar Shop (Kundian)",
        "phone": "923017800615",
        "loc": "Garnely Road, Kundian",
        "items": "Plastics, Paper, Metal Tins"
    },
    {
        "name": "Darhal Scrap Yard",
        "phone": "923327656648",
        "loc": "Chashma Road, Khanqah Sirajia",
        "items": "Cartons, Fabric Clothes, Mixed Stashes"
    },
    {
        "name": "Shah G Scrap Dealers",
        "phone": "923706000509",
        "loc": "Eid Gah Road, Mianwali",
        "items": "Bulk Plastics, Metals, Appliances Stuffing"
    },
    {
        "name": "Local Razaee/Gada Maker",
        "phone": "923046330986",
        "loc": "Kundian Market Link",
        "items": "Torn Fabric Clothes, Old Sheets"
    }
]


# ==========================================
# 📈 3. LIVE WEBSCRAPER & CACHE PROTECTION
# ==========================================
@st.cache_data(ttl=3600)
def fetch_live_pakistan_rates():

    url = "https://getscraprate.com"

    defaults = {
        "plastic": 62.25,
        "raddi": 43.51,
        "cardboard": 30.98,
        "textile": 35.00
    }

    try:

        req = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )

        if req.status_code == 200:

            soup = BeautifulSoup(req.text, "html.parser")

            text_data = soup.get_text().lower()

            def extract_rate(item_name, default_val):

                if item_name in text_data:

                    parts = text_data.split(item_name)

                    for part in parts[1:]:

                        words = part.split()

                        for word in words:

                            clean_word = "".join(
                                c for c in word
                                if c.isdigit() or c == "."
                            )

                            if clean_word:

                                try:

                                    val = float(clean_word)

                                    if 10 < val < 200:
                                        return val

                                except ValueError:
                                    continue

                return default_val

            return {
                "plastic": extract_rate(
                    "plastic",
                    defaults["plastic"]
                ),

                "raddi": extract_rate(
                    "newspaper",
                    defaults["raddi"]
                ),

                "cardboard": extract_rate(
                    "cardboard",
                    defaults["cardboard"]
                ),

                "textile": defaults["textile"]
            }

    except Exception:
        pass

    return defaults


LIVE_RATES = fetch_live_pakistan_rates()


# ==========================================
# 🔑 4. SIDEBAR ACCESS & MARKET TICKER
# ==========================================
st.sidebar.header("🔑 Household Access")

household_code = st.sidebar.text_input(
    "Enter Household Code (گھر کا کوڈ):",
    placeholder="e.g., khan-house-chashma"
).strip().lower()

st.sidebar.divider()

st.sidebar.subheader(
    "📈 Today's Punjab Bazar (لائیو ریٹ)"
)


# Market alert
if (
    LIVE_RATES["plastic"] >= 60.0
    or LIVE_RATES["raddi"] >= 40.0
):

    st.sidebar.markdown("""
        <div class="price-flash-green">
            📈 Bazar Up: Good Time to Sell!<br>
            <span style="font-size:12px; font-weight:normal;">
                (آج ریٹ تیز ہے - مال بیچیں)
            </span>
        </div>
    """, unsafe_allow_html=True)

else:

    st.sidebar.markdown("""
        <div style="
            background-color:#fff3cd;
            color:#856404;
            padding:12px;
            border-radius:8px;
            border-left:5px solid #ffc107;
            font-weight:bold;
            text-align:center;
            margin-bottom:15px;
        ">
            ⚠️ Bazar Normal: Hold or Compare<br>

            <span style="font-size:12px; font-weight:normal;">
                (مارکیٹ مستحکم ہے)
            </span>
        </div>
    """, unsafe_allow_html=True)


# Display rates
st.sidebar.markdown(f"""
    <div class="sidebar-rate-text">
        🍾 <b>Plastics & Cans:</b>
        Rs. {LIVE_RATES['plastic']:.2f} / kg
    </div>

    <div class="sidebar-rate-text">
        📦 <b>Raddi Newspaper:</b>
        Rs. {LIVE_RATES['raddi']:.2f} / kg
    </div>

    <div class="sidebar-rate-text">
        🗂️ <b>Cardboard Box:</b>
        Rs. {LIVE_RATES['cardboard']:.2f} / kg
    </div>

    <div class="sidebar-rate-text">
        🧵 <b>Fabric Clothes:</b>
        Rs. {LIVE_RATES['textile']:.2f} / kg
    </div>
""", unsafe_allow_html=True)


# ==========================================
# 🧠 GOOGLE AI STUDIO CONFIGURATION
# ==========================================
st.sidebar.divider()

st.sidebar.subheader(
    "🧠 Google AI Studio Configuration"
)

gemini_api_key = st.sidebar.text_input(
    "Enter Gemini API Key:",
    type="password",
    help="Get a free key from Google AI Studio website."
)


# ==========================================
# 💾 SESSION DATABASE
# ==========================================
current_cash_total = 0.0

if "global_db" not in st.session_state:

    st.session_state.global_db = {}


# ==========================================
# 🔐 HOUSEHOLD LOGIN
# ==========================================
if not household_code:

    st.warning(
        "👋 Welcome! Please type a unique Household Code "
        "in the sidebar to load your private, customized space."
    )

    st.info(
        "💡 Tip: You can invent any code you want "
        "(like your name or house number). "
        "Just remember it so your family can log back in later!"
    )

else:

    # Create household
    if household_code not in st.session_state.global_db:

        st.session_state.global_db[household_code] = {
            "scores": {},
            "history": []
        }

        st.sidebar.success(
            f"🆕 Private space created: **{household_code}**!"
        )

    else:

        st.sidebar.success(
            f"🔓 Private space unlocked for: "
            f"**{household_code}**"
        )


    my_house = st.session_state.global_db[household_code]


    # ==========================================
    # 📱 MAIN COLUMNS
    # ==========================================
    left_col, right_col = st.columns(2)


    # ==========================================
    # 🎮 5. USER REGISTRATION INTERFACE
    # ==========================================
    with left_col:

        st.write("### 📸 AI Intelligent Waste Scanner")

        st.markdown(
            "#### **1. Register Family Members**"
        )


        # Add family member
        new_member = st.text_input(
            "Add a family member's name:",
            placeholder="Type name here (e.g., Ali, Aisha)..."
        )


        if st.button("✨ Register Member") and new_member:

            clean_name = new_member.strip()

            if clean_name and clean_name not in my_house["scores"]:

                my_house["scores"][clean_name] = 0

                st.toast(
                    f"Profile for '{clean_name}' created successfully! 🎉"
                )

                st.rerun()


        # Select family member
        if my_house["scores"]:

            active_member = st.selectbox(
                "Select who is scanning this item:",
                list(my_house["scores"].keys())
            )

        else:

            st.warning(
                "⚠️ No profiles found in your house yet. "
                "Enter a family name above to unlock scanning features!"
            )

            active_member = None


    # ==========================================
    # 🧠 6. GOOGLE GEMINI AI ENGINE
    # ==========================================
    def analyze_image_with_gemini(uploaded_file, api_key):

        # No API key
        if not api_key:

            return (
                "raddi",
                LIVE_RATES["raddi"],
                5.0,
                "⚠️ Please provide your free Gemini API Key "
                "in the sidebar to unlock real AI features!"
            )


        try:

            # Configure Gemini
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel(
                "gemini-1.5-flash"
            )


            # Open image
            img = Image.open(uploaded_file)


            # AI prompt
            prompt = """
Look at this household waste item from Pakistan.

Classify it into exactly ONE of these categories:

'raddi' = books, newspaper, cardboard

'plastic' = drink bottle, cans, tin

'textile' = torn clothing, rags, fabrics

'kitchen' = peels, tea leaves, organic

'landfill' = diapers, shoppers, wrappers

Respond ONLY in this exact format:

category_keyword|short_urdu_and_english_household_tip

Do not use quotes or extra symbols.
"""


            # Ask Gemini
            response = model.generate_content(
                [prompt, img]
            )


            ai_output = response.text.strip().lower()


            # Default values
            key = "raddi"

            tip = "📦 Save dry for monthly resale."


            # Read AI result
            if "|" in ai_output:

                parts = ai_output.split("|")

                if len(parts) >= 2:

                    key = parts[0].strip()

                    tip = parts[1].strip()


            # ==========================================
            # 💰 CATEGORY & RATE
            # ==========================================

            if "raddi" in key:

                key = "raddi"

                rate = LIVE_RATES["raddi"]


            elif "plastic" in key:

                key = "plastic"

                rate = LIVE_RATES["plastic"]


            elif "textile" in key:

                key = "textile"

                rate = LIVE_RATES["textile"]


            elif "kitchen" in key:

                key = "kitchen"

                rate = 0.0


            else:

                key = "landfill"

                rate = 0.0


            # Return result
            return key, rate, 5.0, tip


        except Exception as e:

            return (
                "raddi",
                LIVE_RATES["raddi"],
                5.0,
                f"⚠️ AI error: {str(e)}"
            )


    # ==========================================
    # 📸 IMAGE UPLOAD
    # ==========================================
    with left_col:

        st.markdown(
            "#### **2. Upload Waste Item**"
        )


        uploaded_file = st.file_uploader(
            "Upload a photo of your waste item:",
            type=["jpg", "jpeg", "png"]
        )


        if uploaded_file is not None:

            st.image(
                uploaded_file,
                caption="Uploaded Waste Item",
                use_container_width=True
            )


            if active_member:

                if st.button(
                    "🤖 Analyze Waste with AI"
                ):

                    with st.spinner(
                        "🧠 AI is analyzing your waste..."
                    ):

                        category, rate, points, tip = (
                            analyze_image_with_gemini(
                                uploaded_file,
                                gemini_api_key
                            )
                        )


                    # Save result
                    st.session_state["last_result"] = {
                        "category": category,
                        "rate": rate,
                        "points": points,
                        "tip": tip,
                        "member": active_member
                    }


                    # Add points
                    my_house["scores"][active_member] += points


                    # Add history
                    my_house["history"].append({
                        "member": active_member,
                        "category": category,
                        "rate": rate,
                        "points": points
                    })


                    st.success(
                        "✅ Waste analyzed successfully!"
                    )

                    st.rerun()


    # ==========================================
    # 📊 7. RESULTS
    # ==========================================
    with right_col:

        st.write("### 📊 Household Dashboard")


        if "last_result" in st.session_state:

            result = st.session_state["last_result"]


            st.markdown(
                f"""
                <div class="illustration-box">

                    <h2>
                        ♻️ {result['category'].upper()}
                    </h2>

                    <h3>
                        💰 Rs. {result['rate']:.2f} / kg
                    </h3>

                    <p>
                        {result['tip']}
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


            st.metric(
                "⭐ Points Earned",
                f"{result['points']:.1f}"
            )


        # ==========================================
        # 👨‍👩‍👧 FAMILY SCORES
        # ==========================================
        st.markdown(
            "#### 🏆 Family Member Scores"
        )


        if my_house["scores"]:

            for member, score in my_house["scores"].items():

                st.markdown(
                    f"""
                    <div class="badge-box">
                        👤 <b>{member}</b>
                        <br>
                        ⭐ {score:.1f} points
                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # ==========================================
        # 📜 HISTORY
        # ==========================================
        st.markdown(
            "#### 📜 Waste History"
        )


        if my_house["history"]:

            history_df = pd.DataFrame(
                my_house["history"]
            )

            st.dataframe(
                history_df,
                use_container_width=True
            )

        else:

            st.info(
                "No waste scanning history yet."
            )


    # ==========================================
    # ♻️ 8. DEALERS
    # ==========================================
    st.divider()

    st.subheader(
        "🏪 Nearby Kabari / Recycling Contacts"
    )


    for dealer in DEALERS:

        st.markdown(
            f"""
            <div class="badge-box">

                <h4>
                    🏪 {dealer['name']}
                </h4>

                <p>
                    📍 <b>Location:</b> {dealer['loc']}
                </p>

                <p>
                    ♻️ <b>Accepts:</b> {dealer['items']}
                </p>

                <p>
                    📞 <b>Phone:</b> {dealer['phone']}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )
```
