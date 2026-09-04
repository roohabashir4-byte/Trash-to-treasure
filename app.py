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
    .landing-nav { display:flex; justify-content:space-between; align-items:center; padding:.8rem 0 1rem; gap:1rem; }
    .brand { font-size:1.35rem; font-weight:800; color:#087f5b; }
    .tagline { color:#66736d; font-size:.95rem; }
    .landing-hero { padding:3.2rem 3rem; border-radius:28px; background:linear-gradient(135deg,#087f5b,#20a46b); color:white; margin:.5rem 0 1.5rem; }
    .landing-hero h1 { font-size:3.5rem; line-height:1.08; margin:.5rem 0 1rem; }
    .landing-hero p { max-width:760px; font-size:1.15rem; line-height:1.65; margin:0; }
    .eyebrow { font-size:.78rem; font-weight:800; letter-spacing:.12em; opacity:.9; }
    .flow-strip { display:flex; justify-content:space-between; gap:.5rem; padding:1rem; margin:1rem 0 1.3rem; border-radius:18px; background:white; border:1px solid #e4ebe7; }
    .flow-strip div { display:flex; align-items:center; gap:.45rem; font-size:.85rem; }
    .flow-strip b { display:inline-flex; width:28px; height:28px; align-items:center; justify-content:center; border-radius:50%; background:#e7f7ef; color:#087f5b; }
    .benefit-card,.auth-card,.mini-card { padding:1.25rem; border-radius:20px; background:white; border:1px solid #e4ebe7; margin:.5rem 0; box-shadow:0 4px 16px rgba(0,0,0,.04); }
    .benefit-card h3 { margin:.4rem 0; } .benefit-card p,.auth-card p,.mini-card p { color:#66736d; line-height:1.5; } .benefit-icon { font-size:1.8rem; } .auth-card { padding:1.6rem; }
    @media (max-width:800px) { .landing-hero{padding:2rem 1.4rem;} .landing-hero h1{font-size:2.3rem;} .flow-strip{flex-direction:column;} .landing-nav{flex-direction:column;align-items:flex-start;} }
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

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None


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
        model="gemini-3.6-flash",
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
# PROFESSIONAL PUBLIC LANDING PAGE
# ============================================================
def landing_page():
    # Remote public photos are used only for visual presentation.
    hero_image = "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=1200&q=85"
    step_images = [
        "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=700&q=80",
        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=700&q=80",
        "https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=700&q=80",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=700&q=80",
        "https://images.unsplash.com/photo-1528323273322-d81458248d40?w=700&q=80",
    ]

    # All HTML blocks below are intentionally self-contained.
    # This prevents Streamlit widgets from being placed inside open HTML
    # elements, which was causing the previous landing page to become
    # unclickable and display raw HTML.
    st.markdown(
        """
        <style>
        .tt-wrap { max-width:1240px; margin:0 auto; }
        .tt-nav {
            display:flex; align-items:center; justify-content:space-between;
            padding:8px 0 16px; border-bottom:1px solid #e7ece8;
            margin-bottom:18px;
        }
        .tt-brand { font-size:1.42rem; font-weight:850; color:#14231b; }
        .tt-brand span { color:#168447; }
        .tt-navlinks {
            display:flex; gap:24px; color:#405047; font-size:.9rem;
            font-weight:650;
        }
        .tt-hero-copy {
            padding:28px 0 8px;
        }
        .tt-pill {
            display:inline-block; padding:7px 12px; border-radius:999px;
            background:#e8f6eb; color:#167a42; font-size:.72rem;
            font-weight:800; letter-spacing:.08em;
        }
        .tt-title {
            font-size:clamp(2.7rem,5vw,4.5rem); line-height:1.02;
            letter-spacing:-.055em; color:#14231b; margin:18px 0 14px;
        }
        .tt-title-green { color:#168447; }
        .tt-lead {
            color:#526159; font-size:1.08rem; line-height:1.65;
            max-width:650px;
        }
        .tt-trust {
            display:flex; flex-wrap:wrap; gap:20px; margin:12px 0 0;
            color:#405047; font-size:.84rem; font-weight:650;
        }
        .tt-visual {
            border-radius:28px; padding:12px; background:#eef7ee;
            box-shadow:0 18px 45px rgba(20,70,40,.13);
        }
        .tt-visual img {
            width:100%; height:380px; object-fit:cover;
            border-radius:22px;
        }
        .tt-phone-card {
            background:white; border:1px solid #e1e9e2;
            border-radius:18px; padding:14px; margin-top:-86px;
            margin-left:35px; margin-right:35px; position:relative;
            box-shadow:0 12px 30px rgba(0,0,0,.13);
        }
        .tt-phone-card h3 { margin:0 0 4px; color:#17251d; }
        .tt-price { color:#128344; font-size:1.35rem; font-weight:850; }
        .tt-section { padding:54px 0 5px; }
        .tt-kicker {
            color:#168447; font-weight:800; font-size:.76rem;
            letter-spacing:.08em; text-align:center;
        }
        .tt-section h2 {
            text-align:center; color:#14231b; font-size:2.25rem;
            letter-spacing:-.04em; margin:7px 0;
        }
        .tt-subtitle {
            text-align:center; color:#6a766f; margin-bottom:24px;
        }
        .tt-step-card {
            background:#fff; border:1px solid #e1e9e2; border-radius:18px;
            overflow:hidden; box-shadow:0 5px 18px rgba(20,60,35,.06);
        }
        .tt-step-card img {
            width:100%; height:145px; object-fit:cover; display:block;
        }
        .tt-step-body { padding:12px 13px 16px; }
        .tt-step-number {
            width:29px; height:29px; border-radius:50%; background:#168447;
            color:#fff; display:flex; align-items:center;
            justify-content:center; font-weight:800; margin-bottom:8px;
        }
        .tt-step-body h3 { margin:0 0 5px; color:#17251d; font-size:1rem; }
        .tt-step-body p { margin:0; color:#6a766f; font-size:.83rem; line-height:1.45; }
        .tt-benefit {
            background:#f3f8f1; border:1px solid #e0eadf; border-radius:20px;
            padding:20px; min-height:170px;
        }
        .tt-benefit-icon { font-size:2rem; }
        .tt-benefit h3 { color:#17251d; margin:8px 0 5px; }
        .tt-benefit p { color:#68756e; line-height:1.5; margin:0; }
        .tt-impact {
            margin-top:52px; padding:38px; border-radius:27px;
            background:linear-gradient(135deg,#0d6337,#168447); color:white;
        }
        .tt-impact h2 { color:white; text-align:left; margin:0 0 8px; }
        .tt-impact p { line-height:1.6; opacity:.92; }
        .tt-stat {
            text-align:center; background:rgba(255,255,255,.10);
            border:1px solid rgba(255,255,255,.18); border-radius:16px;
            padding:15px;
        }
        .tt-stat strong { display:block; font-size:1.65rem; }
        .tt-stat span { font-size:.78rem; opacity:.88; }
        .tt-quote {
            margin-top:18px; background:white; color:#26352c;
            padding:16px 18px; border-radius:17px;
        }
        .tt-footer {
            padding:25px 0 8px; color:#6a766f; font-size:.83rem;
            display:flex; justify-content:space-between; gap:18px;
        }
        @media (max-width:900px) {
            .tt-navlinks { display:none; }
            .tt-visual img { height:300px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Navigation is visual; the two actual actions are Streamlit buttons
    # below, so they remain fully clickable and reliable.
    st.markdown(
        """
        <div class="tt-wrap">
          <div class="tt-nav">
            <div class="tt-brand">♻️ Trash to <span>Treasure</span></div>
            <div class="tt-navlinks">
              <span>How It Works</span>
              <span>Why Use Us</span>
              <span>For Dealers</span>
              <span>FAQ</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.12, .88], gap="large")

    with left:
        st.markdown(
            """
            <div class="tt-hero-copy">
              <div class="tt-pill">SMART SCRAP • LOCAL VALUE • EASY SELLING</div>
              <div class="tt-title">
                Don't throw it away.<br>
                <span class="tt-title-green">Find out what it's worth.</span>
              </div>
              <div class="tt-lead">
                Identify your scrap, get an estimated value, and connect with
                verified buyers near you — all from one simple app.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        a, b = st.columns([1.15, .65])
        with a:
            if st.button("📷  Start Now — It's Free", type="primary",
                         use_container_width=True, key="landing_start"):
                st.session_state.auth_mode = "login"
                st.rerun()
        with b:
            if st.button("♙  Login", use_container_width=True,
                         key="landing_login"):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown(
            """
            <div class="tt-trust">
              <span>🛡️ Safe & Private</span>
              <span>📍 Local Buyers</span>
              <span>✓ Verified Dealers</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="tt-visual">', unsafe_allow_html=True)
        st.image(hero_image, use_container_width=True)
        st.markdown(
            """
            <div class="tt-phone-card">
              <h3>♻️ Copper Scrap</h3>
              <div style="font-size:.76rem;color:#718078">Estimated value</div>
              <div class="tt-price">Rs. 3,250</div>
              <div style="font-size:.72rem;color:#718078">5 kg × available rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="tt-wrap tt-section">
          <div class="tt-kicker">🌿 SIMPLE FROM START TO SALE</div>
          <h2>How It Works</h2>
          <div class="tt-subtitle">Five simple steps to turn unwanted stuff into treasure.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5, gap="small")
    step_data = [
        ("Take a Picture", "Snap a clear photo of your scrap.", step_images[0]),
        ("We Identify It", "AI identifies the likely material.", step_images[1]),
        ("Add Weight", "Enter your measured weight.", step_images[2]),
        ("See Your Value", "Get an estimate from the available rate.", step_images[3]),
        ("Find a Buyer", "Connect with a suitable verified dealer.", step_images[4]),
    ]
    for i, (title, desc, img) in enumerate(step_data, 1):
        with cols[i - 1]:
            st.markdown('<div class="tt-step-card">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown(
                f"""
                <div class="tt-step-body">
                  <div class="tt-step-number">{i}</div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="tt-wrap tt-section">
          <div class="tt-kicker">♻️ MADE FOR REAL PEOPLE</div>
          <h2>Why Use Trash to Treasure?</h2>
          <div class="tt-subtitle">Less guessing. More value. A cleaner recycling journey.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bcols = st.columns(4, gap="small")
    benefits = [
        ("💰", "Make Money", "Find out what your unwanted materials may be worth."),
        ("🛡️", "Trusted Buyers", "See dealers that have been verified before recommendation."),
        ("📍", "Nearby & Convenient", "Our next upgrade will make buyer matching location-aware."),
        ("🌍", "Better for the Planet", "Keep useful materials in circulation instead of throwing them away."),
    ]
    for col, (icon, title, desc) in zip(bcols, benefits):
        with col:
            st.markdown(
                f"""
                <div class="tt-benefit">
                  <div class="tt-benefit-icon">{icon}</div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="tt-wrap">
          <div class="tt-impact">
            <h2>Small Action. Big Impact.</h2>
            <p>
              Every item that finds a better destination is one less useful
              material going straight to the waste stream.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            '<div class="tt-stat"><strong>AI</strong><span>Material Identification</span></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            '<div class="tt-stat"><strong>Rs.</strong><span>Estimated Value</span></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            '<div class="tt-stat"><strong>📍</strong><span>Local Buyer Matching</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="tt-wrap">
          <div class="tt-quote">
            ⭐⭐⭐⭐⭐<br>
            <b>“My old scrap may be worth more than I thought.”</b><br>
            <span style="color:#68756e">A future customer story from Mianwali.</span>
          </div>
          <div class="tt-footer">
            <div><b>♻️ Trash to Treasure</b><br>See it. Identify it. Value it. Sell it.</div>
            <div>Privacy • Terms • Contact</div>
            <div>© Trash to Treasure</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# AUTHENTICATION
# ============================================================
def auth_page(mode="login"):
    st.markdown("""
    <div class="hero"><h1>♻️ Trash to Treasure</h1><p>See it. Identify it. Value it. Sell it.</p></div>
    """,unsafe_allow_html=True)
    if st.button("← Back to Introduction"):
        st.session_state.auth_mode=None; st.rerun()
    tab1,tab2=st.tabs(["🔐 Sign In","📝 Create Account"])
    with tab1:
        with st.form("login_form"):
            email=st.text_input("Email"); password=st.text_input("Password",type="password")
            submitted=st.form_submit_button("Sign In",type="primary",use_container_width=True)
        if submitted:
            try:
                response=supabase.auth.sign_in_with_password({"email":email.strip(),"password":password})
                st.session_state.session=response.session; st.session_state.user=response.user; st.session_state.auth_mode=None; st.success("Login successful."); st.rerun()
            except Exception as exc: st.error(f"Login failed: {exc}")
    with tab2:
        with st.form("signup_form"):
            name=st.text_input("Name"); email=st.text_input("Email",key="signup_email"); password=st.text_input("Password",type="password",key="signup_password"); confirm=st.text_input("Confirm Password",type="password")
            submitted=st.form_submit_button("Create Account",use_container_width=True)
        if submitted:
            if not name.strip(): st.error("Please enter your name.")
            elif password!=confirm: st.error("Passwords do not match.")
            elif len(password)<8: st.error("Password must contain at least 8 characters.")
            else:
                try:
                    response=supabase.auth.sign_up({"email":email.strip(),"password":password,"options":{"data":{"full_name":name.strip()}}})
                    if response.session:
                        st.session_state.session=response.session; st.session_state.user=response.user; st.session_state.auth_mode=None; st.success("Account created."); st.rerun()
                    else: st.success("Account created. Check your email to confirm your account, then log in.")
                except Exception as exc: st.error(f"Sign-up failed: {exc}")

# ============================================================
# STOP HERE IF NOT LOGGED IN
# ============================================================
if not current_user():
    if "auth_mode" not in st.session_state: st.session_state.auth_mode=None
    if st.session_state.auth_mode: auth_page(st.session_state.auth_mode)
    else: landing_page()
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
