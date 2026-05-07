import paho.mqtt.client as mqtt
import time
import json
import random
import math
from datetime import datetime, timezone

# ============================================================
#  KONFIGURASI
# ============================================================
BROKER = "broker.emqx.io"
PORT   = 1883
TOPIC  = "pabrik/mesin/kesehatan"

# ============================================================
#  DEFINISI MESIN – lengkap dengan tipe & profil normal
# ============================================================
daftar_mesin = [
    {"id": "Robot-Arm-A1",      "lokasi": "Jalur Perakitan 1",   "tipe": "robot_arm",       "umur_jam": 4200},
    {"id": "Robot-Arm-A2",      "lokasi": "Jalur Perakitan 1",   "tipe": "robot_arm",       "umur_jam": 3100},
    {"id": "CNC-Machine-B1",    "lokasi": "Sektor Pemotongan",   "tipe": "cnc",             "umur_jam": 8700},
    {"id": "CNC-Machine-B2",    "lokasi": "Sektor Pemotongan",   "tipe": "cnc",             "umur_jam": 2400},
    {"id": "Conveyor-Belt-C1",  "lokasi": "Jalur Distribusi",    "tipe": "conveyor",        "umur_jam": 6300},
    {"id": "Conveyor-Belt-C2",  "lokasi": "Jalur Distribusi",    "tipe": "conveyor",        "umur_jam": 1800},
    {"id": "Hydraulic-Press-D1","lokasi": "Sektor Pencetakan",   "tipe": "hydraulic_press", "umur_jam": 9500},
    {"id": "Hydraulic-Press-D2","lokasi": "Sektor Pencetakan",   "tipe": "hydraulic_press", "umur_jam": 5600},
    {"id": "Packaging-Unit-E1", "lokasi": "Sektor Pengemasan",   "tipe": "packaging",       "umur_jam": 3900},
    {"id": "Packaging-Unit-E2", "lokasi": "Sektor Pengemasan",   "tipe": "packaging",       "umur_jam": 7200},
]

PROFIL = {
    "robot_arm":       {"vib": (2.0, 6.0),   "temp": (45, 65),  "rpm": (1450, 1550), "oil": (3.0, 4.5), "current": (8, 15)},
    "cnc":             {"vib": (3.0, 8.0),   "temp": (50, 72),  "rpm": (800, 1200),  "oil": (2.5, 4.0), "current": (12, 22)},
    "conveyor":        {"vib": (1.5, 5.0),   "temp": (38, 58),  "rpm": (400, 600),   "oil": (1.5, 3.0), "current": (5, 10)},
    "hydraulic_press": {"vib": (4.0, 10.0),  "temp": (55, 78),  "rpm": (200, 400),   "oil": (4.0, 6.0), "current": (20, 35)},
    "packaging":       {"vib": (1.0, 4.0),   "temp": (35, 55),  "rpm": (600, 900),   "oil": (1.0, 2.5), "current": (4, 9)},
}

_state = {m["id"]: {"degradasi": 0.0, "anomali_aktif": False, "tipe_anomali": None} for m in daftar_mesin}


def hitung_health_score(vib, temp, oil, profil):
    """Hitung skor kesehatan 0-100 berdasarkan deviasi dari profil normal."""
    vib_max  = profil["vib"][1]  * 2.5
    temp_max = profil["temp"][1] * 1.5
    oil_min  = profil["oil"][0]  * 0.5

    skor_vib  = max(0, 100 - (vib  / vib_max)  * 100)
    skor_temp = max(0, 100 - (temp / temp_max)  * 100)
    skor_oil  = max(0, min(100, (oil / oil_min) * 50))

    return round((skor_vib * 0.4 + skor_temp * 0.4 + skor_oil * 0.2), 1)


def generate_data(mesin):
    """Hasilkan data sensor realistis dengan pola degradasi bertahap."""
    mid   = mesin["id"]
    tipe  = mesin["tipe"]
    umur  = mesin["umur_jam"]
    p     = PROFIL[tipe]
    st    = _state[mid]

    faktor_umur = min(1.0, umur / 10000)

    if not st["anomali_aktif"] and random.random() < (0.04 + faktor_umur * 0.06):
        st["anomali_aktif"] = True
        st["tipe_anomali"]  = random.choice(["getaran", "suhu", "oli", "listrik", "kombinasi"])
        st["degradasi"]     = min(1.0, st["degradasi"] + 0.1)

    if st["anomali_aktif"] and random.random() < 0.3:
        st["anomali_aktif"] = False

    noise = lambda lo, hi: random.uniform(lo, hi)

    vib  = round(noise(*p["vib"])  * (1 + st["degradasi"] * 0.5), 2)
    temp = round(noise(*p["temp"]) * (1 + st["degradasi"] * 0.3), 2)
    rpm  = random.randint(p["rpm"][0], p["rpm"][1])
    oil  = round(noise(*p["oil"]) * (1 - st["degradasi"] * 0.2), 2)
    amp  = round(noise(*p["current"]) * (1 + st["degradasi"] * 0.15), 2)

    if st["anomali_aktif"]:
        t = st["tipe_anomali"]
        if t in ["getaran", "kombinasi"]:
            vib  = round(random.uniform(p["vib"][1] * 1.8, p["vib"][1] * 3.5), 2)
        if t in ["suhu", "kombinasi"]:
            temp = round(random.uniform(p["temp"][1] * 1.25, p["temp"][1] * 1.6), 2)
        if t in ["oli"]:
            oil  = round(random.uniform(0.2, p["oil"][0] * 0.6), 2)
        if t in ["listrik"]:
            amp  = round(random.uniform(p["current"][1] * 1.5, p["current"][1] * 2.5), 2)

    health = hitung_health_score(vib, temp, oil, p)

    rul = max(0, round(10000 - umur - (st["degradasi"] * 3000)))

    _state[mid]  
    mesin["umur_jam"] = umur + round(random.uniform(0.002, 0.005), 4)

    return {
        "sensor_id":      mid,
        "lokasi":         mesin["lokasi"],
        "tipe_mesin":     tipe,
        "vibration_z":    vib,
        "casing_temp":    temp,
        "rpm":            rpm,
        "oil_pressure":   oil,
        "current_amp":    amp,
        "health_score":   health,
        "rul_jam":        rul,
        "umur_operasi":   round(mesin["umur_jam"], 1),
        "anomali_aktif":  st["anomali_aktif"],
        "tipe_anomali":   st["tipe_anomali"] if st["anomali_aktif"] else None,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
    }


def setup_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Publisher_PredMaint_v2")
    client.connect(BROKER, PORT)
    return client


def main():
    print(f"🚀  Predictive Maintenance Publisher v2.0")
    print(f"    Broker : {BROKER}:{PORT}")
    print(f"    Topic  : {TOPIC}")
    print(f"    Mesin  : {len(daftar_mesin)} unit\n")

    client = setup_mqtt()
    client.loop_start()

    siklus = 0
    try:
        while True:
            siklus += 1
            print(f"\n{'='*60}")
            print(f"  Siklus #{siklus:04d}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            for mesin in daftar_mesin:
                data = generate_data(mesin)
                client.publish(TOPIC, json.dumps(data))

                # Tentukan status tampilan
                if data["health_score"] < 40:
                    ikon = "🔴 KRITIS "
                elif data["health_score"] < 70:
                    ikon = "🟡 WASPADA"
                else:
                    ikon = "🟢 Normal "

                print(
                    f"  {ikon} | {data['sensor_id']:<22} "
                    f"| Vib:{data['vibration_z']:>6} mm/s "
                    f"| Suhu:{data['casing_temp']:>6}°C "
                    f"| Health:{data['health_score']:>5}% "
                    f"| RUL:{data['rul_jam']:>5} jam"
                )
                time.sleep(0.05)

            print(f"\n  ⏳  Siklus berikutnya dalam 5 detik...")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Publisher dihentikan.")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()