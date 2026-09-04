import os
import json
import urllib.parse
from datetime import datetime, timezone

import streamlit as st
from PIL import Image
from supabase import create_client, Client
from google import genai


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Trash to Treasure",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLING
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background: #f6faf7;
    }

    .hero {
        padding: 2.2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #087f5b, #20a46b);
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        font-size: 3rem;
        margin: 0;
    }

    .hero p {
        font-size: 1.1rem;
        margin-top: .5rem;
    }

    .card {
        padding: 1.2rem;
        border-radius: 18px;
        background: white;
        border: 1px solid #e4ebe7;
        margin: .5rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,.04);
    }

    .big-value {
        font-size: 2.1rem;
        font-weight: 800;
    }

    .muted {
        color: #66736d;
    }

    .success-pill {
        display: inline-block;
        padding: .3rem .7rem;
        border-radius: 999px;
        background: #e7f7ef;
        color: #087f5b;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SECRETS / CLIENT
# ============================================================
def secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_KEY")
GEMINI_API_KEY = secret("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY "
        "to Streamlit Cloud Secrets."
    )
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

if "session" not in st.session_state:
    st.session_state.session = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None


# ============================================================
# HELPERS
# ============================================================
def current_user():
    return st.session_state.get("user")


def user_id():
    user = current_user()
    return str(user.id) if user else None


def money(value):
    return f"Rs. {float(value):,.0f}"


def whatsapp_link(phone, material, quantity, area="Chashma/Mianwali"):
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    message = (
        f"Hello, I have approximately {quantity:g} kg of {material} scrap "
        f"available in {area}. Do you purchase this material? "
        f"Please share your current buying rate."
    )
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"


def upload_image(file, uid):
    """Upload image into private bucket under user UUID folder."""
    bucket = "scrap-images"
    extension = file.name.split(".")[-1].lower()
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}.{extension}"
    path = f"{uid}/{filename}"

    data = file.getvalue()

    supabase.storage.from_(bucket).upload(
        path,
        data,
        {"content-type": file.type, "upsert": False},
    )
    return path


def analyze_image(image):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = """
You are the material-identification AI for Trash to Treasure,
a Pakistan-focused household scrap valuation application.

Analyze the photograph and choose the SINGLE most likely category
from this exact list:

Iron / Steel
Aluminium
Copper
Brass
Stainless Steel
Cardboard
Newspaper
Mixed Paper
PET Plastic
Hard Plastic
Mixed Plastic
E-Waste
Cotton Cloth
Denim
Mixed Textile
Textile Rags
Battery
Other / Unknown

For clothing/textiles, identify the closest category.
Do not estimate weight from the photograph.

Return ONLY valid JSON:

{
  "material": "Copper",
  "category": "Copper",
  "confidence": 94,
  "condition": "Clean",
  "reason": "Short explanation"
}

Confidence must be a number from 0 to 100.
Condition must be one of: Clean, Mixed, Dirty, Damaged, Unknown.
"""

    response = client.models.generate_content(
       gemini-3.6-flash
        contents=[image, prompt],
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    result = json.loads(text)

    allowed = {
        "Iron / Steel", "Aluminium", "Copper", "Brass",
        "Stainless Steel", "Cardboard", "Newspaper", "Mixed Paper",
        "PET Plastic", "Hard Plastic", "Mixed Plastic", "E-Waste",
        "Cotton Cloth", "Denim", "Mixed Textile", "Textile Rags",
        "Battery", "Other / Unknown",
    }

    if result.get("category") not in allowed:
        result["category"] = "Other / Unknown"

    result["confidence"] = max(
        0, min(100, int(float(result.get("confidence", 0))))
    )

    return result


def fetch_rates():
    response = (
        supabase.table("scrap_rates")
        .select("*")
        .eq("active", True)
        .order("material")
        .execute()
    )
    return response.data or []


def fetch_dealers(material=None):
    query = (
        supabase.table("dealers")
        .select("*")
        .eq("active", True)
        .eq("verified", True)
    )

    response = query.order("name").execute()
    dealers = response.data or []

    if material and material != "All Materials":
        dealers = [
            d for d in dealers
            if material in (d.get("materials") or [])
        ]

    return dealers


def fetch_history():
    response = (
        supabase.table("scrap_records")
        .select("*")
        .eq("user_id", user_id())
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def save_record(
    image_path,
    result,
    quantity,
    rate,
    estimated_value,
):
    payload = {
        "user_id": user_id(),
        "image_path": image_path,
        "material": result.get("material"),
        "category": result.get("category"),
        "confidence": result.get("confidence"),
        "condition": result.get("condition"),
        "quantity": float(quantity),
        "unit": "kg",
        "rate": float(rate) if rate is not None else None,
        "estimated_value": (
            float(estimated_value) if estimated_value is not None else None
        ),
    }

    supabase.table("scrap_records").insert(payload).execute()


# ============================================================
# AUTHENTICATION
# ============================================================
def auth_page():
    st.markdown(
        """
        <div class="hero">
            <h1>♻️ Trash to Treasure</h1>
            <p>See it. Identify it. Value it. Sell it.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
                st.session_state.session = response.session
                st.session_state.user = response.user
                st.success("Login successful.")
                st.rerun()
            except Exception as exc:
                st.error(f"Login failed: {exc}")

    with tab2:
        with st.form("signup_form"):
            name = st.text_input("Name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )
            confirm = st.text_input(
                "Confirm Password",
                type="password",
            )
            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if submitted:
            if not name.strip():
                st.error("Please enter your name.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Password must contain at least 8 characters.")
            else:
                try:
                    response = supabase.auth.sign_up(
                        {
                            "email": email.strip(),
                            "password": password,
                            "options": {
                                "data": {
                                    "full_name": name.strip()
                                }
                            },
                        }
                    )

                    if response.session:
                        st.session_state.session = response.session
                        st.session_state.user = response.user
                        st.success("Account created.")
                        st.rerun()
                    else:
                        st.success(
                            "Account created. Check your email to confirm "
                            "your account, then log in."
                        )
                except Exception as exc:
                    st.error(f"Sign-up failed: {exc}")


# ============================================================
# STOP HERE IF NOT LOGGED IN
# ============================================================
if not current_user():
    auth_page()
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================
user = current_user()

with st.sidebar:
    st.markdown("## ♻️ Trash to Treasure")
    st.caption(user.email)

    st.divider()

    page = st.radio(
        "Menu",
        [
            "🏠 Dashboard",
            "📸 Scan Scrap",
            "📊 My Scrap History",
            "📍 Find Dealers",
        ],
    )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.user = None
        st.session_state.session = None
        st.session_state.analysis = None
        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================
if page == "🏠 Dashboard":
    st.markdown(
        f"""
        <div class="hero">
            <h1>♻️ Trash to Treasure</h1>
            <p>Welcome back! Turn your scrap into value.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history = fetch_history()

    total_value = sum(
        float(x.get("estimated_value") or 0)
        for x in history
    )

    total_weight = sum(
        float(x.get("quantity") or 0)
        for x in history
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("My Scrap Records", len(history))

    with c2:
        st.metric("Total Weight", f"{total_weight:,.1f} kg")

    with c3:
        st.metric("Estimated Value", money(total_value))

    st.markdown("## 🌱 What can you recycle?")

    cards = [
        ("🔩", "Metals", "Iron, aluminium, copper, brass"),
        ("📦", "Paper", "Cardboard, newspaper, paper"),
        ("🧴", "Plastic", "PET, hard and mixed plastic"),
        ("💻", "E-Waste", "Electronics and cables"),
        ("👕", "Textiles", "Torn clothes, denim and rags"),
        ("🔋", "Batteries", "Battery waste"),
    ]

    cols = st.columns(3)

    for i, (icon, title, text) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="card">
                    <h3>{icon} {title}</h3>
                    <p class="muted">{text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.info(
        "Tip: Take a clear photo with good lighting and show the whole item."
    )


# ============================================================
# SCAN
# ============================================================
elif page == "📸 Scan Scrap":
    st.title("📸 Scan Your Scrap")

    uploaded = st.file_uploader(
        "Take or upload a clear photograph",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded:
        image = Image.open(uploaded).convert("RGB")

        left, right = st.columns([1, 1])

        with left:
            st.image(image, caption="Your Scrap", use_container_width=True)

        with right:
            st.markdown("### 🤖 AI Identification")

            if st.button(
                "Analyze with AI",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("AI is analyzing your scrap..."):
                        st.session_state.analysis = analyze_image(image)
                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")

        result = st.session_state.analysis

        if result:
            st.divider()

            st.markdown("## 🔍 Result")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Material",
                    result.get("material", "Unknown"),
                )

            with c2:
                st.metric(
                    "Category",
                    result.get("category", "Unknown"),
                )

            with c3:
                st.metric(
                    "Confidence",
                    f"{result.get('confidence', 0)}%",
                )

            st.write(
                f"**Condition:** {result.get('condition', 'Unknown')}"
            )
            st.write(result.get("reason", ""))

            st.divider()

            st.markdown("## ⚖️ Quantity")

            quantity = st.number_input(
                "Enter approximate weight",
                min_value=0.1,
                value=1.0,
                step=0.5,
                help="Use a weighing scale for the most accurate valuation.",
            )

            category = result.get("category")
            rates = fetch_rates()

            matching_rate = next(
                (
                    r for r in rates
                    if r["material"] == category
                ),
                None,
            )

            if matching_rate:
                rate = float(matching_rate["rate"])
                estimated_value = quantity * rate

                st.markdown(
                    f"""
                    <div class="card">
                        <div class="muted">
                            Estimated current market value
                        </div>
                        <div class="big-value">
                            {money(estimated_value)}
                        </div>
                        <p>
                            {quantity:g} kg × {money(rate)}/kg
                        </p>
                        <small>
                            Rate updated:
                            {matching_rate.get("updated_at", "N/A")}
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.warning(
                    "Estimated value only. Actual dealer prices may vary "
                    "with quality, quantity and local market conditions."
                )
            else:
                rate = None
                estimated_value = None
                st.info(
                    "No verified current rate is available for this category. "
                    "You can request a dealer quotation."
                )

            if st.button(
                "💾 Save to My Scrap History",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Saving your private record..."):
                        image_path = upload_image(uploaded, user_id())

                        save_record(
                            image_path,
                            result,
                            quantity,
                            rate,
                            estimated_value,
                        )

                    st.success(
                        "Saved securely to your personal Scrap History."
                    )
                except Exception as exc:
                    st.error(f"Could not save record: {exc}")

            st.divider()

            st.markdown("## 📍 Relevant Local Dealers")

            dealers = fetch_dealers(category)

            if dealers:
                for dealer in dealers:
                    link = whatsapp_link(
                        dealer["phone"],
                        result.get("material", category),
                        quantity,
                    )

                    st.markdown(
                        f"""
                        <div class="card">
                            <h3>♻️ {dealer["name"]}</h3>
                            <p>📍 {dealer.get("area", "Mianwali")}</p>
                            <p>
                                <b>Buys:</b>
                                {", ".join(dealer.get("materials") or [])}
                            </p>
                            <p>📞 {dealer["phone"]}</p>
                            <a href="{link}" target="_blank">
                                🟢 Contact on WhatsApp
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info(
                    "No verified local dealer is currently listed for "
                    "this material."
                )


# ============================================================
# HISTORY
# ============================================================
elif page == "📊 My Scrap History":
    st.title("📊 My Scrap History")

    records = fetch_history()

    if not records:
        st.info("You have not saved any scrap records yet.")
    else:
        total = sum(
            float(r.get("estimated_value") or 0)
            for r in records
        )

        st.metric("My estimated total value", money(total))

        for record in records:
            title = (
                f"{record.get('material', 'Unknown')} — "
                f"{record.get('quantity', 0)} kg"
            )

            with st.expander(title):
                st.write(
                    f"**Category:** {record.get('category', 'Unknown')}"
                )
                st.write(
                    f"**AI confidence:** "
                    f"{record.get('confidence', 0)}%"
                )
                st.write(
                    f"**Condition:** "
                    f"{record.get('condition', 'Unknown')}"
                )
                st.write(
                    f"**Quantity:** "
                    f"{record.get('quantity', 0)} kg"
                )

                if record.get("rate") is not None:
                    st.write(
                        f"**Rate used:** {money(record['rate'])}/kg"
                    )
                    st.write(
                        f"**Estimated value:** "
                        f"{money(record['estimated_value'])}"
                    )
                else:
                    st.write("**Value:** Dealer quotation required")

                st.caption(
                    f"Saved: {record.get('created_at', '')}"
                )


# ============================================================
# DEALERS
# ============================================================
elif page == "📍 Find Dealers":
    st.title("📍 Chashma & Mianwali Scrap Dealers")

    rates = fetch_rates()
    material_options = ["All Materials"] + [
        r["material"] for r in rates
    ]

    material = st.selectbox(
        "Show dealers for",
        material_options,
    )

    dealers = fetch_dealers(material)

    if not dealers:
        st.info(
            "No verified dealer is currently listed for this material."
        )
    else:
        for dealer in dealers:
            link = whatsapp_link(
                dealer["phone"],
                material if material != "All Materials" else "scrap",
                1,
            )

            st.markdown(
                f"""
                <div class="card">
                    <h3>♻️ {dealer["name"]}</h3>
                    <p>📍 {dealer.get("area", "Mianwali")}</p>
                    <p>
                        <b>Materials:</b>
                        {", ".join(dealer.get("materials") or [])}
                    </p>
                    <p>📞 {dealer["phone"]}</p>
                    <a href="{link}" target="_blank">
                        🟢 WhatsApp
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "♻️ Trash to Treasure | AI scrap identification and local recycling assistant"
)
