import json
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from colorama import init, Fore, Back, Style
from datetime import datetime, timezone
import statistics

init(autoreset=True)

# ============================================================
#  KONFIGURASI
# ============================================================
BROKER    = "broker.emqx.io"
PORT      = 1883
TOPIC     = "pabrik/mesin/kesehatan"
MONGO_URI = "mongodb://localhost:27017/"

BATAS = {
    "vibration_z":  {"waspada": 10.0,  "bahaya": 15.0},
    "casing_temp":  {"waspada": 75.0,  "bahaya": 90.0},
    "oil_pressure": {"waspada": 1.5,   "bahaya": 1.0},   # terlalu rendah = bahaya
    "current_amp":  {"waspada": 40.0,  "bahaya": 55.0},
    "health_score": {"waspada": 60.0,  "bahaya": 40.0},  # terlalu rendah = bahaya
}

_buffer = {}

# ============================================================
#  KONEKSI MONGODB
# ============================================================
try:
    print(Fore.CYAN + Style.BRIGHT + "🔌 Menghubungkan ke MongoDB...")
    client_db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client_db.admin.command("ping")

    db              = client_db["kelompok6"]
    koleksi_data    = db["kesehatan_mesin"]
    koleksi_alert   = db["alert_mesin"]
    koleksi_summary = db["summary_mesin"]   # ringkasan terkini per mesin

    koleksi_data.create_index([("sensor_id", 1), ("timestamp", -1)])
    koleksi_alert.create_index([("sensor_id", 1), ("timestamp", -1)])

    print(Fore.GREEN + Style.BRIGHT + "✅ Terhubung ke MongoDB – database: kelompok6")
except ConnectionFailure:
    print(Fore.RED + Back.WHITE + Style.BRIGHT + " ❌ FATAL: Gagal terhubung ke MongoDB! ")
    print(Fore.YELLOW + "   Pastikan MongoDB berjalan di localhost:27017")
    exit(1)


# ============================================================
#  HELPERS
# ============================================================
def kategorikan_health(skor):
    if skor >= 80:
        return "Baik"
    elif skor >= 60:
        return "Waspada"
    elif skor >= 40:
        return "Kritis"
    else:
        return "Rusak Parah"


def deteksi_tren(sensor_id, nilai_baru, param):
    """Deteksi apakah nilai parameter sedang naik konsisten (tren degradasi)."""
    buf = _buffer.setdefault(sensor_id, {}).setdefault(param, [])
    buf.append(nilai_baru)
    if len(buf) > 5:
        buf.pop(0)

    if len(buf) < 3:
        return False
    return all(buf[i] < buf[i + 1] for i in range(len(buf) - 1))


def buat_dokumen_alert(data, jenis, pesan, tingkat="waspada"):
    return {
        "sensor_id":   data["sensor_id"],
        "lokasi":      data["lokasi"],
        "tipe_mesin":  data.get("tipe_mesin", "unknown"),
        "vibration_z": data.get("vibration_z"),
        "casing_temp": data.get("casing_temp"),
        "oil_pressure":data.get("oil_pressure"),
        "current_amp": data.get("current_amp"),
        "health_score":data.get("health_score"),
        "rul_jam":     data.get("rul_jam"),
        "jenis_alert": jenis,
        "tingkat":     tingkat,
        "pesan":       pesan,
        "timestamp":   data["timestamp"],
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
#  CALLBACK MQTT
# ============================================================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(Fore.GREEN + Style.BRIGHT + f"✅ Terhubung ke MQTT Broker ({BROKER})")
        client.subscribe(TOPIC)
        print(Fore.CYAN + f"📡 Mendengarkan topik: {TOPIC}\n" + "─" * 60)
    else:
        print(Fore.RED + f"❌ Gagal terhubung, kode: {reason_code}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))

        sid     = data.get("sensor_id", "Unknown")
        lokasi  = data.get("lokasi", "-")
        vib     = data.get("vibration_z", 0.0)
        temp    = data.get("casing_temp", 0.0)
        oil     = data.get("oil_pressure", 0.0)
        amp     = data.get("current_amp", 0.0)
        health  = data.get("health_score", 100.0)
        rul     = data.get("rul_jam", 9999)
        ts      = data.get("timestamp", "-")

        koleksi_data.insert_one({**data})
        koleksi_summary.update_one(
            {"sensor_id": sid},
            {"$set": {
                **data,
                "kategori_health": kategorikan_health(health),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )

        alerts_dihasilkan = []

        if vib > BATAS["vibration_z"]["bahaya"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "getaran_kritis",
                f"Getaran KRITIS {vib} mm/s (batas {BATAS['vibration_z']['bahaya']})", "bahaya"))
        elif vib > BATAS["vibration_z"]["waspada"] or deteksi_tren(sid, vib, "vib"):
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "getaran_waspada",
                f"Getaran tinggi {vib} mm/s – tren memburuk", "waspada"))

        if temp > BATAS["casing_temp"]["bahaya"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "overheat_kritis",
                f"OVERHEAT {temp}°C (batas {BATAS['casing_temp']['bahaya']}°C)", "bahaya"))
        elif temp > BATAS["casing_temp"]["waspada"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "suhu_waspada",
                f"Suhu tinggi {temp}°C", "waspada"))

        if oil < BATAS["oil_pressure"]["bahaya"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "tekanan_oli_kritis",
                f"Tekanan oli RENDAH {oil} bar – risiko kerusakan bantalan!", "bahaya"))
        elif oil < BATAS["oil_pressure"]["waspada"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "tekanan_oli_waspada",
                f"Tekanan oli rendah {oil} bar", "waspada"))

        if health < BATAS["health_score"]["bahaya"]:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "health_kritis",
                f"Skor Kesehatan KRITIS {health}% – jadwalkan pemeliharaan segera!", "bahaya"))

        if rul < 500:
            alerts_dihasilkan.append(buat_dokumen_alert(
                data, "rul_rendah",
                f"Sisa Umur Berguna (RUL) hanya {rul} jam – perlu penggantian komponen!", "waspada"))

        if alerts_dihasilkan:
            koleksi_alert.insert_many(alerts_dihasilkan)

        if any(a["tingkat"] == "bahaya" for a in alerts_dihasilkan):
            print(Fore.WHITE + Back.RED + Style.BRIGHT +
                  f" 🚨 BAHAYA │ {sid:<22} │ Health:{health:>5}% │ RUL:{rul:>5} jam ")
            for a in alerts_dihasilkan:
                print(Fore.RED + f"    └─ {a['pesan']}")
        elif alerts_dihasilkan:
            print(Fore.YELLOW +
                  f"⚠️  WASPADA │ {sid:<22} │ Health:{health:>5}% │ RUL:{rul:>5} jam")
            for a in alerts_dihasilkan:
                print(Fore.YELLOW + f"    └─ {a['pesan']}")
        else:
            print(Fore.GREEN +
                  f"✅ Normal  │ {sid:<22} │ Health:{health:>5}% │ Suhu:{temp}°C │ Vib:{vib} mm/s")

    except json.JSONDecodeError:
        print(Fore.YELLOW + "⚠️  Data rusak (bukan JSON valid) – diabaikan.")
    except PyMongoError as e:
        print(Fore.MAGENTA + f"💾 ERROR DATABASE: {e}")
    except Exception as e:
        print(Fore.RED + f"🔥 ERROR: {e}")


# ============================================================
#  MAIN
# ============================================================
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Subscriber_PredMaint_v2")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Subscriber dihentikan.")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan jaringan: {e}")


if __name__ == "__main__":
    main()