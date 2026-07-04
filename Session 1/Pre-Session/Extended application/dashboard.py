"""
==============================================================
  📈 Extended Stock Price Dashboard
  Built with Streamlit · yfinance · Plotly · Groq AI
==============================================================
  Sections:
    0  — Imports & Page Config
    1  — Sidebar: Dashboard Controls
    2  — Helper / Indicator Functions
    3  — Data Loading (cached)
    4  — KPI Metric Cards  (preserved from original)
    5  — Company Fundamentals Panel
    6  — Candlestick Chart + Technical Overlays
    7  — RSI / MACD Sub-charts
    8  — Performance Statistics
    9  — Stock Comparison Chart
   10  — News Panel + AI News Summary
   11  — AI Market Commentary  (preserved from original)
   12  — AI Chat ("Ask AI About This Stock")
   13  — Raw Data Table  (preserved from original)
==============================================================
"""

# ─────────────────────────────────────────────────────────────
# SECTION 0 — IMPORTS & PAGE CONFIG
# ─────────────────────────────────────────────────────────────
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page must be configured before any other Streamlit call
st.set_page_config(
    page_title="Stock Price Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# SECTION 1 — SIDEBAR: DASHBOARD CONTROLS
# ─────────────────────────────────────────────────────────────

st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("---")

# --- Stock Ticker Input ---
st.sidebar.subheader("🔍 Stock Selection")
ticker = st.sidebar.text_input(
    "Enter Stock Ticker",
    value="RELIANCE.NS",
    help="e.g. RELIANCE.NS, TCS.NS, AAPL, TSLA",
).strip().upper()

# --- Quick Date Range Selector ---
st.sidebar.subheader("📅 Date Range")
QUICK_RANGES = {
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "3 Years": 1095,
    "5 Years": 1825,
    "Max": 7300,  # ~20 years
}
quick_range = st.sidebar.radio(
    "Quick Select",
    options=list(QUICK_RANGES.keys()),
    index=2,  # default: 6 Months
)
today = datetime.date.today()
default_start = today - datetime.timedelta(days=QUICK_RANGES[quick_range])

# Manual date override (still available)
date_range = st.sidebar.date_input(
    "Or pick custom dates",
    value=(default_start, today),
    max_value=today,
)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0] if isinstance(date_range, (list, tuple)) else default_start
    end_date = today

st.sidebar.markdown("---")

# --- Chart Options ---
st.sidebar.subheader("📉 Chart Options")
show_volume = st.sidebar.checkbox("Show Volume", value=True)
show_grid   = st.sidebar.checkbox("Show Grid",   value=True)

st.sidebar.markdown("---")

# --- Technical Indicators ---
st.sidebar.subheader("📐 Technical Indicators")
ind_sma20  = st.sidebar.checkbox("SMA 20")
ind_sma50  = st.sidebar.checkbox("SMA 50")
ind_ema20  = st.sidebar.checkbox("EMA 20")
ind_bb     = st.sidebar.checkbox("Bollinger Bands")
ind_rsi    = st.sidebar.checkbox("RSI (14)")
ind_macd   = st.sidebar.checkbox("MACD")

st.sidebar.markdown("---")

# --- Comparison Stock ---
st.sidebar.subheader("🔀 Stock Comparison")
compare_ticker = st.sidebar.text_input(
    "Comparison Ticker (optional)",
    value="",
    help="e.g. TCS.NS, INFY.NS, MSFT",
).strip().upper()

st.sidebar.markdown("---")
st.sidebar.caption("Data sourced from Yahoo Finance · AI by Groq")

# ─────────────────────────────────────────────────────────────
# SECTION 2 — HELPER / INDICATOR FUNCTIONS
# ─────────────────────────────────────────────────────────────

def compute_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average over `window` periods."""
    return series.rolling(window=window).mean()


def compute_ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average over `window` periods."""
    return series.ewm(span=window, adjust=False).mean()


def compute_bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands: returns (upper, middle SMA, lower).
    """
    mid = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder's smoothing).
    Returns a Series of RSI values (0–100).
    """
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    MACD indicator.
    Returns DataFrame with columns: macd, signal, histogram.
    """
    ema_fast   = series.ewm(span=fast,   adjust=False).mean()
    ema_slow   = series.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return pd.DataFrame({
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": histogram,
    })


def format_large_number(value) -> str:
    """Format large numbers into readable strings (e.g. 1.23T, 456.7B)."""
    try:
        value = float(value)
        if value >= 1e12:
            return f"{value / 1e12:.2f}T"
        elif value >= 1e9:
            return f"{value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"{value / 1e6:.2f}M"
        return f"{value:,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def safe_get(info: dict, key: str, default: str = "N/A") -> str:
    """Safely extract a value from yfinance info dict."""
    val = info.get(key, None)
    if val is None or val == "" or val != val:   # catches NaN
        return default
    return str(val)


# ─────────────────────────────────────────────────────────────
# SECTION 3 — CACHED DATA LOADERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data(ticker: str, start: datetime.date, end: datetime.date) -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance (cached 5 min)."""
    df = yf.download(ticker, start=start, end=end, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_company_info(ticker: str) -> dict:
    """Fetch company metadata from yfinance (cached 1 hour)."""
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def load_news(ticker: str) -> list:
    """
    Fetch recent news articles from yfinance (cached 30 min).
    
    Newer yfinance versions (0.2.x+) use a POST-based endpoint that
    may time out for some tickers. We cap the wait and return an
    empty list rather than crashing.
    """
    try:
        articles = yf.Ticker(ticker).news or []
        return articles[:5]
    except Exception:
        # Covers network timeouts, API errors, and schema changes
        return []


def extract_article_fields(article: dict) -> dict:
    """
    Safely pull title, publisher, link, and publish-time from a
    yfinance news article regardless of schema version.

    yfinance < 0.2  →  flat dict with 'title', 'link', 'publisher'
    yfinance ≥ 0.2  →  nested under article['content'] with keys
                        'title', 'clickThroughUrl.url', 'provider.displayName'
    """
    # --- Try new nested schema first ---
    content = article.get("content", {})
    if content:
        title = content.get("title", "").strip()
        # Link lives in clickThroughUrl.url or canonicalUrl.url
        click_url  = (content.get("clickThroughUrl") or {}).get("url", "")
        canon_url  = (content.get("canonicalUrl")    or {}).get("url", "")
        link       = click_url or canon_url or "#"
        publisher  = (content.get("provider") or {}).get("displayName", "Unknown")
        # Publish time is an ISO string in new schema
        pub_raw    = content.get("pubDate", "")
        pub_time   = None
        if pub_raw:
            try:
                pub_time = datetime.datetime.fromisoformat(
                    pub_raw.replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                pub_time = None
    else:
        # --- Flat (legacy) schema ---
        title     = article.get("title", "").strip()
        link      = article.get("link", article.get("url", "#"))
        publisher = article.get("publisher", "Unknown")
        pub_time  = article.get("providerPublishTime", None)

    return {
        "title":     title or "(Title unavailable)",
        "publisher": publisher or "Unknown",
        "link":      link or "#",
        "pub_time":  pub_time,
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_recent_ohlc(ticker: str) -> pd.DataFrame:
    """Download last 20 calendar days to get ~10 trading days (cached 5 min)."""
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.tail(10)


# ─────────────────────────────────────────────────────────────
# CHART BUILDER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def build_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    show_vol: bool,
    show_grid: bool,
    sma20: bool,
    sma50: bool,
    ema20: bool,
    bb: bool,
) -> go.Figure:
    """
    Build an interactive Plotly candlestick chart with optional
    moving average overlays and a volume subplot.
    """
    rows = 2 if show_vol else 1
    row_heights = [0.75, 0.25] if show_vol else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # --- Candlestick ---
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    close = df["Close"]

    # --- SMA 20 overlay ---
    if sma20:
        sma20_vals = compute_sma(close, 20)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=sma20_vals,
                name="SMA 20",
                line=dict(color="#FF9800", width=1.5),
                hovertemplate="SMA20: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- SMA 50 overlay ---
    if sma50:
        sma50_vals = compute_sma(close, 50)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=sma50_vals,
                name="SMA 50",
                line=dict(color="#9C27B0", width=1.5),
                hovertemplate="SMA50: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- EMA 20 overlay ---
    if ema20:
        ema20_vals = compute_ema(close, 20)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ema20_vals,
                name="EMA 20",
                line=dict(color="#03A9F4", width=1.5, dash="dot"),
                hovertemplate="EMA20: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- Bollinger Bands overlay ---
    if bb:
        upper, mid, lower = compute_bollinger_bands(close)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=upper,
                name="BB Upper",
                line=dict(color="rgba(173,216,230,0.8)", width=1),
                hovertemplate="BB Upper: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=mid,
                name="BB Mid",
                line=dict(color="rgba(173,216,230,0.5)", width=1, dash="dash"),
                hovertemplate="BB Mid: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=lower,
                name="BB Lower",
                line=dict(color="rgba(173,216,230,0.8)", width=1),
                fill="tonexty",
                fillcolor="rgba(173,216,230,0.07)",
                hovertemplate="BB Lower: %{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- Volume bar chart ---
    if show_vol and "Volume" in df.columns:
        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.7,
                hovertemplate="Vol: %{y:,.0f}<extra></extra>",
            ),
            row=2, col=1,
        )
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    # --- Layout styling ---
    grid_opts = dict(showgrid=show_grid, gridcolor="rgba(128,128,128,0.2)")
    fig.update_layout(
        title=f"📈 {ticker} — Price History",
        xaxis_rangeslider_visible=True if not show_vol else False,
        hovermode="x unified",
        height=520 if show_vol else 420,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(size=12),
    )
    fig.update_xaxes(**grid_opts)
    fig.update_yaxes(title_text="Price", row=1, col=1, **grid_opts)

    return fig


def build_rsi_chart(rsi: pd.Series, show_grid: bool) -> go.Figure:
    """Build a standalone RSI chart with overbought/oversold bands."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rsi.index, y=rsi,
            name="RSI (14)",
            line=dict(color="#FF9800", width=2),
            hovertemplate="RSI: %{y:.1f}<extra></extra>",
        )
    )
    # Overbought / oversold reference lines
    for level, color, label in [
        (70, "rgba(239,83,80,0.4)", "Overbought 70"),
        (30, "rgba(38,166,154,0.4)", "Oversold 30"),
    ]:
        fig.add_hline(y=level, line_dash="dash", line_color=color, annotation_text=label)

    grid_opts = dict(showgrid=show_grid, gridcolor="rgba(128,128,128,0.2)")
    fig.update_layout(
        title="📉 RSI (14)",
        height=220,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(range=[0, 100], **grid_opts),
        xaxis=grid_opts,
    )
    return fig


def build_macd_chart(macd_df: pd.DataFrame, show_grid: bool) -> go.Figure:
    """Build a standalone MACD chart (line + signal + histogram)."""
    colors = [
        "#26a69a" if v >= 0 else "#ef5350"
        for v in macd_df["histogram"]
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=macd_df.index, y=macd_df["histogram"],
            name="Histogram",
            marker_color=colors,
            opacity=0.6,
            hovertemplate="Hist: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=macd_df.index, y=macd_df["macd"],
            name="MACD",
            line=dict(color="#03A9F4", width=2),
            hovertemplate="MACD: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=macd_df.index, y=macd_df["signal"],
            name="Signal",
            line=dict(color="#FF9800", width=2, dash="dot"),
            hovertemplate="Signal: %{y:.2f}<extra></extra>",
        )
    )
    grid_opts = dict(showgrid=show_grid, gridcolor="rgba(128,128,128,0.2)")
    fig.update_layout(
        title="📉 MACD (12, 26, 9)",
        height=250,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        xaxis=grid_opts,
        yaxis=grid_opts,
    )
    return fig


def build_comparison_chart(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    ticker1: str,
    ticker2: str,
    show_grid: bool,
) -> go.Figure:
    """
    Normalise both Close series to 100 at the common start date
    and plot them on the same Plotly chart.
    """
    close1 = df1["Close"].dropna()
    close2 = df2["Close"].dropna()

    # Align to common dates
    common_idx = close1.index.intersection(close2.index)
    if common_idx.empty:
        return None
    close1 = close1.loc[common_idx]
    close2 = close2.loc[common_idx]

    norm1 = (close1 / close1.iloc[0]) * 100
    norm2 = (close2 / close2.iloc[0]) * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=norm1.index, y=norm1,
            name=ticker1,
            line=dict(color="#26a69a", width=2),
            hovertemplate=f"{ticker1}: %{{y:.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=norm2.index, y=norm2,
            name=ticker2,
            line=dict(color="#FF9800", width=2),
            hovertemplate=f"{ticker2}: %{{y:.2f}}<extra></extra>",
        )
    )
    grid_opts = dict(showgrid=show_grid, gridcolor="rgba(128,128,128,0.2)")
    fig.update_layout(
        title=f"🔀 {ticker1} vs {ticker2} — Normalised to 100",
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        xaxis=grid_opts,
        yaxis=dict(title="Indexed Value (Base = 100)", **grid_opts),
    )
    return fig


# ─────────────────────────────────────────────────────────────
# MAIN DASHBOARD — PAGE HEADER
# ─────────────────────────────────────────────────────────────

st.title("📈 Stock Price History Dashboard")
st.caption("An interactive market data tool to visualize stock price trends.")

# Guard: require a ticker before anything else
if not ticker:
    st.warning("⚠️ Please enter a stock ticker symbol in the sidebar.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# FETCH MAIN DATASET
# ─────────────────────────────────────────────────────────────

with st.spinner(f"Fetching data for **{ticker}** …"):
    df = load_stock_data(ticker, start_date, end_date)

if df.empty:
    st.error(
        f"❌ No data found for **{ticker}** between {start_date} and {end_date}. "
        "Please check the ticker symbol and date range."
    )
    st.stop()

if "Close" not in df.columns:
    st.error("The Close price column is missing from the downloaded data.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# SECTION 4 — KPI METRIC CARDS  (preserved from original)
# ─────────────────────────────────────────────────────────────

# Core price metrics
latest_close = float(df["Close"].iloc[-1])
prev_close   = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_close
price_change = latest_close - prev_close
pct_change   = (price_change / prev_close) * 100 if prev_close != 0 else 0.0

# Currency symbol based on exchange suffix
currency = "₹" if ticker.endswith(".NS") or ticker.endswith(".BO") else "$"

high_val   = float(df["High"].max())
low_val    = float(df["Low"].min())
avg_vol    = int(df["Volume"].mean())    if "Volume" in df.columns else 0
latest_vol = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric(
        label=f"📅 Latest Close",
        value=f"{currency}{latest_close:.2f}",
        help=f"As of {df.index[-1].strftime('%d %b %Y')}",
    )
with m2:
    st.metric(
        label="📊 Day Change",
        value=f"{price_change:+.2f}",
        delta=f"{pct_change:+.2f}%",
        delta_color="normal",
    )
with m3:
    st.metric(
        label="🔺 Period High",
        value=f"{currency}{high_val:.2f}",
        help="Highest price in the selected date range",
    )
with m4:
    st.metric(
        label="🔻 Period Low",
        value=f"{currency}{low_val:.2f}",
        help="Lowest price in the selected date range",
    )
with m5:
    st.metric(
        label="📦 Latest Volume",
        value=f"{latest_vol:,}",
        delta=f"Avg: {avg_vol:,}",
        delta_color="off",
        help="Today's volume vs period average",
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 5 — COMPANY FUNDAMENTALS PANEL
# ─────────────────────────────────────────────────────────────

with st.expander("🏢 Company Fundamentals", expanded=False):
    with st.spinner("Loading company information…"):
        info = load_company_info(ticker)

    if info:
        # Row 1 — Identity
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            st.markdown("**🏷️ Company Name**")
            st.write(safe_get(info, "longName"))
        with f2:
            st.markdown("**🏭 Sector**")
            st.write(safe_get(info, "sector"))
        with f3:
            st.markdown("**🔧 Industry**")
            st.write(safe_get(info, "industry"))
        with f4:
            st.markdown("**🌍 Country**")
            st.write(safe_get(info, "country"))

        st.markdown("")

        # Row 2 — Financials
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            mc_raw = info.get("marketCap")
            mc_str = format_large_number(mc_raw) if mc_raw else "N/A"
            st.markdown("**💰 Market Cap**")
            st.write(mc_str)
        with g2:
            pe = info.get("trailingPE")
            st.markdown("**📐 P/E Ratio**")
            st.write(f"{pe:.2f}" if pe else "N/A")
        with g3:
            dy = info.get("dividendYield")
            st.markdown("**💵 Dividend Yield**")
            st.write(f"{dy * 100:.2f}%" if dy else "N/A")
        with g4:
            emp = info.get("fullTimeEmployees")
            st.markdown("**👥 Employees**")
            st.write(f"{emp:,}" if emp else "N/A")

        st.markdown("")

        # Row 3 — 52-week range + website
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.markdown("**📈 52-Week High**")
            high52 = info.get("fiftyTwoWeekHigh")
            st.write(f"{currency}{high52:.2f}" if high52 else "N/A")
        with h2:
            st.markdown("**📉 52-Week Low**")
            low52 = info.get("fiftyTwoWeekLow")
            st.write(f"{currency}{low52:.2f}" if low52 else "N/A")
        with h3:
            st.markdown("**🌐 Website**")
            website = info.get("website", "")
            if website:
                st.markdown(f"[{website}]({website})")
            else:
                st.write("N/A")
        with h4:
            st.markdown("**📋 Exchange**")
            st.write(safe_get(info, "exchange"))
    else:
        st.info("ℹ️ Company information is not available for this ticker.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 6 — CANDLESTICK CHART + TECHNICAL OVERLAYS
# ─────────────────────────────────────────────────────────────

# Main chart column | AI column (preserves original 2:1 layout)
chart_col, ai_col = st.columns([2, 1], gap="large")

with chart_col:
    st.subheader(f"📈 Price Trend — {ticker}")
    try:
        candle_fig = build_candlestick_chart(
            df=df,
            ticker=ticker,
            show_vol=show_volume,
            show_grid=show_grid,
            sma20=ind_sma20,
            sma50=ind_sma50,
            ema20=ind_ema20,
            bb=ind_bb,
        )
        st.plotly_chart(candle_fig, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")

# ─────────────────────────────────────────────────────────────
# SECTION 7 — RSI / MACD SUB-CHARTS (inside chart_col)
# ─────────────────────────────────────────────────────────────

    if ind_rsi:
        try:
            rsi_series = compute_rsi(df["Close"])
            st.plotly_chart(
                build_rsi_chart(rsi_series, show_grid),
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"RSI calculation error: {e}")

    if ind_macd:
        try:
            macd_df = compute_macd(df["Close"])
            st.plotly_chart(
                build_macd_chart(macd_df, show_grid),
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"MACD calculation error: {e}")

# ─────────────────────────────────────────────────────────────
# SECTION 11 — AI MARKET COMMENTARY  (preserved from original)
# ─────────────────────────────────────────────────────────────

with ai_col:
    st.subheader("🤖 AI Market Commentary")
    with st.spinner("Generating AI commentary…"):
        try:
            from groq import Groq
            GROQ_API_KEY = ""
            client = Groq(api_key=GROQ_API_KEY)

            # Fetch last ~10 trading days
            df_10d = load_recent_ohlc(ticker)

            if not df_10d.empty:
                ohlc_summary = ""
                for date, row in df_10d.iterrows():
                    date_str = date.strftime("%Y-%m-%d")
                    ohlc_summary += (
                        f"{date_str}: Open={row['Open']:.2f}, "
                        f"High={row['High']:.2f}, "
                        f"Low={row['Low']:.2f}, "
                        f"Close={row['Close']:.2f}\n"
                    )

                prompt = (
                    f"Here is the last 10 days of daily OHLC data for {ticker}:\n\n"
                    f"{ohlc_summary}\n"
                    "Please analyze the trend and provide your 3-sentence summary."
                )
                SYSTEM_PROMPT = (
                    "You are a junior financial analyst summarizing stock price charts.\n"
                    "Based on the provided last 10 days of daily OHLC data, write a plain-English summary of the recent trend.\n"
                    "Rules:\n"
                    "1. The summary MUST be exactly 3 sentences long. No more, no less.\n"
                    "2. Only describe the trend. Never give buy or sell recommendations.\n"
                    "3. If you are uncertain about the direction of the trend, clearly flag that uncertainty.\n"
                    "4. Do not include any greeting, intro, outro, markdown formatting, or bullet points. Just output the 3 sentences."
                )

                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=250,
                    temperature=0.3,
                )
                commentary = completion.choices[0].message.content.strip()
                commentary = " ".join(commentary.split())
                st.info(commentary)
            else:
                st.warning("Insufficient data to generate AI commentary.")
        except Exception as e:
            st.error(f"Error generating AI commentary: {e}")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────
    # SECTION 12 — AI CHAT: "Ask AI About This Stock"
    # ─────────────────────────────────────────────────────────

    st.subheader("💬 Ask AI About This Stock")
    st.caption(
        "Ask questions about the price data, indicators, or news. "
        "The AI will not give investment advice or predictions."
    )

    # Example question hints
    example_questions = [
        "Summarize the trend",
        "What happened today?",
        "Explain the volatility",
        "Is momentum increasing?",
    ]
    st.markdown(
        "**Examples:** "
        + " · ".join(f"*{q}*" for q in example_questions)
    )

    user_question = st.text_input(
        "Your question:",
        key="ai_chat_input",
        placeholder="e.g. What does the RSI suggest?",
    )

    if user_question.strip():
        with st.spinner("AI is thinking…"):
            try:
                from groq import Groq
                GROQ_API_KEY = ""
                client = Groq(api_key=GROQ_API_KEY)

                # Build data context for the AI
                close = df["Close"]
                data_ctx = f"Stock: {ticker}\nDate range: {start_date} to {end_date}\n"
                data_ctx += f"Latest close: {currency}{latest_close:.2f}\n"
                data_ctx += f"Period high: {currency}{high_val:.2f}, Period low: {currency}{low_val:.2f}\n"
                data_ctx += f"Day change: {price_change:+.2f} ({pct_change:+.2f}%)\n"

                # Append indicator values if enabled
                if ind_sma20:
                    sma20_last = compute_sma(close, 20).iloc[-1]
                    data_ctx += f"SMA 20 (latest): {sma20_last:.2f}\n"
                if ind_sma50:
                    sma50_last = compute_sma(close, 50).iloc[-1]
                    data_ctx += f"SMA 50 (latest): {sma50_last:.2f}\n"
                if ind_ema20:
                    ema20_last = compute_ema(close, 20).iloc[-1]
                    data_ctx += f"EMA 20 (latest): {ema20_last:.2f}\n"
                if ind_rsi:
                    rsi_last = compute_rsi(close).iloc[-1]
                    data_ctx += f"RSI (14, latest): {rsi_last:.1f}\n"
                if ind_macd:
                    macd_last = compute_macd(close).iloc[-1]
                    data_ctx += (
                        f"MACD: {macd_last['macd']:.2f}, "
                        f"Signal: {macd_last['signal']:.2f}, "
                        f"Hist: {macd_last['histogram']:.2f}\n"
                    )

                # Recent OHLC summary
                df_recent = load_recent_ohlc(ticker)
                if not df_recent.empty:
                    data_ctx += "\nLast 10 trading days OHLC:\n"
                    for date, row in df_recent.iterrows():
                        data_ctx += (
                            f"  {date.strftime('%Y-%m-%d')}: "
                            f"O={row['Open']:.2f} H={row['High']:.2f} "
                            f"L={row['Low']:.2f} C={row['Close']:.2f}\n"
                        )

                AI_CHAT_SYSTEM = (
                    "You are a helpful financial data assistant.\n"
                    "You have been given a set of stock market data for a specific ticker.\n"
                    "Rules (strictly follow):\n"
                    "1. Answer ONLY based on the provided data. Do not fabricate any information.\n"
                    "2. NEVER provide investment advice, buy/sell recommendations, or price predictions.\n"
                    "3. If the user asks for predictions or recommendations, politely refuse and "
                    "describe only what the observable data shows.\n"
                    "4. Keep the answer concise (3–5 sentences max).\n"
                    "5. Use plain English. No markdown headers or bullet lists.\n"
                )

                ai_chat_prompt = (
                    f"Here is the available market data:\n\n{data_ctx}\n\n"
                    f"User question: {user_question}"
                )

                chat_response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": AI_CHAT_SYSTEM},
                        {"role": "user",   "content": ai_chat_prompt},
                    ],
                    max_tokens=300,
                    temperature=0.3,
                )
                answer = chat_response.choices[0].message.content.strip()
                answer = " ".join(answer.split())
                st.success(answer)
            except Exception as e:
                st.error(f"AI Chat error: {e}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 8 — PERFORMANCE STATISTICS
# ─────────────────────────────────────────────────────────────

st.subheader("📊 Performance Statistics")

try:
    daily_returns = df["Close"].pct_change().dropna()

    # Metrics
    total_return  = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
    todays_return = pct_change
    avg_daily_ret = daily_returns.mean() * 100
    winning_days  = int((daily_returns > 0).sum())
    losing_days   = int((daily_returns < 0).sum())
    largest_gain  = float(daily_returns.max() * 100)
    largest_loss  = float(daily_returns.min() * 100)
    ann_volatility = float(daily_returns.std() * np.sqrt(252) * 100)

    p1, p2, p3, p4, p5, p6, p7, p8 = st.columns(8)
    with p1:
        st.metric("📈 Total Return", f"{total_return:+.2f}%")
    with p2:
        st.metric("📅 Today's Return", f"{todays_return:+.2f}%")
    with p3:
        st.metric("📊 Avg Daily Return", f"{avg_daily_ret:+.3f}%")
    with p4:
        st.metric("✅ Winning Days", f"{winning_days}")
    with p5:
        st.metric("❌ Losing Days", f"{losing_days}")
    with p6:
        st.metric("🚀 Largest Gain", f"{largest_gain:+.2f}%")
    with p7:
        st.metric("💥 Largest Loss", f"{largest_loss:+.2f}%")
    with p8:
        st.metric("📉 Ann. Volatility", f"{ann_volatility:.2f}%")

except Exception as e:
    st.warning(f"Could not compute performance statistics: {e}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 9 — STOCK COMPARISON CHART
# ─────────────────────────────────────────────────────────────

if compare_ticker:
    st.subheader(f"🔀 Stock Comparison: {ticker} vs {compare_ticker}")
    with st.spinner(f"Fetching data for {compare_ticker}…"):
        df_compare = load_stock_data(compare_ticker, start_date, end_date)

    if df_compare.empty or "Close" not in df_compare.columns:
        st.warning(
            f"⚠️ No data found for **{compare_ticker}**. "
            "Please check the ticker symbol."
        )
    else:
        try:
            comp_fig = build_comparison_chart(df, df_compare, ticker, compare_ticker, show_grid)
            if comp_fig:
                st.plotly_chart(comp_fig, use_container_width=True)
            else:
                st.warning("No common trading dates found for the two tickers.")
        except Exception as e:
            st.error(f"Comparison chart error: {e}")

    st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 10 — NEWS PANEL + AI NEWS SUMMARY
# ─────────────────────────────────────────────────────────────

st.subheader("📰 Latest News")

with st.spinner("Fetching news…"):
    articles = load_news(ticker)

if articles:
    news_texts = []   # collect real titles for AI summary
    for i, article in enumerate(articles):
        # Use the schema-agnostic extractor (handles flat + nested yfinance formats)
        fields    = extract_article_fields(article)
        title     = fields["title"]
        publisher = fields["publisher"]
        link      = fields["link"]
        pub_time  = fields["pub_time"]

        # Format publish timestamp
        if pub_time:
            try:
                pub_dt   = datetime.datetime.fromtimestamp(pub_time)
                time_str = pub_dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                time_str = "—"
        else:
            time_str = "—"

        # Display article card
        with st.container():
            col_news, col_meta = st.columns([3, 1])
            with col_news:
                if link != "#":
                    st.markdown(f"**[{title}]({link})**")
                else:
                    st.markdown(f"**{title}**")
            with col_meta:
                st.caption(f"🗞️ {publisher}  \n🕐 {time_str}")
            if i < len(articles) - 1:
                st.markdown("<hr style='margin:4px 0;opacity:0.2'>", unsafe_allow_html=True)

        # Only add real titles to the AI summary list
        if title and title != "(Title unavailable)":
            news_texts.append(title)

    # --- AI News Summary (only when we have real headline text) ---
    st.markdown("")
    st.markdown("**🤖 AI News Summary**")
    if not news_texts:
        st.caption(
            "ℹ️ Headline text could not be retrieved for this ticker — "
            "AI summary is unavailable. Try a US-listed ticker (e.g. AAPL, TSLA) "
            "or check your network connection."
        )
    else:
        with st.spinner("Summarizing news with AI…"):
            try:
                from groq import Groq
                GROQ_API_KEY = ""
                client = Groq(api_key=GROQ_API_KEY)

                headlines_block = "\n".join(f"- {t}" for t in news_texts)
                news_prompt = (
                    f"Here are the latest news headlines for {ticker}:\n\n"
                    f"{headlines_block}\n\n"
                    "Provide a concise 3-sentence summary of what these headlines cover."
                )
                NEWS_SYSTEM = (
                    "You are a neutral financial news summarizer.\n"
                    "Rules:\n"
                    "1. Write exactly 3 sentences.\n"
                    "2. Only summarize the news. Do not give investment advice.\n"
                    "3. Do not add any greeting, intro, or markdown formatting.\n"
                    "4. If headlines are unrelated, summarize each theme briefly."
                )
                news_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": NEWS_SYSTEM},
                        {"role": "user",   "content": news_prompt},
                    ],
                    max_tokens=200,
                    temperature=0.3,
                )
                news_summary = news_completion.choices[0].message.content.strip()
                news_summary = " ".join(news_summary.split())
                st.info(news_summary)
            except Exception as e:
                st.warning(f"Could not generate AI news summary: {e}")
else:
    st.info(f"ℹ️ No recent news available for **{ticker}**.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SECTION 13 — RAW DATA TABLE  (preserved from original)
# ─────────────────────────────────────────────────────────────

with st.expander("📋 View Raw Data (Recent 5 Days)"):
    cols_to_show = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    st.dataframe(
        df.tail(5)[cols_to_show].style.format("{:.2f}"),
        use_container_width=True,
    )
