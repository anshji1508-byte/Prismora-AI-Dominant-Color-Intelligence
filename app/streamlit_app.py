import hashlib
import base64
import json
from io import BytesIO
import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Supports both `streamlit run app/streamlit_app.py` and editable installs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chromatic.color_analysis import extract_palette, rgb_to_hex, valid_centers


DEFAULT_SAMPLE = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample-colorful.png"
LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "prismora-logo.svg"
FAVICON_PATH = Path(__file__).resolve().parents[1] / "assets" / "prismora-favicon.png"
PROJECT_ROOT = DEFAULT_SAMPLE.parents[2]
METRICS_PATH = PROJECT_ROOT / "reports" / "metrics.json"
PALETTE_PATH = PROJECT_ROOT / "models" / "palette.json"


st.set_page_config(page_title="Prismora AI — Color Intelligence", page_icon=str(FAVICON_PATH), layout="wide")


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


experiment_metrics = load_json(METRICS_PATH)
experiment_palette = load_json(PALETTE_PATH)


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


themes = {
    "Aurora": ("#090b18", "#15102c", "#a78bfa", "#6ee7b7"),
    "Ocean": ("#06131d", "#0b2635", "#38bdf8", "#5eead4"),
    "Ember": ("#180b0b", "#301311", "#fb7185", "#fbbf24"),
    "Emerald": ("#071510", "#10271e", "#34d399", "#bef264"),
}
theme_name = st.sidebar.selectbox("Visual theme", list(themes), index=0)
theme_bg, theme_panel, theme_accent, theme_success = themes[theme_name]
theme_css = """
<style>
:root { --bg: __BG__; --panel: __PANEL__; --accent: __ACCENT__; --success: __SUCCESS__; }
.stApp { background: radial-gradient(circle at 85% 0%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 30rem), linear-gradient(135deg, var(--bg), #080910 70%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, var(--panel), var(--bg)); border-right:1px solid color-mix(in srgb, var(--accent) 22%, transparent); }
[data-testid="stSidebar"] > div:first-child { padding-top:2rem; }
.status-pill { display:inline-block; background:color-mix(in srgb, var(--success) 15%, transparent); color:var(--success); border:1px solid color-mix(in srgb, var(--success) 40%, transparent); border-radius:999px; padding:.35rem .75rem; font-size:.72rem; font-weight:800; letter-spacing:.08em; }
.brand { font-size:1.25rem; font-weight:800; letter-spacing:-.04em; color:#fff; }
.brand-lockup { display:flex; align-items:center; gap:.7rem; margin-bottom:.35rem; }
.brand-lockup img { width:42px; height:42px; object-fit:contain; filter:drop-shadow(0 5px 14px color-mix(in srgb, var(--accent) 35%, transparent)); }
.brand-word { font-size:1.35rem; font-weight:850; letter-spacing:-.06em; color:#fff; }
.brand-word span { color:var(--accent); font-size:.72rem; letter-spacing:.12em; margin-left:.15rem; vertical-align:top; }
.hero { padding:2.1rem 0 1.35rem; position:relative; }
.hero::after { content:""; position:absolute; right:4%; top:8%; width:180px; height:180px; border-radius:50%; background:radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--accent) 70%, white), transparent 62%); filter:blur(12px); opacity:.28; animation:floatOrb 6s ease-in-out infinite; pointer-events:none; }
.eyebrow { color:var(--accent); font-size:.72rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.5rem,6vw,5.2rem); line-height:.94; letter-spacing:-.075em; margin:.55rem 0 1rem; background:linear-gradient(100deg,#fff 25%,var(--accent)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p,.muted { color:#a7afc0; } .hero p { font-size:1.05rem; max-width:680px; line-height:1.55; }
.panel { background:linear-gradient(145deg, color-mix(in srgb, var(--panel) 92%, white 8%), color-mix(in srgb, var(--bg) 75%, transparent)); border:1px solid color-mix(in srgb, var(--accent) 20%, #303544); border-radius:22px; padding:1.1rem; box-shadow:0 18px 50px rgba(0,0,0,.16); animation:riseIn .65s ease both; }
.panel:hover { border-color:color-mix(in srgb, var(--accent) 52%, transparent); transform:translateY(-2px); transition:transform .25s ease,border-color .25s ease; }
.swatch { border-radius:16px; height:110px; box-shadow:inset 0 0 0 1px rgba(255,255,255,.18), 0 8px 24px rgba(0,0,0,.15); margin-bottom:.8rem; }
.color-name { font-weight:750; font-size:1.05rem; } .metric { color:#fff; font-size:1.55rem; font-weight:800; letter-spacing:-.04em; }
.kpi-card { min-height:112px; }
.kpi-value { color:#fff; font-size:1.65rem; font-weight:850; letter-spacing:-.05em; margin:.25rem 0; }
.kpi-label { color:#a7afc0; font-size:.72rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
.kpi-hint { color:#788296; font-size:.75rem; }
.palette-graph { background:color-mix(in srgb, var(--panel) 85%, transparent); border:1px solid color-mix(in srgb, var(--accent) 15%, transparent); border-radius:22px; padding:1.2rem 1.35rem; margin:1.2rem 0; }
.bar-row { display:grid; grid-template-columns:88px 1fr 62px; align-items:center; gap:12px; margin:.8rem 0; }
.bar-label { color:#d8dcea; font-size:.8rem; font-weight:700; }
.bar-track { background:rgba(255,255,255,.08); border-radius:999px; height:12px; overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; transform-origin:left; animation:growBar 1.1s cubic-bezier(.2,.8,.2,1) both; box-shadow:0 0 18px color-mix(in srgb, var(--bar-color) 65%, transparent); }
.bar-value { color:#a7afc0; font-size:.78rem; text-align:right; }
@keyframes riseIn { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
@keyframes growBar { from { transform:scaleX(0); } to { transform:scaleX(1); } }
@keyframes floatOrb { 0%,100% { transform:translate(0,0) scale(1); } 50% { transform:translate(-18px,12px) scale(1.08); } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
div[data-testid="stButton"] button[kind="primary"] { background:linear-gradient(100deg,var(--accent),color-mix(in srgb, var(--accent) 60%, #fff)); color:#0b0d12; border:0; font-weight:800; }
div[data-testid="stDownloadButton"] button { border-color:color-mix(in srgb, var(--accent) 30%, transparent); }
div[data-testid="stTabs"] button[aria-selected="true"] { color:var(--accent); }
</style>
""".replace("__BG__", theme_bg).replace("__PANEL__", theme_panel).replace("__ACCENT__", theme_accent).replace("__SUCCESS__", theme_success)
st.markdown(theme_css, unsafe_allow_html=True)


with st.sidebar:
    logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode() if LOGO_PATH.exists() else ""
    st.markdown(f'<div class="brand-lockup"><img src="data:image/svg+xml;base64,{logo_data}" alt="Prismora AI logo"><div class="brand-word">Prismora<span>AI</span></div></div>', unsafe_allow_html=True)
    st.caption("Visual intelligence for every image")
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
    st.divider()
    st.markdown("### MLOps status")
    st.markdown('<span class="status-pill">● PIPELINE READY</span>', unsafe_allow_html=True)
    st.caption(f"DVC experiment · {experiment_metrics.get('n_colors', '—')} clusters · reproducible artifact")


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

# Build live metrics from the image/settings currently displayed in the UI.
original_pixels = np.asarray(preview).astype(np.float32)
segmented_pixels = np.asarray(segmented).astype(np.float32)
live_percentages = np.asarray(percentages, dtype=float)
live_distribution = live_percentages / 100.0
live_metrics = {
    "n_colors": analysis_n_colors,
    "sample_size": analysis_sample_size,
    "mean_absolute_color_error": float(np.abs(original_pixels - segmented_pixels).mean()),
    "rmse_color_error": float(np.sqrt(np.square(original_pixels - segmented_pixels).mean())),
    "palette_entropy": float(-(live_distribution * np.log2(np.clip(live_distribution, 1e-12, 1))).sum()),
    "dominant_color_share_percent": float(live_percentages[0]),
    "image_width": original_size[0],
    "image_height": original_size[1],
}
live_params = {
    "n_colors": analysis_n_colors,
    "sample_size": analysis_sample_size,
    "online_learning": analysis_online,
    "random_state": 42,
}

st.markdown(f'<div class="hero"><div class="eyebrow">Image intelligence · production pipeline</div><span class="status-pill">● ONLINE ANALYSIS</span><h1>Find the colors<br><span style="color:#9b8cff">hiding in plain sight.</span></h1><p>Upload any image and uncover its {analysis_n_colors} most dominant colors through a reproducible, experiment-tracked pipeline.</p></div>', unsafe_allow_html=True)
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
cards_per_row = min(4, analysis_n_colors)
for row_start in range(0, analysis_n_colors, cards_per_row):
    row_colors = centers[row_start:row_start + cards_per_row]
    row_percentages = percentages[row_start:row_start + cards_per_row]
    cols = st.columns(cards_per_row, gap="medium")
    for offset, (column, color, percentage) in enumerate(zip(cols, row_colors, row_percentages), row_start + 1):
        with column:
            hex_value = rgb_to_hex(color)
            st.markdown(f'<div class="panel"><div class="swatch" style="background:{hex_value}"></div><div class="color-name">Color {offset}</div><div class="metric">{percentage:.1f}%</div><div class="muted">{hex_value} · RGB {tuple(int(x) for x in color)}</div></div>', unsafe_allow_html=True)

bar_rows = "".join(
    f'<div class="bar-row"><div class="bar-label">Color {index}</div>'
    f'<div class="bar-track"><div class="bar-fill" style="--bar-color:{rgb_to_hex(color)}; width:{float(percentage):.2f}%; background:{rgb_to_hex(color)}; animation-delay:{index * 80}ms"></div></div>'
    f'<div class="bar-value">{float(percentage):.1f}%</div></div>'
    for index, (color, percentage) in enumerate(zip(centers, percentages), 1)
)
st.markdown(f'<div class="palette-graph"><div class="eyebrow">Palette composition</div><h3 style="margin:.35rem 0 1rem">Color distribution</h3>{bar_rows}</div>', unsafe_allow_html=True)

palette_text = "\n".join(f"Color {i}: {rgb_to_hex(c)} | RGB {tuple(int(x) for x in c)} | {p:.1f}%" for i, (c, p) in enumerate(zip(centers, percentages), 1))
st.download_button("Download palette values", palette_text, "dominant-palette.txt", mime="text/plain")
st.download_button("Download segmented image", png_bytes(segmented), "segmented-image.png", mime="image/png")

st.divider()
st.markdown("## MLOps control room")
st.caption("Experiment artifacts generated by DVC · model parameters, metrics and outputs are versionable and reproducible.")
metric_cols = st.columns(4, gap="medium")
cards = [
    ("Clusters", live_metrics["n_colors"], "current analysis"),
    ("Color error", f"{live_metrics['mean_absolute_color_error']:.1f}", "live mean RGB error"),
    ("Dominant share", f"{live_metrics['dominant_color_share_percent']:.1f}%", "current largest cluster"),
    ("Experiment", "LIVE", "updated from this image"),
]
for column, (label, value, hint) in zip(metric_cols, cards):
    with column:
        st.markdown(f'<div class="panel kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-hint">{hint}</div></div>', unsafe_allow_html=True)

tab_experiment, tab_pipeline, tab_deploy = st.tabs(["Experiment", "Pipeline", "Deploy"])
with tab_experiment:
    st.markdown("#### Current run parameters")
    param_cols = st.columns(4, gap="medium")
    param_cards = [
        ("Color clusters", live_params["n_colors"], "current model.n_colors"),
        ("Pixel sample", f"{live_params['sample_size']:,}", "pixels used now"),
        ("Learning mode", "Online" if live_params["online_learning"] else "Batch", "current training strategy"),
        ("Random seed", live_params["random_state"], "reproducibility"),
    ]
    for column, (label, value, hint) in zip(param_cols, param_cards):
        with column:
            st.metric(label, value, help=hint)

    st.markdown("#### Evaluation KPIs")
    kpi_cols = st.columns(4, gap="medium")
    kpi_cards = [
        ("Mean color error", f"{live_metrics['mean_absolute_color_error']:.2f}", "lower is better"),
        ("RMSE error", f"{live_metrics['rmse_color_error']:.2f}", "reconstruction quality"),
        ("Palette entropy", f"{live_metrics['palette_entropy']:.2f}", "color diversity"),
        ("Image size", f"{live_metrics['image_width']} × {live_metrics['image_height']}", "source resolution"),
    ]
    for column, (label, value, hint) in zip(kpi_cols, kpi_cards):
        with column:
            st.metric(label, value, help=hint)
    st.caption(f"Dominant color share: {live_metrics['dominant_color_share_percent']:.2f}% · live session result")
with tab_pipeline:
    st.markdown("#### Reproducible pipeline")
    st.code("""data/raw/sample-colorful.png
        ↓
analyze  →  models/palette.json
        ↓
reports/metrics.json + reports/segmented.png""", language="text")
    st.success("DVC stage `analyze` is configured and reproducible.")
    st.caption("Change `params.yaml`, then run `dvc exp run` to compare a new experiment.")
with tab_deploy:
    st.markdown("#### Container & CI/CD")
    st.code("""make test
make lint
dvc repro
docker build -t chromatic-color-studio .
docker run --rm -p 8501:8501 chromatic-color-studio""", language="bash")
    st.info("GitHub Actions runs linting, tests, the DVC experiment and publishes the Docker image to GHCR on main.")
