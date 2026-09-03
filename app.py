import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import quote
from google import genai
import base64


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

.price-box {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 20px;
    border-left: 6px solid #4caf50;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

.sidebar-rate-text {
    font-size: 14px;
    margin: 5px 0;
    padding: 8px;
    background-color: #ffffff;
    border-radius: 6px;
    border: 1px solid #eee;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 💎 3. BRANDING
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
# 📦 4. DEALERS
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
# 📈 5. SCRAP RATES
# ==========================================

@st.cache_data(ttl=3600)
def fetch_live_pakistan_rates():

    url = "https://getscraprate.com"

    defaults = {
        "plastic": 50.00,
        "raddi": 50.00,
        "cardboard": 30.98,
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

                    parts = text_data.split(
                        item_name
                    )

                    for part in parts[1:]:

                        words = part.split()

                        for word in words:

                            clean_word = "".join(
                                c for c in word
                                if c.isdigit() or c == "."
                            )

                            if clean_word:

                                try:

                                    val = float(
                                        clean_word
                                    )

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
    "📈 Today's Punjab Bazar"
)


st.sidebar.markdown(f"""
<div class="sidebar-rate-text">
🍾 <b>Plastic:</b>
Rs. {LIVE_RATES['plastic']:.2f} / kg
</div>

<div class="sidebar-rate-text">
📦 <b>Raddi:</b>
Rs. {LIVE_RATES['raddi']:.2f} / kg
</div>

<div class="sidebar-rate-text">
🗂️ <b>Cardboard:</b>
Rs. {LIVE_RATES['cardboard']:.2f} / kg
</div>

<div class="sidebar-rate-text">
🧵 <b>Textile:</b>
Rs. {LIVE_RATES['textile']:.2f} / kg
</div>
""", unsafe_allow_html=True)


# ==========================================
# 🔐 7. GEMINI SECRET
# ==========================================

try:

    gemini_api_key = st.secrets[
        "GEMINI_API_KEY"
    ]

except Exception:

    gemini_api_key = ""

    st.sidebar.error(
        "Gemini API key is missing."
    )


# ==========================================
# 💾 8. SESSION DATABASE
# ==========================================

if "global_db" not in st.session_state:

    st.session_state.global_db = {}


if "last_result" not in st.session_state:

    st.session_state.last_result = None


# ==========================================
# 🔐 9. HOUSEHOLD LOGIN
# ==========================================

if not household_code:

    st.warning(
        "👋 Please enter your Household Code "
        "in the sidebar to continue."
    )

    st.info(
        "💡 You can create any unique code, "
        "for example: khan-house-chashma"
    )

else:

    if household_code not in st.session_state.global_db:

        st.session_state.global_db[
            household_code
        ] = {
            "scores": {},
            "history": []
        }

        st.sidebar.success(
            "🆕 New private household created!"
        )

    else:

        st.sidebar.success(
            "🔓 Household unlocked!"
        )


    my_house = st.session_state.global_db[
        household_code
    ]


    # ==========================================
    # 👨‍👩‍👧 FAMILY MEMBER
    # ==========================================

    left_col, right_col = st.columns(2)


    with left_col:

        st.write(
            "### 📸 AI Intelligent Waste Scanner"
        )

        st.markdown(
            "#### 1. Register Family Member"
        )


        new_member = st.text_input(
            "Family member name:",
            placeholder="e.g. Ali"
        )


        if st.button(
            "✨ Register Member"
        ):

            if new_member:

                clean_name = (
                    new_member.strip()
                )

                if (
                    clean_name
                    and clean_name
                    not in my_house["scores"]
                ):

                    my_house[
                        "scores"
                    ][clean_name] = 0

                    st.success(
                        f"Profile created for {clean_name}!"
                    )

                    st.rerun()


        if my_house["scores"]:

            active_member = st.selectbox(
                "Who is scanning?",
                list(
                    my_house["scores"].keys()
                )
            )

        else:

            active_member = None

            st.warning(
                "Register a family member first."
            )


    # ==========================================
    # 🤖 10. GEMINI ANALYSIS FUNCTION
    # ==========================================

    def analyze_image_with_gemini(
        picture,
        api_key
    ):

        if not api_key:

            return (
                "error",
                0.0,
                0.0,
                "Gemini API key is missing."
            )


        try:

            # ------------------------------
            # CREATE GEMINI CLIENT
            # ------------------------------

            client = genai.Client(
                api_key=api_key
            )


            # ------------------------------
            # IMAGE DATA
            # ------------------------------

            image_bytes = picture.getvalue()

            image_b64 = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            mime_type = picture.type


            # ------------------------------
            # AI PROMPT
            # ------------------------------

            prompt = """

You are an expert waste classification assistant.

Look carefully at the photograph.

Identify the MAIN waste material.

Choose exactly ONE category:

plastic
raddi
textile
kitchen
landfill

CATEGORY RULES:

plastic =
plastic bottles,
PET bottles,
plastic containers,
plastic cups,
plastic packaging.

raddi =
newspaper,
books,
paper,
cardboard,
cartons.

textile =
clothes,
fabric,
cloth,
rags,
bedsheets.

kitchen =
food,
fruit peels,
vegetable peels,
tea leaves,
organic waste.

landfill =
diapers,
dirty wrappers,
non-recyclable garbage.

IMPORTANT:

A plastic drinking bottle MUST be classified as plastic.

Never classify a plastic bottle as raddi.

Also visually estimate the approximate weight of the visible material.

IMPORTANT WEIGHT RULE:

Weight from a photograph is ONLY a rough visual estimate.
Do not pretend it is an exact measurement.

Return ONLY this format:

category|estimated_weight_kg|tip

Examples:

plastic|0.05|🧴 Plastic bottle ko saaf aur dry karke kabari ko dein.

raddi|1.50|📦 Raddi ko dry rakh kar kabari ko dein.

textile|2.00|👕 Purane kapray alag jama karein.

kitchen|0.50|🍌 Kitchen waste ko compost mein use karein.

landfill|0.30|🗑️ Is waste ko general waste mein dispose karein.

The estimated weight must be a number in kilograms.

Do not write anything else.

"""


            # ------------------------------
            # GEMINI REQUEST
            # ------------------------------

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ]
            )


            # ------------------------------
            # GET RESPONSE
            # ------------------------------

            ai_output = (
                response.text
                .strip()
                .lower()
            )


            ai_output = (
                ai_output
                .replace("```", "")
                .strip()
            )


            # ------------------------------
            # PARSE RESULT
            # ------------------------------

            parts = ai_output.split(
                "|",
                2
            )


            if len(parts) < 3:

                return (
                    "error",
                    0.0,
                    0.0,
                    "AI returned an invalid response."
                )


            category = (
                parts[0]
                .strip()
            )


            weight_text = (
                parts[1]
                .strip()
            )


            tip = (
                parts[2]
                .strip()
            )


            valid_categories = [
                "plastic",
                "raddi",
                "textile",
                "kitchen",
                "landfill"
            ]


            if category not in valid_categories:

                return (
                    "error",
                    0.0,
                    0.0,
                    "AI could not identify the material."
                )


            # ------------------------------
            # WEIGHT
            # ------------------------------

            try:

                weight = float(
                    weight_text
                )

            except ValueError:

                weight = 0.0


            # Keep weight sensible
            if weight < 0:

                weight = 0.0

            if weight > 1000:

                weight = 1000.0


            # ------------------------------
            # RATE
            # ------------------------------

            if category == "plastic":

                rate = LIVE_RATES[
                    "plastic"
                ]

            elif category == "raddi":

                rate = LIVE_RATES[
                    "raddi"
                ]

            elif category == "textile":

                rate = LIVE_RATES[
                    "textile"
                ]

            elif category == "kitchen":

                rate = 0.0

            else:

                rate = 0.0


            # ------------------------------
            # POINTS
            # ------------------------------

            points = 5.0


            return (
                category,
                weight,
                rate,
                points,
                tip
            )


        except Exception as e:

            return (
                "error",
                0.0,
                0.0,
                0.0,
                f"AI error: {str(e)}"
            )


    # ==========================================
    # 📷 11. CAMERA
    # ==========================================

    with left_col:

        st.markdown(
            "#### 2. 📷 Take a Picture"
        )

        st.caption(
            "Take a clear picture of the scrap material."
        )


        picture = st.camera_input(
            "📷 Open Camera",
            key="waste_camera",
            resolution="720p"
        )


        if picture is not None:

            st.image(
                picture,
                caption="Captured Waste",
                use_container_width=True
            )


            if active_member:

                analyze_button = st.button(
                    "🤖 Identify + Estimate Weight",
                    type="primary"
                )


                if analyze_button:

                    with st.spinner(
                        "🧠 AI is identifying the material..."
                    ):

                        result = (
                            analyze_image_with_gemini(
                                picture,
                                gemini_api_key
                            )
                        )


                    if result[0] == "error":

                        st.error(
                            result[-1]
                        )

                    else:

                        (
                            category,
                            estimated_weight,
                            rate,
                            points,
                            tip
                        ) = result


                        # Save temporary result
                        st.session_state.last_result = {

                            "category": category,

                            "estimated_weight":
                                estimated_weight,

                            "rate": rate,

                            "points": points,

                            "tip": tip,

                            "member":
                                active_member

                        }


                        st.success(
                            "✅ Material identified!"
                        )


    # ==========================================
    # 📊 12. RESULTS
    # ==========================================

    with right_col:

        st.write(
            "### 📊 Waste Result"
        )


        result = (
            st.session_state.last_result
        )


        if result is not None:

            category = result[
                "category"
            ]

            estimated_weight = result[
                "estimated_weight"
            ]

            rate = result[
                "rate"
            ]

            tip = result[
                "tip"
            ]


            # ==================================
            # CATEGORY
            # ==================================

            st.markdown(
                f"""
                <div class="illustration-box">

                    <h1>
                        ♻️ {category.upper()}
                    </h1>

                    <p>
                        {tip}
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # WEIGHT
            # ==================================

            st.markdown(
                "#### ⚖️ Weight"
            )

            st.info(
                "The AI weight is only a visual estimate. "
                "For the correct selling price, confirm the "
                "actual weight using a scale."
            )


            actual_weight = st.number_input(
                "Confirm / adjust weight (kg):",
                min_value=0.0,
                max_value=1000.0,
                value=float(
                    estimated_weight
                ),
                step=0.1,
                key="confirmed_weight"
            )


            # ==================================
            # RATE
            # ==================================

            if category == "plastic":

                rate = LIVE_RATES[
                    "plastic"
                ]

            elif category == "raddi":

                rate = LIVE_RATES[
                    "raddi"
                ]

            elif category == "textile":

                rate = LIVE_RATES[
                    "textile"
                ]

            else:

                rate = 0.0


            # ==================================
            # PRICE CALCULATION
            # ==================================

            total_price = (
                actual_weight * rate
            )


            st.markdown(
                f"""
                <div class="price-box">

                    <h3>
                        💰 Estimated Selling Price
                    </h3>

                    <h1>
                        Rs. {total_price:,.2f}
                    </h1>

                    <p>
                        {actual_weight:.2f} kg
                        ×
                        Rs. {rate:.2f}/kg
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # SAVE SALE
            # ==================================

            if st.button(
                "💾 Save This Scan"
            ):

                my_house[
                    "scores"
                ][result["member"]] += (
                    result["points"]
                )


                my_house[
                    "history"
                ].append({

                    "member":
                        result["member"],

                    "category":
                        category,

                    "weight_kg":
                        actual_weight,

                    "rate_per_kg":
                        rate,

                    "estimated_price":
                        total_price,

                    "points":
                        result["points"]

                })


                st.success(
                    "✅ Scan saved successfully!"
                )


            # ==================================
            # 🏪 DEALER DROPDOWN
            # ==================================

            st.markdown(
                "#### 🏪 Select Kabari Dealer"
            )


            dealer_names = [
                dealer["name"]
                for dealer in DEALERS
            ]


            selected_dealer_name = (
                st.selectbox(
                    "Choose a dealer:",
                    dealer_names
                )
            )


            selected_dealer = next(
                dealer
                for dealer in DEALERS
                if dealer["name"]
                == selected_dealer_name
            )


            st.markdown(
                f"""
                <div class="badge-box">

                    <h3>
                        🏪 {selected_dealer['name']}
                    </h3>

                    <p>
                        📍 {selected_dealer['loc']}
                    </p>

                    <p>
                        ♻️ {selected_dealer['items']}
                    </p>

                    <p>
                        📞 {selected_dealer['phone']}
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # 💬 WHATSAPP MESSAGE
            # ==================================

            whatsapp_message = (
                f"Assalam o Alaikum, "
                f"I have {actual_weight:.2f} kg of "
                f"{category} scrap. "
                f"The current rate shown by Trash to "
                f"Treasure PK is Rs. {rate:.2f}/kg. "
                f"Estimated total is Rs. "
                f"{total_price:.2f}. "
                f"Please confirm your buying rate."
            )


            whatsapp_url = (
                "https://wa.me/"
                + selected_dealer["phone"]
                + "?text="
                + quote(whatsapp_message)
            )


            st.link_button(
                "💬 Contact Dealer on WhatsApp",
                whatsapp_url,
                type="primary"
            )


        else:

            st.info(
                "📷 Take a picture to start."
            )


    # ==========================================
    # 🏆 13. FAMILY SCORES
    # ==========================================

    st.divider()

    st.subheader(
        "🏆 Family Member Scores"
    )


    if my_house["scores"]:

        for member, score in (
            my_house["scores"].items()
        ):

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
    # 📜 14. HISTORY
    # ==========================================

    st.subheader(
        "📜 Waste History"
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
            "No saved scans yet."
        )


    # ==========================================
    # 🏪 15. DEALER DIRECTORY
    # ==========================================

    st.divider()

    st.subheader(
        "🏪 Available Kabari Dealers"
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
