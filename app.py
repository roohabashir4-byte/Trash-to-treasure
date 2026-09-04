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
    # Visuals are loaded from Unsplash's image CDN. They are only used on
    # the public landing page; the app's data/backend remains unchanged.
    step_images = [
        "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=900&q=80",
        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=900&q=80",
        "https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=900&q=80",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=900&q=80",
        "https://images.unsplash.com/photo-1528323273322-d81458248d40?w=900&q=80",
    ]

    st.markdown(
        """
        <style>
        /* Landing-page-only styling */
        .tt-shell {
            max-width: 1240px;
            margin: 0 auto;
        }
        .tt-nav {
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding: .6rem 0 1rem;
            border-bottom:1px solid #e9eee9;
            margin-bottom:1rem;
        }
        .tt-brand {
            display:flex;
            align-items:center;
            gap:.55rem;
            font-size:1.35rem;
            font-weight:800;
            letter-spacing:-.03em;
            color:#13231b;
        }
        .tt-brand span { color:#168447; }
        .tt-navlinks {
            display:flex;
            gap:1.6rem;
            color:#33423a;
            font-size:.92rem;
            font-weight:600;
        }
        .tt-hero {
            min-height:510px;
            border-radius:30px;
            overflow:hidden;
            position:relative;
            background:
                linear-gradient(90deg, rgba(248,252,248,.98) 0%,
                rgba(248,252,248,.94) 48%, rgba(248,252,248,.28) 100%),
                url("https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=1800&q=85")
                center/cover;
            display:flex;
            align-items:center;
            padding:3.8rem;
            box-shadow:0 14px 40px rgba(22,70,43,.10);
        }
        .tt-hero-copy { max-width:650px; }
        .tt-eyebrow {
            display:inline-block;
            padding:.4rem .75rem;
            border-radius:999px;
            background:#e6f5e9;
            color:#167a42;
            font-size:.75rem;
            font-weight:800;
            letter-spacing:.08em;
        }
        .tt-hero h1 {
            font-size:clamp(2.7rem,5vw,4.6rem);
            line-height:1.02;
            letter-spacing:-.055em;
            color:#13231b;
            margin:1rem 0;
        }
        .tt-hero h1 .green { color:#168447; }
        .tt-hero p {
            font-size:1.14rem;
            line-height:1.65;
            color:#3f4d45;
            max-width:610px;
            margin-bottom:1.4rem;
        }
        .tt-phone {
            position:absolute;
            right:6%;
            bottom:0;
            width:280px;
            background:#101511;
            border:7px solid #111;
            border-radius:34px 34px 0 0;
            padding:11px;
            box-shadow:0 22px 45px rgba(0,0,0,.22);
            transform:rotate(2deg);
        }
        .tt-phone-screen {
            background:white;
            border-radius:22px;
            overflow:hidden;
            padding-bottom:12px;
        }
        .tt-phone-screen img {
            width:100%;
            height:165px;
            object-fit:cover;
        }
        .tt-phone-body { padding:10px 13px; }
        .tt-phone-body h3 { margin:0 0 5px; font-size:1.1rem; color:#17231c; }
        .tt-price { color:#128344; font-size:1.25rem; font-weight:800; }
        .tt-phone-btn {
            margin-top:10px;
            padding:9px;
            border-radius:10px;
            text-align:center;
            background:#168447;
            color:white;
            font-weight:700;
            font-size:.75rem;
        }
        .tt-trust {
            display:flex;
            gap:1.4rem;
            flex-wrap:wrap;
            margin-top:1rem;
            color:#3f4d45;
            font-size:.85rem;
            font-weight:600;
        }
        .tt-section {
            padding:3.5rem 0 .8rem;
        }
        .tt-section-head {
            text-align:center;
            margin-bottom:2rem;
        }
        .tt-section-head h2 {
            font-size:2.25rem;
            letter-spacing:-.04em;
            color:#13231b;
            margin:.35rem 0;
        }
        .tt-section-head p { color:#68756e; }
        .tt-steps {
            display:grid;
            grid-template-columns:repeat(5,1fr);
            gap:1rem;
        }
        .tt-step {
            background:white;
            border:1px solid #e3eae4;
            border-radius:22px;
            overflow:hidden;
            box-shadow:0 5px 20px rgba(20,60,35,.06);
        }
        .tt-step-img {
            width:100%;
            height:155px;
            object-fit:cover;
            display:block;
        }
        .tt-step-body { padding:1rem; }
        .tt-num {
            width:30px;
            height:30px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#168447;
            color:white;
            font-weight:800;
            margin-bottom:.65rem;
        }
        .tt-step h3 { margin:0 0 .4rem; color:#17231c; font-size:1.05rem; }
        .tt-step p { margin:0; color:#68756e; line-height:1.45; font-size:.88rem; }
        .tt-benefits {
            display:grid;
            grid-template-columns:repeat(4,1fr);
            gap:1rem;
        }
        .tt-benefit {
            min-height:180px;
            padding:1.35rem;
            border-radius:22px;
            background:#f3f8f1;
            border:1px solid #e0eadf;
        }
        .tt-icon { font-size:2rem; }
        .tt-benefit h3 { color:#17231c; margin:.45rem 0; }
        .tt-benefit p { color:#68756e; line-height:1.5; }
        .tt-impact {
            margin-top:3rem;
            border-radius:28px;
            padding:3rem;
            background:linear-gradient(135deg,#0d6337,#168447);
            color:white;
            display:grid;
            grid-template-columns:1.3fr 1fr;
            gap:2rem;
            align-items:center;
        }
        .tt-impact h2 {
            font-size:2.4rem;
            margin:0 0 .7rem;
        }
        .tt-impact p { opacity:.9; line-height:1.6; }
        .tt-stats {
            display:grid;
            grid-template-columns:repeat(3,1fr);
            gap:1rem;
            text-align:center;
        }
        .tt-stat strong { display:block; font-size:2rem; }
        .tt-stat span { opacity:.85; font-size:.8rem; }
        .tt-testimonial {
            background:white;
            color:#26342c;
            padding:1.3rem;
            border-radius:20px;
            margin-top:1.3rem;
        }
        .tt-footer {
            padding:2rem 0 1rem;
            color:#6b776f;
            display:flex;
            justify-content:space-between;
            gap:1rem;
            font-size:.85rem;
        }
        @media (max-width: 950px) {
            .tt-navlinks { display:none; }
            .tt-hero { padding:2rem; min-height:620px; }
            .tt-phone { opacity:.28; right:3%; }
            .tt-steps { grid-template-columns:repeat(2,1fr); }
            .tt-benefits { grid-template-columns:repeat(2,1fr); }
            .tt-impact { grid-template-columns:1fr; }
        }
        @media (max-width: 600px) {
            .tt-hero { padding:1.5rem; }
            .tt-hero h1 { font-size:2.65rem; }
            .tt-phone { display:none; }
            .tt-steps, .tt-benefits { grid-template-columns:1fr; }
            .tt-stats { grid-template-columns:1fr; }
            .tt-footer { flex-direction:column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tt-shell">
          <div class="tt-nav">
            <div class="tt-brand">♻️ Trash to <span>Treasure</span></div>
            <div class="tt-navlinks">
              <span>How It Works</span>
              <span>Why Use Us</span>
              <span>For Dealers</span>
              <span>FAQ</span>
            </div>
          </div>

          <div class="tt-hero">
            <div class="tt-hero-copy">
              <div class="tt-eyebrow">SMART SCRAP • LOCAL VALUE • EASY SELLING</div>
              <h1>Don't throw it away.<br><span class="green">Find out what it's worth.</span></h1>
              <p>
                Identify your scrap, get an estimated value, and connect with
                verified buyers near you — all from one simple app.
              </p>
        """,
        unsafe_allow_html=True,
    )

    cta1, cta2 = st.columns([1, .55])
    with cta1:
        if st.button("📷  Start Now — It's Free", type="primary",
                     use_container_width=True, key="landing_start"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with cta2:
        if st.button("♙  Login", use_container_width=True, key="landing_login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    st.markdown(
        """
              <div class="tt-trust">
                <span>🛡️ Safe & Private</span>
                <span>📍 Local Buyers</span>
                <span>✓ Verified Dealers</span>
              </div>
            </div>

            <div class="tt-phone">
              <div class="tt-phone-screen">
                <img src="https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=700&q=80">
                <div class="tt-phone-body">
                  <h3>Copper</h3>
                  <div style="font-size:.7rem;color:#718078">Estimated value</div>
                  <div class="tt-price">Rs. 3,250</div>
                  <div style="font-size:.72rem;color:#718078;margin-top:7px">5 kg × current rate</div>
                  <div class="tt-phone-btn">Find Buyers Near Me</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="tt-shell tt-section">
          <div class="tt-section-head">
            <div style="color:#168447;font-weight:800">🌿 SIMPLE FROM START TO SALE</div>
            <h2>How It Works</h2>
            <p>Five simple steps to turn unwanted stuff into treasure.</p>
          </div>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        ("Take a Picture", "Snap a clear photo of the item you want to sell.", step_images[0]),
        ("We Identify It", "Our AI identifies the most likely material.", step_images[1]),
        ("Add Weight", "Enter the measured weight for a better estimate.", step_images[2]),
        ("See Your Value", "Get an estimated value using the available rate.", step_images[3]),
        ("Find a Buyer", "Connect with a suitable verified local dealer.", step_images[4]),
    ]

    step_html = '<div class="tt-steps">'
    for i, (title, desc, img) in enumerate(steps, 1):
        step_html += f"""
        <div class="tt-step">
          <img class="tt-step-img" src="{img}" alt="{title}">
          <div class="tt-step-body">
            <div class="tt-num">{i}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
          </div>
        </div>
        """
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="tt-section-head" style="margin-top:3.5rem">
          <div style="color:#168447;font-weight:800">♻️ MADE FOR REAL PEOPLE</div>
          <h2>Why Use Trash to Treasure?</h2>
          <p>Less guessing. More value. A cleaner recycling journey.</p>
        </div>

        <div class="tt-benefits">
          <div class="tt-benefit">
            <div class="tt-icon">💰</div>
            <h3>Make Money</h3>
            <p>Find out what your unwanted materials may be worth.</p>
          </div>
          <div class="tt-benefit">
            <div class="tt-icon">🛡️</div>
            <h3>Trusted Buyers</h3>
            <p>See dealers that have been verified before recommendation.</p>
          </div>
          <div class="tt-benefit">
            <div class="tt-icon">📍</div>
            <h3>Nearby & Convenient</h3>
            <p>Our next upgrade will make buyer matching location-aware.</p>
          </div>
          <div class="tt-benefit">
            <div class="tt-icon">🌍</div>
            <h3>Better for the Planet</h3>
            <p>Keep useful materials in circulation instead of throwing them away.</p>
          </div>
        </div>

        <div class="tt-impact">
          <div>
            <h2>Small Action.<br>Big Impact.</h2>
            <p>
              Every item that finds a better destination is one less useful
              material going straight to the waste stream.
            </p>
            <div class="tt-testimonial">
              ⭐⭐⭐⭐⭐<br>
              <b>“My old scrap may be worth more than I thought.”</b><br>
              <span style="color:#68756e">A future customer story from Mianwali.</span>
            </div>
          </div>
          <div class="tt-stats">
            <div class="tt-stat"><strong>AI</strong><span>Material Identification</span></div>
            <div class="tt-stat"><strong>Rs.</strong><span>Estimated Value</span></div>
            <div class="tt-stat"><strong>📍</strong><span>Local Buyer Matching</span></div>
          </div>
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
