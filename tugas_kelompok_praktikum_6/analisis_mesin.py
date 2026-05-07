import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import json, os, warnings
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "figure.facecolor":  "#0f1117",
    "axes.facecolor":    "#1a1d27",
    "axes.edgecolor":    "#3a3d4f",
    "axes.labelcolor":   "#c8ccd8",
    "xtick.color":       "#8a8d9f",
    "ytick.color":       "#8a8d9f",
    "text.color":        "#c8ccd8",
    "grid.color":        "#2a2d3f",
    "legend.facecolor":  "#1a1d27",
    "legend.edgecolor":  "#3a3d4f",
    "font.family":       "monospace",
})

WARNA_LOKASI = [
    "#4fc3f7", "#81c784", "#ffb74d", "#e57373",
    "#ba68c8", "#4db6ac", "#ff8a65", "#90a4ae",
    "#f48fb1", "#a5d6a7",
]

def ambil_data(uri="mongodb://localhost:27017/", jam=24):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db     = client["kelompok6"]

        batas_waktu = (datetime.now(timezone.utc) - timedelta(hours=jam)).isoformat()

        raw  = list(db["kesehatan_mesin"].find(
            {"timestamp": {"$gte": batas_waktu}}, {"_id": 0}
        ))
        alrt = list(db["alert_mesin"].find(
            {"timestamp": {"$gte": batas_waktu}}, {"_id": 0}
        ))
        return raw, alrt
    except Exception as e:
        print(f"❌ Gagal mengambil data: {e}")
        return [], []


def proses_df(raw):
    if not raw:
        return None
    df = pd.DataFrame(raw)
    df["timestamp"]   = pd.to_datetime(df["timestamp"], utc=True)
    df["jam"]         = df["timestamp"].dt.floor("h")
    df["menit"]       = df["timestamp"].dt.floor("min")

    num_cols = ["vibration_z", "casing_temp", "oil_pressure", "current_amp", "health_score", "rul_jam"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# ── Z-score anomaly detection ───────────────────────────────
def tandai_anomali(df, kolom="vibration_z", threshold=2.5):
    df = df.copy()
    mean = df[kolom].mean()
    std  = df[kolom].std()
    df[f"z_{kolom}"]       = (df[kolom] - mean) / (std + 1e-9)
    df[f"anomali_{kolom}"] = df[f"z_{kolom}"].abs() > threshold
    return df


# ── Agregasi per jam per lokasi ─────────────────────────────
def agregasi_jam(df):
    cols = [c for c in ["vibration_z","casing_temp","oil_pressure","current_amp","health_score","rul_jam"] if c in df.columns]
    return df.groupby(["lokasi","jam"])[cols].mean().reset_index().round(2)


# ── Buat dashboard PNG ──────────────────────────────────────
def buat_dashboard(df, df_agg, df_alert_raw, out="dashboard_tren_mesin.png"):
    if df is None or df.empty:
        print("⚠️  Data kosong, grafik tidak dibuat.")
        return

    df = tandai_anomali(df, "vibration_z")
    df = tandai_anomali(df, "casing_temp")

    lokasi_list = sorted(df["lokasi"].unique())
    warna       = {l: WARNA_LOKASI[i % len(WARNA_LOKASI)] for i, l in enumerate(lokasi_list)}

    fig = plt.figure(figsize=(22, 26), facecolor="#0f1117")
    gs  = gridspec.GridSpec(5, 2, figure=fig, hspace=0.55, wspace=0.35,
                             top=0.95, bottom=0.04, left=0.06, right=0.97)

    fig.suptitle(
        "⚙️  PREDICTIVE MAINTENANCE – ANALISIS MESIN PABRIK",
        fontsize=18, fontweight="bold", color="#ffffff", y=0.98
    )

    # ── Panel 1: Tren getaran ──────────────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    for lok in lokasi_list:
        d = df_agg[df_agg["lokasi"] == lok]
        ax1.plot(d["jam"], d["vibration_z"], marker="o", ms=4,
                 label=lok, color=warna[lok], linewidth=1.6)
    ax1.axhline(15.0, color="#ff4b4b", ls="--", lw=1.5, label="Batas Bahaya (15 mm/s)")
    ax1.axhline(10.0, color="#ffb74d", ls=":",  lw=1.2, label="Batas Waspada (10 mm/s)")
    ax1.set_title("Tren Rata-Rata Getaran per Jam (semua lokasi)", pad=8, color="#ffffff")
    ax1.set_ylabel("Vibration Z (mm/s)")
    ax1.legend(loc="upper right", fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.3)

    # ── Panel 2: Tren suhu ─────────────────────────────────
    ax2 = fig.add_subplot(gs[1, :])
    for lok in lokasi_list:
        d = df_agg[df_agg["lokasi"] == lok]
        ax2.plot(d["jam"], d["casing_temp"], marker="s", ms=4,
                 label=lok, color=warna[lok], linewidth=1.6)
    ax2.axhline(90.0, color="#ff4b4b", ls="--", lw=1.5, label="Batas Overheat (90°C)")
    ax2.axhline(75.0, color="#ffb74d", ls=":",  lw=1.2, label="Batas Waspada (75°C)")
    ax2.set_title("Tren Rata-Rata Suhu per Jam (semua lokasi)", pad=8, color="#ffffff")
    ax2.set_ylabel("Casing Temp (°C)")
    ax2.legend(loc="upper right", fontsize=7, ncol=3)
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: Health score per sensor ──────────────────
    ax3 = fig.add_subplot(gs[2, 0])
    if "health_score" in df.columns and "sensor_id" in df.columns:
        hs = df.groupby("sensor_id")["health_score"].mean().sort_values()
        colors_bar = ["#ff4b4b" if v < 40 else "#ffb74d" if v < 70 else "#66bb6a" for v in hs.values]
        hs.plot(kind="barh", ax=ax3, color=colors_bar, edgecolor="none")
        ax3.axvline(40, color="#ff4b4b", ls="--", lw=1.2)
        ax3.axvline(70, color="#ffb74d", ls=":",  lw=1.2)
        ax3.set_title("Rata-rata Health Score per Mesin", color="#ffffff", pad=8)
        ax3.set_xlabel("Health Score (%)")
        ax3.set_xlim(0, 105)
        ax3.grid(axis="x", alpha=0.3)

    # ── Panel 4: Distribusi health score ──────────────────
    ax4 = fig.add_subplot(gs[2, 1])
    if "health_score" in df.columns:
        vals = df["health_score"].dropna()
        ax4.hist(vals, bins=30, color="#4fc3f7", edgecolor="#0f1117", alpha=0.85)
        ax4.axvline(40, color="#ff4b4b", ls="--", lw=1.5, label="Batas Kritis (40)")
        ax4.axvline(70, color="#ffb74d", ls="--", lw=1.5, label="Batas Waspada (70)")
        ax4.set_title("Distribusi Health Score", color="#ffffff", pad=8)
        ax4.set_xlabel("Health Score (%)")
        ax4.set_ylabel("Frekuensi")
        ax4.legend(fontsize=8)
        ax4.grid(axis="y", alpha=0.3)

    # ── Panel 5: Scatter suhu vs getaran + anomali ────────
    ax5 = fig.add_subplot(gs[3, 0])
    normal  = df[~df["anomali_vibration_z"] & ~df["anomali_casing_temp"]]
    anomali = df[ df["anomali_vibration_z"] |  df["anomali_casing_temp"]]
    ax5.scatter(normal["casing_temp"],  normal["vibration_z"],
                c="#4fc3f7", alpha=0.3, s=8,  label="Normal")
    ax5.scatter(anomali["casing_temp"], anomali["vibration_z"],
                c="#ff4b4b", alpha=0.7, s=20, label="Anomali", marker="x")
    ax5.axhline(15.0, color="#ff4b4b", ls="--", lw=1.2)
    ax5.axvline(90.0, color="#ff4b4b", ls="--", lw=1.2)
    ax5.set_title("Korelasi Suhu × Getaran (anomali merah)", color="#ffffff", pad=8)
    ax5.set_xlabel("Casing Temp (°C)")
    ax5.set_ylabel("Vibration Z (mm/s)")
    ax5.legend(fontsize=8)
    ax5.grid(alpha=0.3)

    # ── Panel 6: RUL per sensor ───────────────────────────
    ax6 = fig.add_subplot(gs[3, 1])
    if "rul_jam" in df.columns and "sensor_id" in df.columns:
        rul = df.groupby("sensor_id")["rul_jam"].mean().sort_values()
        colors_rul = ["#ff4b4b" if v < 500 else "#ffb74d" if v < 2000 else "#66bb6a" for v in rul.values]
        rul.plot(kind="barh", ax=ax6, color=colors_rul, edgecolor="none")
        ax6.axvline(500,  color="#ff4b4b", ls="--", lw=1.2, label="< 500 jam – Ganti segera")
        ax6.axvline(2000, color="#ffb74d", ls=":",  lw=1.2, label="< 2000 jam – Pantau ketat")
        ax6.set_title("Estimasi Remaining Useful Life (RUL)", color="#ffffff", pad=8)
        ax6.set_xlabel("Jam")
        ax6.legend(fontsize=7)
        ax6.grid(axis="x", alpha=0.3)

    # ── Panel 7: Heatmap alert per jam ────────────────────
    ax7 = fig.add_subplot(gs[4, :])
    if df_alert_raw:
        df_al = pd.DataFrame(df_alert_raw)
        df_al["timestamp"] = pd.to_datetime(df_al["timestamp"], utc=True)
        df_al["jam"]       = df_al["timestamp"].dt.floor("h")
        if "sensor_id" in df_al.columns:
            pivot = df_al.groupby(["sensor_id", "jam"]).size().unstack(fill_value=0)
            cmap  = LinearSegmentedColormap.from_list("alert", ["#1a1d27", "#ffb74d", "#ff4b4b"])
            sns.heatmap(pivot, ax=ax7, cmap=cmap, linewidths=0.3,
                        linecolor="#0f1117", cbar_kws={"label": "Jumlah Alert"})
            ax7.set_title("Heatmap Frekuensi Alert per Mesin per Jam", color="#ffffff", pad=8)
            ax7.set_xlabel("Jam")
            ax7.set_ylabel("")
            ax7.tick_params(axis="x", rotation=30, labelsize=7)
    else:
        ax7.text(0.5, 0.5, "Belum ada data alert",
                 ha="center", va="center", color="#8a8d9f", fontsize=12)
        ax7.set_title("Heatmap Alert", color="#ffffff")
        ax7.axis("off")

    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0f1117")
    print(f"✅ Dashboard disimpan: {out}")


# ── Export CSV & JSON ringkasan ─────────────────────────────
def ekspor(df, df_agg, out_csv="data_24jam_mesin.csv", out_json="ringkasan_mesin.json"):
    if df is None:
        return

    df_agg.to_csv(out_csv, index=False)
    print(f"✅ CSV disimpan : {out_csv}")

    if "sensor_id" in df.columns:
        ring = df.groupby("sensor_id").agg(
            rata_getaran=("vibration_z",  "mean"),
            rata_suhu   =("casing_temp",  "mean"),
            rata_health =("health_score", "mean"),
            min_rul     =("rul_jam",      "min"),
            jumlah_data =("sensor_id",    "count"),
        ).round(2).reset_index()
        ring.to_json(out_json, orient="records", indent=2)
        print(f"✅ JSON disimpan: {out_json}")


# ── Main ────────────────────────────────────────────────────
def main():
    print("⏳ Memulai analisis data historis (24 jam terakhir)...")
    raw, alrt = ambil_data()
    print(f"   Data sensor : {len(raw):,} dokumen")
    print(f"   Data alert  : {len(alrt):,} dokumen")

    df     = proses_df(raw)
    df_agg = agregasi_jam(df) if df is not None else None

    if df is not None:
        print("\n── Pratinjau DataFrame ──")
        print(df[["sensor_id","vibration_z","casing_temp","health_score","rul_jam"]].head(8).to_string(index=False))
        print()
        buat_dashboard(df, df_agg, alrt)
        ekspor(df, df_agg)
    else:
        print("❌ Tidak ada data. Jalankan publisher & subscriber terlebih dahulu.")


if __name__ == "__main__":
    main()