"""
design_system.py
-----------------
Shared visual language for the quant dashboards in this workspace.
Aesthetic: a dark trading-terminal at night — near-black panels, hairline
borders, and a single electric-cyan accent that does the talking. Numbers
are set in a monospace face the way a real execution terminal would.

Usage:
    from design_system import *
    apply_theme()   # call once, first thing in the script
"""

import streamlit as st

__all__ = [
    "BG_PRIMARY", "BG_SECONDARY", "BG_CARD", "BG_CARD_HOVER",
    "BORDER_COLOR", "BORDER_COLOR_SOFT",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED",
    "ACCENT_CYAN", "ACCENT_CYAN_DIM", "ACCENT_MAGENTA", "ACCENT_GREEN", "ACCENT_AMBER", "ACCENT_RED",
    "REGIME_COLORS", "FONT_DISPLAY", "FONT_BODY",
    "regime_color", "apply_theme", "section_header", "regime_badge",
    "kpi_value", "metric_card", "get_plotly_layout",
]

# --------------------------------------------------------------------------
# COLOR TOKENS
# --------------------------------------------------------------------------

BG_PRIMARY = "#060a12"          # page background
BG_SECONDARY = "#0a1018"        # sidebar / secondary panels
BG_CARD = "#0d1420"             # card surfaces
BG_CARD_HOVER = "#101a28"
BORDER_COLOR = "#1c2735"
BORDER_COLOR_SOFT = "#141d29"

TEXT_PRIMARY = "#e8edf5"
TEXT_SECONDARY = "#7186a0"
TEXT_MUTED = "#4d5e72"

ACCENT_CYAN = "#2dd4ee"
ACCENT_CYAN_DIM = "#1a8aa0"
ACCENT_MAGENTA = "#e879f9"
ACCENT_GREEN = "#34d399"
ACCENT_AMBER = "#fbbf24"
ACCENT_RED = "#f87171"

# Ordered low-vol -> high-vol palette. "Uncertain" is the stability-filter
# flag color (slate grey, deliberately desaturated so it reads as "unknown"
# rather than as another point on the heat ramp).
REGIME_COLORS = {
    "Very Low Vol": "#22d3ee",
    "Low Vol": "#34d399",
    "Medium-Low Vol": "#a3e635",
    "Medium Vol": "#fbbf24",
    "Medium-High Vol": "#fb923c",
    "High Vol": "#f87171",
    "Very High Vol": "#ef4444",
    "Extreme Vol": "#dc2626",
    "Uncertain": "#64748b",
}

FONT_DISPLAY = "'JetBrains Mono', 'IBM Plex Mono', monospace"
FONT_BODY = "'Inter', -apple-system, sans-serif"


def regime_color(label: str) -> str:
    """Safe lookup with a grey fallback for unmapped labels."""
    return REGIME_COLORS.get(label, REGIME_COLORS["Uncertain"])


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# --------------------------------------------------------------------------
# THEME INJECTION
# --------------------------------------------------------------------------

def apply_theme(page_title: str = "Regime Detection Dashboard", page_icon: str = "◈"):
    """Call once at the top of the script, before any other st.* call."""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: {FONT_BODY};
        }}

        #MainMenu, footer {{ visibility: hidden; }}
        header {{ visibility: visible; }}
        [data-testid="stHeader"] {{ background: transparent; }}

        .stApp {{
            background:
                radial-gradient(circle at 15% 0%, {_hex_to_rgba(ACCENT_CYAN, 0.05)} 0%, transparent 45%),
                radial-gradient(circle at 85% 100%, {_hex_to_rgba(ACCENT_MAGENTA, 0.04)} 0%, transparent 45%),
                {BG_PRIMARY};
        }}

        section[data-testid="stSidebar"] {{
            background: {BG_SECONDARY};
            border-right: 1px solid {BORDER_COLOR};
        }}
        section[data-testid="stSidebar"] .stMarkdown p {{
            color: {TEXT_SECONDARY};
        }}

        h1, h2, h3 {{
            color: {TEXT_PRIMARY} !important;
            font-family: {FONT_BODY};
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        p, span, label, div {{ color: {TEXT_PRIMARY}; }}

        /* inputs */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        div[data-baseweb="select"] > div {{
            background-color: {BG_CARD} !important;
            border: 1px solid {BORDER_COLOR} !important;
            color: {TEXT_PRIMARY} !important;
            border-radius: 8px !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus {{
            border-color: {ACCENT_CYAN} !important;
            box-shadow: 0 0 0 1px {_hex_to_rgba(ACCENT_CYAN, 0.35)} !important;
        }}

        /* primary button */
        .stButton > button {{
            background: linear-gradient(135deg, {_hex_to_rgba(ACCENT_CYAN, 0.18)}, {_hex_to_rgba(ACCENT_CYAN, 0.05)});
            border: 1px solid {ACCENT_CYAN};
            color: {ACCENT_CYAN};
            font-weight: 600;
            border-radius: 8px;
            letter-spacing: 0.02em;
            transition: all 0.15s ease;
        }}
        .stButton > button:hover {{
            background: {_hex_to_rgba(ACCENT_CYAN, 0.22)};
            box-shadow: 0 0 18px {_hex_to_rgba(ACCENT_CYAN, 0.35)};
            color: {TEXT_PRIMARY};
        }}

        .stSlider [data-baseweb="slider"] > div > div {{ background: {ACCENT_CYAN} !important; }}

        hr {{ border-color: {BORDER_COLOR}; }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: {BG_PRIMARY}; }}
        ::-webkit-scrollbar-thumb {{ background: {BORDER_COLOR}; border-radius: 4px; }}

        [data-testid="stExpander"] {{
            background: {BG_CARD};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
        }}

        .block-container {{ padding-top: 1.6rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# COMPONENTS
# --------------------------------------------------------------------------

def section_header(title: str, subtitle: str | None = None):
    """An eyebrow-style section divider used above grids/tables."""
    sub_html = (
        f"<div style='color:{TEXT_SECONDARY};font-size:0.85rem;margin-top:2px;'>{subtitle}</div>"
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div style="margin:28px 0 14px 0;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="
                    font-family:{FONT_DISPLAY};
                    color:{ACCENT_CYAN};
                    font-size:0.75rem;
                    letter-spacing:0.12em;
                    text-transform:uppercase;
                    background:{_hex_to_rgba(ACCENT_CYAN, 0.1)};
                    padding:3px 9px;
                    border-radius:4px;
                    border:1px solid {_hex_to_rgba(ACCENT_CYAN, 0.3)};
                ">{title}</span>
                <div style="flex:1;height:1px;background:linear-gradient(90deg,{BORDER_COLOR},transparent);"></div>
            </div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def regime_badge(label: str, glow: bool = True, confidence: float | None = None):
    """Pill-shaped regime indicator with a colored glow, e.g. for the top bar."""
    color = regime_color(label)
    glow_css = (
        f"box-shadow: 0 0 22px {_hex_to_rgba(color, 0.45)}, 0 0 48px {_hex_to_rgba(color, 0.18)};"
        if glow
        else ""
    )
    conf_html = (
        f"<span style='color:{TEXT_SECONDARY};font-family:{FONT_DISPLAY};font-size:0.8rem;margin-left:4px;'>· {confidence*100:.0f}%</span>"
        if confidence is not None
        else ""
    )
    st.markdown(
        f"""
        <div style="
            display:inline-flex;align-items:center;gap:10px;
            background:linear-gradient(135deg, {_hex_to_rgba(color, 0.16)}, {_hex_to_rgba(color, 0.04)});
            border:1.5px solid {color};
            border-radius:999px;
            padding:9px 20px;
            {glow_css}
        ">
            <span style="
                width:9px;height:9px;border-radius:50%;background:{color};
                box-shadow:0 0 10px {color};
            "></span>
            <span style="color:{color};font-weight:700;font-size:1.1rem;letter-spacing:0.01em;
                font-family:{FONT_BODY};">{label}</span>
            {conf_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_value(label: str, value: str, color: str = ACCENT_CYAN, sublabel: str | None = None):
    """A large monospace number with a small uppercase label above it — used
    for the top status bar (confidence %, regimes detected, etc.)."""
    sub_html = (
        f"<div style='color:{TEXT_MUTED};font-size:0.72rem;margin-top:2px;'>{sublabel}</div>"
        if sublabel
        else ""
    )
    st.markdown(
        f"""
        <div>
            <div style="
                color:{TEXT_SECONDARY};font-size:0.72rem;letter-spacing:0.1em;
                text-transform:uppercase;font-family:{FONT_BODY};font-weight:600;
            ">{label}</div>
            <div style="
                color:{color};font-family:{FONT_DISPLAY};font-weight:700;
                font-size:2rem;line-height:1.25;margin-top:2px;
            ">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    title: str,
    metrics: dict,
    border_color: str = ACCENT_CYAN,
    footer: str | None = None,
):
    """
    A bordered stat card — used in the Regime Statistics grid.

    metrics: ordered dict of {label: value_string}
    """
    rows_html = ""
    for k, v in metrics.items():
        rows_html += f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:8px;">
<span style="color:{TEXT_SECONDARY};font-size:0.78rem;">{k}</span>
<span style="color:{TEXT_PRIMARY};font-family:{FONT_DISPLAY};font-weight:600;font-size:0.92rem;">{v}</span>
</div>
"""

    footer_html = (
        f"<div style='margin-top:10px;padding-top:10px;border-top:1px solid {BORDER_COLOR_SOFT};color:{TEXT_MUTED};font-size:0.72rem;'>{footer}</div>"
        if footer
        else ""
    )

    st.markdown(
        f"""
        <div style="
            background:{BG_CARD};
            border:1px solid {BORDER_COLOR};
            border-left:3px solid {border_color};
            border-radius:10px;
            padding:16px 18px;
            margin-bottom:14px;
            height:100%;
        ">
            <div style="
                color:{border_color};font-weight:700;font-size:0.95rem;
                display:flex;align-items:center;gap:8px;
            ">
                <span style="width:7px;height:7px;border-radius:50%;background:{border_color};box-shadow:0 0 8px {border_color};"></span>
                {title}
            </div>
{rows_html}
{footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_plotly_layout(height: int | None = None, title: str | None = None, show_legend: bool = True) -> dict:
    """Base layout dict to merge into go.Figure(layout=...) for a consistent
    dark, gridded, terminal-style chart look."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_BODY, color=TEXT_SECONDARY, size=12),
        xaxis=dict(
            gridcolor=BORDER_COLOR_SOFT,
            showgrid=True,
            zeroline=False,
            linecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_SECONDARY, size=11),
        ),
        yaxis=dict(
            gridcolor=BORDER_COLOR_SOFT,
            showgrid=True,
            zeroline=False,
            linecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_SECONDARY, size=11),
        ),
        margin=dict(l=50, r=30, t=50 if title else 20, b=40),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=BORDER_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_SECONDARY),
            orientation="h",
            y=1.06,
            x=0,
        )
        if show_legend
        else dict(visible=False),
        showlegend=show_legend,
    )
    if height:
        layout["height"] = height
    if title:
        layout["title"] = dict(text=title, font=dict(color=TEXT_PRIMARY, size=16, family=FONT_BODY), x=0)
    return layout