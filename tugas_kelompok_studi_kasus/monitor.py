import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta

def run_dashboard():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping') 
        db = client["studi_kasus_pertemuan6"]
        collection = db["suhu_mesin"]
    except (ConnectionFailure, ServerSelectionTimeoutError):
        print("Sistem sedang offline: Gagal terhubung ke database MongoDB.")
        return

    satu_jam_lalu = datetime.utcnow() - timedelta(hours=1)
    
    pipeline_terkini = [
        {"$match": {"timestamp": {"$gte": satu_jam_lalu}}},
        {"$sort": {"timestamp": -1}}, 
        {"$group": {
            "_id": "$mesin", 
            "suhu_terkini": {"$first": "$suhu"}, 
            "waktu_terkini": {"$first": "$timestamp"}
        }},
        {"$sort": {"_id": 1}}
    ]
    data_terkini = list(collection.aggregate(pipeline_terkini))
    
    pipeline_rata_rata = [
        {"$match": {"timestamp": {"$gte": satu_jam_lalu}}},
        {"$group": {"_id": "$mesin", "rata_rata_suhu": {"$avg": "$suhu"}}},
        {"$sort": {"_id": 1}}
    ]
    data_rata_rata = list(collection.aggregate(pipeline_rata_rata))
    
    pipeline_alarm = [
        {"$match": {"timestamp": {"$gte": satu_jam_lalu}, "suhu": {"$gt": 90}}},
        {"$group": {"_id": "$mesin", "suhu_maksimum": {"$max": "$suhu"}}},
        {"$sort": {"_id": 1}}
    ]
    data_alarm_maks = list(collection.aggregate(pipeline_alarm))

    log_alarms = list(collection.find(
        {"timestamp": {"$gte": satu_jam_lalu}, "suhu": {"$gt": 90}}
    ).sort("timestamp", 1))

    if log_alarms:
        with open("alarm.log", "a") as f:
            for alarm in log_alarms:
                waktu_str = alarm["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{waktu_str}] ALARM - Mesin: {alarm['mesin']} | Suhu: {alarm['suhu']}°C\n")

    print("\n" + "="*60)
    print(" DASHBOARD MONITORING SUHU MESIN (1 Jam Terakhir)")
    print("="*60 + "\n")

    print("=== 1. SUHU TERKINI PER MESIN ===")
    if data_terkini:
        df_terkini = pd.DataFrame(data_terkini)
        df_terkini.rename(columns={"_id": "Mesin", "suhu_terkini": "Suhu Terkini (°C)", "waktu_terkini": "Waktu Update (UTC)"}, inplace=True)
        print(df_terkini.to_string(index=False))
    else:
        print("- Tidak ada data suhu dalam 1 jam terakhir.")

    print("\n=== 2. RATA-RATA SUHU PER MESIN ===")
    if data_rata_rata:
        df_rata_rata = pd.DataFrame(data_rata_rata)
        df_rata_rata.rename(columns={"_id": "Mesin", "rata_rata_suhu": "Rata-rata Suhu (°C)"}, inplace=True)
        df_rata_rata["Rata-rata Suhu (°C)"] = df_rata_rata["Rata-rata Suhu (°C)"].round(2)
        print(df_rata_rata.to_string(index=False))
    else:
        print("- Tidak ada data suhu dalam 1 jam terakhir.")

    print("\n=== 3. STATUS ALARM (Suhu > 90°C) ===")
    if data_alarm_maks:
        df_alarm = pd.DataFrame(data_alarm_maks)
        df_alarm.rename(columns={"_id": "Mesin", "suhu_maksimum": "Suhu Maksimum (°C)"}, inplace=True)
        print("[!] PERINGATAN! Mesin berikut telah melebihi batas batas aman:")
        print(df_alarm.to_string(index=False))
        print("\n*(Catatan detail seluruh kejadian alarm telah disimpan ke alarm.log)*")
    else:
        print("[✓] Aman. Tidak ada mesin yang melebihi batas 90°C.")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    run_dashboard()