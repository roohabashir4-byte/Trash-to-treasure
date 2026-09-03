import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
import google.generativeai as genai


# ==========================================
# 🎨 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Trash to Treasure PK",
    page_icon="💎",
    layout="wide"
)


# ==========================================
# 🎨 2. CUSTOM CSS
# ==========================================

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
# 💎 3. BRANDING BANNER
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
# 📦 4. KABARI DEALERS
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
# 📈 5. LIVE SCRAP RATES
# ==========================================

@st.cache_data(ttl=3600)
def fetch_live_pakistan_rates():

    url = "https://getscraprate.com"

    defaults = {
        "plastic": 50.00,
        "raddi": 50.00,
        "cardboard": 50.00,
        "textile": 35.00
    }

    try:

        req = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=8
        )

        if req.status_code == 200:

            soup = BeautifulSoup(
                req.text,
                "html.parser"
            )

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
# 🔑 6. SIDEBAR
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


# ==========================================
# 📈 MARKET ALERT
# ==========================================

if (
    LIVE_RATES["plastic"] >= 60.0
    or LIVE_RATES["raddi"] >= 40.0
):

    st.sidebar.markdown("""
    <div class="price-flash-green">

        📈 Bazar Up: Good Time to Sell!

        <br>

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

        ⚠️ Bazar Normal: Hold or Compare

        <br>

        <span style="font-size:12px; font-weight:normal;">
            (مارکیٹ مستحکم ہے)
        </span>

    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 💰 DISPLAY RATES
# ==========================================

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
# 🔐 GEMINI API KEY FROM STREAMLIT SECRETS
# ==========================================

st.sidebar.divider()

st.sidebar.subheader(
    "🧠 Google AI"
)

try:

    gemini_api_key = st.secrets["GEMINI_API_KEY"]

except Exception:

    gemini_api_key = ""

    st.sidebar.error(
        "Gemini API key is missing from Secrets."
    )


# ==========================================
# 💾 SESSION DATABASE
# ==========================================

if "global_db" not in st.session_state:

    st.session_state.global_db = {}


if "last_result" not in st.session_state:

    st.session_state.last_result = None


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

    # ==========================================
    # CREATE HOUSEHOLD
    # ==========================================

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


    my_house = st.session_state.global_db[
        household_code
    ]


    # ==========================================
    # 📱 MAIN COLUMNS
    # ==========================================

    left_col, right_col = st.columns(2)


    # ==========================================
    # 👨‍👩‍👧 FAMILY MEMBERS
    # ==========================================

    with left_col:

        st.write(
            "### 📸 AI Intelligent Waste Scanner"
        )

        st.markdown(
            "#### **1. Register Family Members**"
        )


        new_member = st.text_input(
            "Add a family member's name:",
            placeholder="Type name here (e.g., Ali, Aisha)..."
        )


        if st.button("✨ Register Member"):

            if new_member:

                clean_name = new_member.strip()

                if (
                    clean_name
                    and clean_name not in my_house["scores"]
                ):

                    my_house["scores"][clean_name] = 0

                    st.toast(
                        f"Profile for '{clean_name}' "
                        f"created successfully! 🎉"
                    )

                    st.rerun()

                else:

                    st.warning(
                        "This member already exists."
                    )


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
    # 🧠 GEMINI AI FUNCTION
    # ==========================================

    def analyze_image_with_gemini(
        uploaded_file,
        api_key
    ):

        # ------------------------------------------
        # CHECK API KEY
        # ------------------------------------------

        if not api_key:

            return (
                "error",
                0.0,
                0.0,
                "⚠️ Gemini API key is missing. "
                "Please add GEMINI_API_KEY in Streamlit Secrets."
            )


        try:

            # --------------------------------------
            # CONFIGURE GEMINI
            # --------------------------------------

            genai.configure(
                api_key=api_key
            )


            # --------------------------------------
            # USE GEMINI 2.5 FLASH
            # --------------------------------------

            model = genai.GenerativeModel(
                "gemini-2.5-flash"
            )


            # --------------------------------------
            # OPEN IMAGE
            # --------------------------------------

            img = Image.open(
                uploaded_file
            )


            # --------------------------------------
            # STRONG CLASSIFICATION PROMPT
            # --------------------------------------

            prompt = """

You are an expert waste classification AI.

Look carefully at the uploaded image.

Identify the MAIN waste item visible in the image.

You MUST choose exactly ONE category.

CATEGORY RULES:

plastic =
plastic bottles,
plastic containers,
plastic cups,
plastic packaging,
plastic cans,
PET bottles.

raddi =
newspapers,
books,
paper,
cardboard,
cartons.

textile =
clothes,
shirts,
pants,
fabric,
cloth,
rags,
bedsheets.

kitchen =
food,
fruit peels,
vegetable peels,
tea leaves,
food scraps,
organic waste.

landfill =
diapers,
dirty wrappers,
non-recyclable waste,
mixed garbage.

IMPORTANT RULE:

If you see a normal plastic drinking bottle,
YOU MUST classify it as "plastic".

A plastic bottle is NEVER "raddi".

Return ONLY this exact format:

category|tip

Examples:

plastic|🧴 Plastic bottle ko saaf aur dry karke kabari ko dein.

raddi|📦 Raddi ko dry rakh kar kabari ko dein.

textile|👕 Purane kapray alag jama karein.

kitchen|🍌 Kitchen waste ko compost mein use karein.

landfill|🗑️ Is waste ko general waste mein dispose karein.

Do not return anything else.

"""


            # --------------------------------------
            # SEND IMAGE TO GEMINI
            # --------------------------------------

            response = model.generate_content(
                [
                    prompt,
                    img
                ]
            )


            # --------------------------------------
            # GET AI RESPONSE
            # --------------------------------------

            ai_output = response.text.strip().lower()


            # Remove markdown if Gemini adds it
            ai_output = ai_output.replace(
                "```",
                ""
            ).strip()


            # --------------------------------------
            # VALID CATEGORIES
            # --------------------------------------

            categories = [
                "plastic",
                "raddi",
                "textile",
                "kitchen",
                "landfill"
            ]


            key = None
            tip = ""


            # --------------------------------------
            # READ category|tip
            # --------------------------------------

            if "|" in ai_output:

                parts = ai_output.split(
                    "|",
                    1
                )

                possible_category = (
                    parts[0]
                    .strip()
                )

                possible_tip = (
                    parts[1]
                    .strip()
                )


                if possible_category in categories:

                    key = possible_category

                    tip = possible_tip


            # --------------------------------------
            # BACKUP CATEGORY DETECTION
            # --------------------------------------

            if key is None:

                first_word = (
                    ai_output
                    .split()
                )

                if first_word:

                    possible_category = (
                        first_word[0]
                        .strip()
                        .replace(
                            ":",
                            ""
                        )
                    )


                    if (
                        possible_category
                        in categories
                    ):

                        key = possible_category

                        tip = ai_output


            # --------------------------------------
            # AI DID NOT RETURN VALID CATEGORY
            # --------------------------------------

            if key is None:

                return (
                    "error",
                    0.0,
                    0.0,
                    "⚠️ AI could not identify this item. "
                    "Please upload a clearer photo."
                )


            # ======================================
            # 💰 CORRECT RATE FOR CATEGORY
            # ======================================

            if key == "plastic":

                rate = LIVE_RATES[
                    "plastic"
                ]


            elif key == "raddi":

                rate = LIVE_RATES[
                    "raddi"
                ]


            elif key == "textile":

                rate = LIVE_RATES[
                    "textile"
                ]


            elif key == "kitchen":

                rate = 0.0


            elif key == "landfill":

                rate = 0.0


            else:

                rate = 0.0


            # ======================================
            # ⭐ POINTS
            # ======================================

            points = 5.0


            # ======================================
            # RETURN RESULT
            # ======================================

            return (
                key,
                rate,
                points,
                tip
            )


        except Exception as e:

            return (
                "error",
                0.0,
                0.0,
                f"⚠️ AI error: {str(e)}"
            )


    # ==========================================
    # 📸 UPLOAD WASTE IMAGE
    # ==========================================

    with left_col:

        st.markdown(
            "#### **2. Upload Waste Item**"
        )


        uploaded_file = st.file_uploader(
            "Upload a photo of your waste item:",
            type=[
                "jpg",
                "jpeg",
                "png"
            ]
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

                        (
                            category,
                            rate,
                            points,
                            tip
                        ) = analyze_image_with_gemini(
                            uploaded_file,
                            gemini_api_key
                        )


                    # ==================================
                    # SAVE RESULT
                    # ==================================

                    st.session_state.last_result = {

                        "category": category,

                        "rate": rate,

                        "points": points,

                        "tip": tip,

                        "member": active_member

                    }


                    # ==================================
                    # ONLY ADD POINTS IF AI SUCCESSFUL
                    # ==================================

                    if category != "error":

                        my_house[
                            "scores"
                        ][active_member] += points


                        # ------------------------------
                        # SAVE HISTORY
                        # ------------------------------

                        my_house[
                            "history"
                        ].append({

                            "member": active_member,

                            "category": category,

                            "rate": rate,

                            "points": points

                        })


                        st.success(
                            "✅ Waste analyzed successfully!"
                        )

                    else:

                        st.error(
                            tip
                        )


    # ==========================================
    # 📊 DASHBOARD
    # ==========================================

    with right_col:

        st.write(
            "### 📊 Household Dashboard"
        )


        result = st.session_state.last_result


        # ==========================================
        # SHOW RESULT
        # ==========================================

        if result is not None:

            if result["category"] == "error":

                st.error(
                    result["tip"]
                )

            else:

                category_display = (
                    result["category"]
                    .upper()
                )


                st.markdown(
                    f"""
                    <div class="illustration-box">

                        <h2>
                            ♻️ {category_display}
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
        # 🏆 FAMILY SCORES
        # ==========================================

        st.markdown(
            "#### 🏆 Family Member Scores"
        )


        if my_house["scores"]:

            for (
                member,
                score
            ) in my_house["scores"].items():

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
        # 📜 WASTE HISTORY
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
    # 🏪 KABARI DEALERS
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
                    📍 <b>Location:</b>
                    {dealer['loc']}
                </p>

                <p>
                    ♻️ <b>Accepts:</b>
                    {dealer['items']}
                </p>

                <p>
                    📞 <b>Phone:</b>
                    {dealer['phone']}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )
