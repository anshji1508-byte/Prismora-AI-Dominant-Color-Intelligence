import hashlib
from io import BytesIO
import sys
from pathlib import Path

import streamlit as st

# Supports both `streamlit run app/streamlit_app.py` and editable installs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chromatic.color_analysis import extract_palette, rgb_to_hex, valid_centers


DEFAULT_SAMPLE = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample-colorful.png"


st.set_page_config(page_title="Chromatic — Dominant Color Studio", page_icon="🎨", layout="wide")


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


st.markdown("""
<style>
.stApp { background:#0b0d12; } [data-testid="stSidebar"] { background:#11141c; }
.hero { padding:1.3rem 0; } .eyebrow { color:#9b8cff; font-size:.76rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.3rem,5vw,4.5rem); line-height:.98; letter-spacing:-.06em; margin:.35rem 0 .8rem; }
.hero p,.muted { color:#9199aa; } .hero p { font-size:1.05rem; max-width:650px; }
.panel { background:#151923; border:1px solid #262c3a; border-radius:18px; padding:1.05rem; }
.swatch { border-radius:14px; height:96px; box-shadow:inset 0 0 0 1px rgba(255,255,255,.13); margin-bottom:.7rem; }
.color-name { font-weight:700; font-size:1.05rem; } .metric { color:#fff; font-size:1.4rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## 🎨 Chromatic")
    st.caption("A tiny color lab for your images")
    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])
    st.divider()
    st.markdown("### Analysis settings")
    n_colors = st.slider("Dominant colors", 2, 8, 4)
    sample_size = st.slider("Pixels used for analysis", 5_000, 50_000, 20_000, step=5_000)
    online_learning = st.toggle("Online learning mode", value=True)
    analyze_clicked = st.button("🔍 Analyze image", type="primary", use_container_width=True)
    st.caption("Upload an image, choose settings, then click Analyze image.")
    if st.button("Reset learned palette", use_container_width=True):
        for key in ("learned_centers", "images_seen", "last_image_key"):
            st.session_state.pop(key, None)
        st.rerun()


candidate_bytes = uploaded.getvalue() if uploaded else None
candidate_label = uploaded.name if uploaded else None
if candidate_bytes is None and DEFAULT_SAMPLE.exists():
    candidate_bytes = DEFAULT_SAMPLE.read_bytes()
    candidate_label = "sample-colorful.png"
if analyze_clicked and candidate_bytes is not None:
    st.session_state["analysis_bytes"] = candidate_bytes
    st.session_state["analysis_label"] = candidate_label
    st.session_state["analysis_config"] = (n_colors, sample_size, online_learning)
    st.session_state.pop("last_image_key", None)

if "analysis_bytes" not in st.session_state:
    if candidate_bytes is None:
        st.info("Upload an image, then click Analyze image to begin.")
        st.stop()
    st.session_state["analysis_bytes"] = candidate_bytes
    st.session_state["analysis_label"] = candidate_label
    st.session_state["analysis_config"] = (n_colors, sample_size, online_learning)

source_bytes = st.session_state["analysis_bytes"]
source_label = st.session_state["analysis_label"]
analysis_n_colors, analysis_sample_size, analysis_online = st.session_state["analysis_config"]
previous_centers = valid_centers(st.session_state.get("learned_centers"), analysis_n_colors) if analysis_online else None
if analysis_online and st.session_state.get("learned_centers") is not None and previous_centers is None:
    st.session_state.pop("learned_centers", None)
    st.session_state.pop("last_image_key", None)

image_key = hashlib.sha1(source_bytes).hexdigest()
should_learn = analysis_online and image_key != st.session_state.get("last_image_key")
try:
    preview, segmented, centers, percentages, original_size, learned_centers = extract_palette(
        source_bytes, analysis_n_colors, analysis_sample_size, analysis_online,
        tuple(map(tuple, previous_centers)) if previous_centers is not None else None, should_learn
    )
except Exception as error:
    st.error(f"Could not process this image: {error}")
    st.stop()

if analysis_online and should_learn:
    st.session_state["learned_centers"] = learned_centers
    st.session_state["images_seen"] = st.session_state.get("images_seen", 0) + 1
    st.session_state["last_image_key"] = image_key

st.markdown(f'<div class="hero"><div class="eyebrow">Image intelligence · 01</div><h1>Find the colors<br><span style="color:#9b8cff">hiding in plain sight.</span></h1><p>Upload any image and uncover its {analysis_n_colors} most dominant colors.</p></div>', unsafe_allow_html=True)
left, right = st.columns(2, gap="large")
with left:
    st.markdown('<div class="panel"><div class="muted">ORIGINAL IMAGE</div>', unsafe_allow_html=True)
    st.image(preview, use_container_width=True)
    st.markdown(f'<div class="muted">{source_label} · {original_size[0]} × {original_size[1]} px</div></div>', unsafe_allow_html=True)
with right:
    st.markdown(f'<div class="panel"><div class="muted">{analysis_n_colors}-COLOR SEGMENTATION</div>', unsafe_allow_html=True)
    st.image(segmented, use_container_width=True)
    st.markdown('<div class="muted">Each pixel mapped to its closest dominant color</div></div>', unsafe_allow_html=True)

st.markdown(f"## Your top {analysis_n_colors} colors")
cols = st.columns(analysis_n_colors, gap="medium")
for index, (column, color, percentage) in enumerate(zip(cols, centers, percentages), 1):
    with column:
        hex_value = rgb_to_hex(color)
        st.markdown(f'<div class="panel"><div class="swatch" style="background:{hex_value}"></div><div class="color-name">Color {index}</div><div class="metric">{percentage:.1f}%</div><div class="muted">{hex_value} · RGB {tuple(int(x) for x in color)}</div></div>', unsafe_allow_html=True)

palette_text = "\n".join(f"Color {i}: {rgb_to_hex(c)} | RGB {tuple(int(x) for x in c)} | {p:.1f}%" for i, (c, p) in enumerate(zip(centers, percentages), 1))
st.download_button("Download palette values", palette_text, "dominant-palette.txt", mime="text/plain")
st.download_button("Download segmented image", png_bytes(segmented), "segmented-image.png", mime="image/png")
