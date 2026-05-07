import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import time

# ── Konfigurasi halaman ─────────────────────────────────────
st.set_page_config(
    page_title="PredMaint Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS kustom – dark industrial theme ─────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Rajdhani:wght@400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    background-color: #0c0e14;
    color: #c8ccd8;
  }
  .main .block-container { padding: 1.2rem 2rem 2rem; max-width: 100%; }

  /* Header strip */
  .dash-header {
    background: linear-gradient(135deg, #1a1d27 0%, #12151f 100%);
    border-left: 4px solid #4fc3f7;
    padding: 1rem 1.5rem;
    border-radius: 4px;
    margin-bottom: 1.2rem;
    display: flex; align-items: center; gap: 1rem;
  }
  .dash-title  { font-size: 1.7rem; font-weight: 700; color: #ffffff; margin: 0; letter-spacing: 1px; }
  .dash-sub    { font-size: 0.82rem; color: #7a7d8f; font-family: 'JetBrains Mono', monospace; margin: 0; }
  .dot-live    { width: 10px; height: 10px; border-radius: 50%; background: #4caf50;
                 animation: pulse 1.4s ease-in-out infinite; display: inline-block; }
  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(76,175,80,0.6); }
    50%       { box-shadow: 0 0 0 8px rgba(76,175,80,0); }
  }

  /* KPI cards */
  .kpi-card {
    background: #12151f;
    border: 1px solid #1e2130;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    text-align: center;
    transition: border-color 0.3s;
  }
  .kpi-card:hover { border-color: #4fc3f7; }
  .kpi-label { font-size: 0.72rem; color: #7a7d8f; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
  .kpi-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono'; line-height: 1; }
  .kpi-sub   { font-size: 0.7rem; color: #5a5d6f; margin-top: 4px; }

  /* Mesin cards */
  .mesin-card {
    background: #12151f;
    border: 1px solid #1e2130;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    font-size: 0.82rem;
    transition: all 0.2s;
  }
  .mesin-card:hover { border-color: #4fc3f7; transform: translateY(-1px); }
  .mesin-card.bahaya  { border-left: 3px solid #ff4b4b; }
  .mesin-card.waspada { border-left: 3px solid #ffb74d; }
  .mesin-card.normal  { border-left: 3px solid #66bb6a; }

  .mesin-id    { font-weight: 700; font-size: 0.9rem; color: #e0e3f0; font-family: 'JetBrains Mono'; }
  .mesin-loc   { color: #6a6d7f; font-size: 0.72rem; }
  .badge-bahaya  { background:#ff4b4b22; color:#ff4b4b; border:1px solid #ff4b4b44;
                   border-radius:4px; padding:1px 6px; font-size:0.68rem; font-weight:600; }
  .badge-waspada { background:#ffb74d22; color:#ffb74d; border:1px solid #ffb74d44;
                   border-radius:4px; padding:1px 6px; font-size:0.68rem; font-weight:600; }
  .badge-normal  { background:#66bb6a22; color:#66bb6a; border:1px solid #66bb6a44;
                   border-radius:4px; padding:1px 6px; font-size:0.68rem; font-weight:600; }

  /* Metric rows */
  .m-row { display:flex; justify-content:space-between; margin: 3px 0; }
  .m-lbl { color:#7a7d8f; } .m-val { font-family:'JetBrains Mono'; color:#c8ccd8; }

  /* Health bar */
  .health-bar-bg { background:#1e2130; border-radius:4px; height:6px; margin:6px 0; overflow:hidden; }
  .health-bar-fill { height:100%; border-radius:4px; transition: width 0.5s; }

  /* Alert row */
  .alert-row { background:#12151f; border-radius:6px; padding:8px 12px;
               margin-bottom:6px; border-left:3px solid #ff4b4b; font-size:0.8rem; }
  .alert-row.waspada { border-left-color: #ffb74d; }
  .alert-time  { font-family:'JetBrains Mono'; font-size:0.68rem; color:#6a6d7f; }

  /* Tab overrides */
  [data-baseweb="tab-list"] { background:#12151f !important; border-radius:8px; gap:4px; }
  [data-baseweb="tab"]      { color:#7a7d8f !important; font-weight:600; border-radius:6px; }
  [aria-selected="true"]    { background:#1e2130 !important; color:#4fc3f7 !important; }

  /* Sidebar */
  [data-testid="stSidebar"] { background:#0c0e14 !important; border-right:1px solid #1e2130; }
  [data-testid="stSidebar"] .stMarkdown p { color:#8a8d9f; font-size:0.82rem; }

  /* Scrollbar */
  ::-webkit-scrollbar { width:6px; }
  ::-webkit-scrollbar-track { background:#0c0e14; }
  ::-webkit-scrollbar-thumb { background:#2a2d3f; border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ── Koneksi MongoDB ─────────────────────────────────────────
@st.cache_resource
def init_db():
    c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    return c["kelompok6"]

try:
    db = init_db()
except Exception as e:
    st.error(f"❌ Gagal terhubung MongoDB: {e}")
    st.stop()


# ── Query helpers ───────────────────────────────────────────
def get_summary():
    """Ambil summary terkini setiap sensor dari koleksi summary_mesin."""
    return list(db["summary_mesin"].find({}, {"_id": 0}))


def get_tren(jam=1):
    """Data time-series untuk grafik tren (n jam terakhir)."""
    batas = (datetime.now(timezone.utc) - timedelta(hours=jam)).isoformat()
    raw   = list(db["kesehatan_mesin"].find(
        {"timestamp": {"$gte": batas}}, {"_id": 0,
         "sensor_id":1,"lokasi":1,"vibration_z":1,"casing_temp":1,
         "health_score":1,"oil_pressure":1,"current_amp":1,"timestamp":1}
    ))
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_lokal"]  = df["timestamp"].dt.tz_convert("Asia/Jakarta")
    return df.sort_values("timestamp")


def get_alerts(limit=50, tingkat=None):
    filt = {}
    if tingkat and tingkat != "Semua":
        filt["tingkat"] = tingkat.lower()
    return list(db["alert_mesin"].find(filt, {"_id": 0}).sort("timestamp", -1).limit(limit))


def get_alert_count():
    satu_jam = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    return db["alert_mesin"].count_documents({"timestamp": {"$gte": satu_jam}})


# ── Warna status ────────────────────────────────────────────
def status_info(health):
    if health < 40:
        return "bahaya",  "#ff4b4b", "🔴 KRITIS",  "badge-bahaya"
    elif health < 70:
        return "waspada", "#ffb74d", "🟡 WASPADA", "badge-waspada"
    else:
        return "normal",  "#66bb6a", "🟢 Normal",  "badge-normal"


# ── Gauge chart (Plotly) ────────────────────────────────────
def gauge(val, title, max_val=100, unit="", red_lo=None, red_hi=None, warn_lo=None, warn_hi=None):
    """Buat gauge/indicator Plotly."""
    if red_hi:   # nilai tinggi = bahaya
        color = "#ff4b4b" if val > red_hi else "#ffb74d" if val > warn_hi else "#66bb6a"
    elif red_lo is not None:  # nilai rendah = bahaya
        color = "#ff4b4b" if val < red_lo else "#ffb74d" if val < warn_lo else "#66bb6a"
    else:
        color = "#4fc3f7"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={"suffix": unit, "font": {"size": 18, "color": "#c8ccd8", "family": "JetBrains Mono"}},
        title={"text": title, "font": {"size": 11, "color": "#8a8d9f"}},
        gauge={
            "axis":    {"range": [0, max_val], "tickcolor": "#3a3d4f", "tickwidth": 1,
                        "tickfont": {"size": 9, "color": "#5a5d6f"}},
            "bar":     {"color": color, "thickness": 0.22},
            "bgcolor": "#1a1d27",
            "borderwidth": 0,
            "steps": [
                {"range": [0, max_val * 0.4], "color": "rgba(255, 75, 75, 0.1)"},
                {"range": [max_val * 0.4, max_val * 0.7], "color": "rgba(255, 183, 77, 0.1)"}, 
                {"range": [max_val * 0.7, max_val], "color": "rgba(102, 187, 106, 0.1)"},  
            ],
        }
    ))
    fig.update_layout(
        height=140, margin=dict(l=10, r=10, t=30, b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#c8ccd8"},
    )
    return fig


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Pengaturan")
    auto_refresh   = st.toggle("🔄 Auto Refresh", value=True)
    refresh_detik  = st.slider("Interval refresh (detik)", 3, 30, 5, step=1)
    jam_tren       = st.selectbox("Rentang Tren", [1, 3, 6, 12, 24], index=0, format_func=lambda x: f"{x} Jam")
    filter_lokasi  = st.multiselect("Filter Lokasi", options=[
        "Jalur Perakitan 1", "Sektor Pemotongan", "Jalur Distribusi",
        "Sektor Pencetakan", "Sektor Pengemasan"
    ], default=[])

    st.divider()
    st.markdown("### 📋 Legenda")
    st.markdown("""
    <div style='font-size:0.78rem; line-height:1.9'>
      🟢 <b>Normal</b>  – Health ≥ 70%<br>
      🟡 <b>Waspada</b> – Health 40–69%<br>
      🔴 <b>Kritis</b>  – Health &lt; 40%<br><br>
      <span style='color:#7a7d8f'>Getaran bahaya : &gt; 15 mm/s</span><br>
      <span style='color:#7a7d8f'>Suhu bahaya    : &gt; 90 °C</span><br>
      <span style='color:#7a7d8f'>RUL kritis     : &lt; 500 jam</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Refresh Manual", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ══════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════

placeholder = st.empty()

def render_dashboard():
    with placeholder.container():

        # ── Header ─────────────────────────────────────────
        now_str = datetime.now().strftime("%A, %d %b %Y  |  %H:%M:%S WIB")
        st.markdown(f"""
        <div class="dash-header">
          <span class="dot-live"></span>
          <div>
            <p class="dash-title">⚙️ PREDICTIVE MAINTENANCE SYSTEM</p>
            <p class="dash-sub">Sistem Pemantauan Kesehatan Mesin Pabrik Manufaktur &nbsp;|&nbsp; {now_str}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        summary     = get_summary()
        alert_count = get_alert_count()

        if filter_lokasi:
            summary = [m for m in summary if m.get("lokasi") in filter_lokasi]

        total_mesin  = len(summary)
        mesin_kritis = sum(1 for m in summary if m.get("health_score", 100) < 40)
        mesin_waspada= sum(1 for m in summary if 40 <= m.get("health_score", 100) < 70)
        mesin_normal = total_mesin - mesin_kritis - mesin_waspada
        avg_health   = round(sum(m.get("health_score", 0) for m in summary) / max(total_mesin, 1), 1)

        c1, c2, c3, c4, c5 = st.columns(5)
        kpis = [
            (c1, str(total_mesin),   "#4fc3f7", "Total Mesin",      "unit terpantau"),
            (c2, str(mesin_normal),  "#66bb6a", "Mesin Normal",     "beroperasi baik"),
            (c3, str(mesin_waspada), "#ffb74d", "Mesin Waspada",    "perlu perhatian"),
            (c4, str(mesin_kritis),  "#ff4b4b", "Mesin Kritis",     "tindakan segera"),
            (c5, str(alert_count),   "#ba68c8", "Alert (1 Jam)",    "peringatan aktif"),
        ]
        for col, val, clr, lbl, sub in kpis:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                  <div class="kpi-label">{lbl}</div>
                  <div class="kpi-value" style="color:{clr}">{val}</div>
                  <div class="kpi-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([
            "🖥️  Status Real-Time",
            "📈  Tren & Analisis",
            "🔮  Prediksi RUL",
            "🚨  Log Peringatan",
        ])

        # ══════════════════════════════════════════════════
        #  TAB 1 – Status Real-Time
        # ══════════════════════════════════════════════════
        with tab1:
            if not summary:
                st.info("⏳ Menunggu data dari Publisher & Subscriber…")
            else:
                summary_sorted = sorted(summary, key=lambda m: m.get("health_score", 100))

                cols_per_row = 2
                for i in range(0, len(summary_sorted), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for j, col in enumerate(row_cols):
                        if i + j >= len(summary_sorted):
                            break
                        m      = summary_sorted[i + j]
                        health = m.get("health_score", 0)
                        rul    = m.get("rul_jam", 0)
                        vib    = m.get("vibration_z", 0)
                        temp   = m.get("casing_temp", 0)
                        oil    = m.get("oil_pressure", 0)
                        amp    = m.get("current_amp", 0)
                        cls, clr, lbl_stat, badge_cls = status_info(health)

                        bar_clr = clr
                        ts_raw  = m.get("timestamp", "")
                        try:
                            ts_dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                            ts_str= ts_dt.astimezone(timezone(timedelta(hours=7))).strftime("%H:%M:%S")
                        except:
                            ts_str= ts_raw[:19] if ts_raw else "-"

                        with col:
                            st.markdown(f"""
                            <div class="mesin-card {cls}">
                              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                                <div>
                                  <div class="mesin-id">{m.get('sensor_id','?')}</div>
                                  <div class="mesin-loc">📍 {m.get('lokasi','?')} &nbsp;·&nbsp; {m.get('tipe_mesin','?')}</div>
                                </div>
                                <span class="{badge_cls}">{lbl_stat}</span>
                              </div>

                              <div class="health-bar-bg">
                                <div class="health-bar-fill" style="width:{health}%;background:{bar_clr}"></div>
                              </div>
                              <div style="font-size:0.68rem;color:#6a6d7f;margin-bottom:6px">
                                Health Score: <b style="color:{clr}">{health}%</b>
                              </div>

                              <div class="m-row"><span class="m-lbl">🌡️ Suhu Casing</span><span class="m-val">{temp} °C</span></div>
                              <div class="m-row"><span class="m-lbl">📳 Getaran Z</span><span class="m-val">{vib} mm/s</span></div>
                              <div class="m-row"><span class="m-lbl">🛢️ Tekanan Oli</span><span class="m-val">{oil} bar</span></div>
                              <div class="m-row"><span class="m-lbl">⚡ Arus Listrik</span><span class="m-val">{amp} A</span></div>
                              <div class="m-row"><span class="m-lbl">⏳ Est. RUL</span>
                                <span class="m-val" style="color:{'#ff4b4b' if rul<500 else '#ffb74d' if rul<2000 else '#66bb6a'}">{rul:,} jam</span>
                              </div>
                              <div style="margin-top:6px;font-size:0.65rem;color:#4a4d5f">🕐 Update: {ts_str} WIB</div>
                            </div>""", unsafe_allow_html=True)

                kritis_list = [m for m in summary_sorted if m.get("health_score", 100) < 40]
                if kritis_list:
                    st.markdown("---")
                    st.markdown("#### 🔴 Detail Gauge – Mesin Kritis")
                    for m in kritis_list[:3]:  # maks 3
                        sid = m.get("sensor_id", "?")
                        st.markdown(f"**{sid}**")
                        gcols = st.columns(4)
                        gauges = [
                            (gcols[0], m.get("health_score", 0),  "Health Score",     100,  None,   40,  None,  70,  "%"),
                            (gcols[1], m.get("vibration_z",  0),  "Getaran Z",        30,   15.0,  None, 10.0, None, " mm/s"),
                            (gcols[2], m.get("casing_temp",  0),  "Suhu Casing",      130,  90.0,  None, 75.0, None, " °C"),
                            (gcols[3], m.get("current_amp",  0),  "Arus Listrik",     80,   55.0,  None, 40.0, None, " A"),
                        ]
                        for gc, val, ttl, mx, rhi, rlo, whi, wlo, unit in gauges:
                            with gc:
                                if rlo is not None:  
                                    fig = gauge(val, ttl, mx, unit, red_lo=rlo, warn_lo=wlo)
                                else:                
                                    fig = gauge(val, ttl, mx, unit, red_hi=rhi, warn_hi=whi)
                                st.plotly_chart(fig, use_container_width=True)

        # ══════════════════════════════════════════════════
        #  TAB 2 – Tren & Analisis
        # ══════════════════════════════════════════════════
        with tab2:
            df_tren = get_tren(jam_tren)

            if df_tren.empty:
                st.warning("Belum ada data historis. Jalankan publisher & subscriber.")
            else:
                if filter_lokasi:
                    df_tren = df_tren[df_tren["lokasi"].isin(filter_lokasi)]

                sensors = sorted(df_tren["sensor_id"].unique().tolist()) if "sensor_id" in df_tren.columns else []
                sel_sensor = st.selectbox("Pilih Mesin untuk Detail Tren", ["Semua"] + sensors)

                df_plot = df_tren if sel_sensor == "Semua" else df_tren[df_tren["sensor_id"] == sel_sensor]

                fig_tren = make_subplots(
                    rows=2, cols=1, shared_xaxes=True,
                    subplot_titles=("Getaran Mesin (mm/s)", "Suhu Casing (°C)"),
                    vertical_spacing=0.1
                )
                warna_plotly = px.colors.qualitative.Plotly

                if sel_sensor == "Semua":
                    for i, sid in enumerate(df_plot["sensor_id"].unique()):
                        d  = df_plot[df_plot["sensor_id"] == sid]
                        clr = warna_plotly[i % len(warna_plotly)]
                        fig_tren.add_trace(go.Scatter(x=d["ts_lokal"], y=d["vibration_z"],
                            name=sid, line=dict(color=clr, width=1.2), mode="lines",
                            legendgroup=sid), row=1, col=1)
                        fig_tren.add_trace(go.Scatter(x=d["ts_lokal"], y=d["casing_temp"],
                            name=sid, line=dict(color=clr, width=1.2), mode="lines",
                            legendgroup=sid, showlegend=False), row=2, col=1)
                else:
                    fig_tren.add_trace(go.Scatter(x=df_plot["ts_lokal"], y=df_plot["vibration_z"],
                        name="Getaran", line=dict(color="#4fc3f7", width=2), mode="lines+markers",
                        marker=dict(size=4)), row=1, col=1)
                    fig_tren.add_trace(go.Scatter(x=df_plot["ts_lokal"], y=df_plot["casing_temp"],
                        name="Suhu", line=dict(color="#ff8a65", width=2), mode="lines+markers",
                        marker=dict(size=4)), row=2, col=1)

                fig_tren.add_hline(y=15, line_dash="dash", line_color="#ff4b4b", row=1, col=1, annotation_text="Batas Bahaya")
                fig_tren.add_hline(y=10, line_dash="dot",  line_color="#ffb74d", row=1, col=1, annotation_text="Waspada")
                fig_tren.add_hline(y=90, line_dash="dash", line_color="#ff4b4b", row=2, col=1, annotation_text="Overheat")
                fig_tren.add_hline(y=75, line_dash="dot",  line_color="#ffb74d", row=2, col=1, annotation_text="Waspada")

                fig_tren.update_layout(
                    height=420, paper_bgcolor="#0c0e14", plot_bgcolor="#12151f",
                    font=dict(color="#c8ccd8", size=11),
                    legend=dict(bgcolor="#12151f", bordercolor="#1e2130"),
                    margin=dict(l=50, r=20, t=40, b=20),
                )
                fig_tren.update_xaxes(gridcolor="#1e2130", zerolinecolor="#1e2130")
                fig_tren.update_yaxes(gridcolor="#1e2130", zerolinecolor="#1e2130")
                st.plotly_chart(fig_tren, use_container_width=True)

                st.markdown("#### 🗺️  Heatmap Health Score per Mesin")
                if "sensor_id" in df_tren.columns and "health_score" in df_tren.columns:
                    df_tren["jam_label"] = df_tren["ts_lokal"].dt.strftime("%H:%M")
                    pivot = df_tren.groupby(["sensor_id", "jam_label"])["health_score"].mean().unstack(fill_value=0).round(1)

                    fig_heat = go.Figure(go.Heatmap(
                        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                        colorscale=[[0,"#ff4b4b"],[0.4,"#ffb74d"],[0.7,"#66bb6a"],[1,"#4fc3f7"]],
                        zmin=0, zmax=100,
                        text=pivot.values.round(0).astype(int),
                        texttemplate="%{text}%",
                        colorbar=dict(title="Health%", tickfont=dict(color="#c8ccd8")),
                        hovertemplate="Sensor: %{y}<br>Jam: %{x}<br>Health: %{z:.1f}%<extra></extra>",
                    ))
                    fig_heat.update_layout(
                        height=320, paper_bgcolor="#0c0e14", plot_bgcolor="#12151f",
                        font=dict(color="#c8ccd8", size=10),
                        margin=dict(l=160, r=60, t=10, b=50),
                        xaxis=dict(side="bottom"),
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)

                st.markdown("#### 📊  Statistik Ringkasan")
                if not df_tren.empty:
                    num_cols = [c for c in ["vibration_z","casing_temp","oil_pressure","health_score"] if c in df_tren.columns]
                    stat_df  = df_tren.groupby("sensor_id")[num_cols].agg(["mean","max","min"]).round(2)
                    stat_df.columns = [f"{b}_{a}" for a,b in stat_df.columns]
                    st.dataframe(stat_df, use_container_width=True)

        # ══════════════════════════════════════════════════
        #  TAB 3 – Prediksi RUL
        # ══════════════════════════════════════════════════
        with tab3:
            st.markdown("#### 🔮  Estimasi Remaining Useful Life (RUL) per Mesin")
            if not summary:
                st.info("Belum ada data summary.")
            else:
                rul_data = sorted(
                    [{"sensor_id": m.get("sensor_id"), "rul_jam": m.get("rul_jam", 9999),
                      "health_score": m.get("health_score", 100), "lokasi": m.get("lokasi","")}
                     for m in summary],
                    key=lambda x: x["rul_jam"]
                )
                fig_rul = go.Figure()
                colors_rul = ["#ff4b4b" if r["rul_jam"] < 500 else "#ffb74d" if r["rul_jam"] < 2000 else "#66bb6a"
                              for r in rul_data]
                fig_rul.add_trace(go.Bar(
                    x=[r["rul_jam"] for r in rul_data],
                    y=[r["sensor_id"] for r in rul_data],
                    orientation="h",
                    marker_color=colors_rul,
                    text=[f"{r['rul_jam']:,} jam" for r in rul_data],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>RUL: %{x:,} jam<extra></extra>",
                ))
                fig_rul.add_vline(x=500,  line_dash="dash", line_color="#ff4b4b", annotation_text="Ganti Segera (<500j)")
                fig_rul.add_vline(x=2000, line_dash="dot",  line_color="#ffb74d", annotation_text="Pantau (<2000j)")
                fig_rul.update_layout(
                    height=420, paper_bgcolor="#0c0e14", plot_bgcolor="#12151f",
                    font=dict(color="#c8ccd8", size=11),
                    xaxis=dict(title="Sisa Jam Operasi (jam)", gridcolor="#1e2130"),
                    yaxis=dict(gridcolor="#1e2130"),
                    margin=dict(l=180, r=80, t=20, b=40),
                )
                st.plotly_chart(fig_rul, use_container_width=True)

                df_rul = pd.DataFrame(rul_data)
                df_rul["Status RUL"] = df_rul["rul_jam"].apply(
                    lambda v: "🔴 Ganti Segera" if v < 500 else "🟡 Pantau" if v < 2000 else "🟢 Aman"
                )
                df_rul["Health"] = df_rul["health_score"].apply(lambda v: f"{v:.1f}%")
                df_rul["RUL (jam)"] = df_rul["rul_jam"].apply(lambda v: f"{v:,}")
                st.dataframe(
                    df_rul[["sensor_id", "lokasi", "Health", "RUL (jam)", "Status RUL"]].rename(columns={"sensor_id":"Mesin","lokasi":"Lokasi"}),
                    use_container_width=True, hide_index=True
                )

        # ══════════════════════════════════════════════════
        #  TAB 4 – Log Peringatan
        # ══════════════════════════════════════════════════
        with tab4:
            col_f1, col_f2 = st.columns([1, 3])
            with col_f1:
                filter_tingkat = st.selectbox("Filter Tingkat", ["Semua", "Bahaya", "Waspada"])
            with col_f2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("Menampilkan 50 peringatan terbaru")

            alerts = get_alerts(limit=50, tingkat=filter_tingkat)

            if not alerts:
                st.success("✅ Tidak ada peringatan aktif saat ini.")
            else:
                for a in alerts:
                    tingkat   = a.get("tingkat", "waspada")
                    border_clr= "#ff4b4b" if tingkat == "bahaya" else "#ffb74d"
                    ikon      = "🚨" if tingkat == "bahaya" else "⚠️"
                    ts        = a.get("timestamp", "")
                    try:
                        ts_dt  = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        ts_str = ts_dt.astimezone(timezone(timedelta(hours=7))).strftime("%d/%m %H:%M:%S")
                    except:
                        ts_str = ts[:16] if ts else "-"

                    st.markdown(f"""
                    <div class="alert-row {tingkat}" style="border-left-color:{border_clr}">
                      <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                        <span style="font-weight:700;color:{border_clr}">{ikon} {a.get('sensor_id','?')}</span>
                        <span class="alert-time">{ts_str} WIB</span>
                      </div>
                      <div style="color:#9a9db0;font-size:0.78rem">{a.get('pesan','?')}</div>
                      <div style="font-size:0.72rem;color:#5a5d6f;margin-top:2px">
                        📍 {a.get('lokasi','?')} &nbsp;|&nbsp;
                        Health: {a.get('health_score','?')}% &nbsp;|&nbsp;
                        Vib: {a.get('vibration_z','?')} mm/s &nbsp;|&nbsp;
                        Suhu: {a.get('casing_temp','?')} °C
                      </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("#### 📊  Distribusi Alert per Jenis")
                df_al = pd.DataFrame(alerts)
                if "jenis_alert" in df_al.columns:
                    cnt = df_al["jenis_alert"].value_counts().reset_index()
                    cnt.columns = ["Jenis", "Jumlah"]
                    fig_pie = px.pie(cnt, names="Jenis", values="Jumlah",
                                     color_discrete_sequence=px.colors.sequential.Plasma_r,
                                     hole=0.45)
                    fig_pie.update_layout(
                        height=320, paper_bgcolor="#0c0e14",
                        font=dict(color="#c8ccd8"),
                        legend=dict(bgcolor="#12151f"),
                        margin=dict(l=20, r=20, t=10, b=20),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)


if auto_refresh:
    render_dashboard()
    time.sleep(refresh_detik)
    st.rerun()
else:
    render_dashboard()