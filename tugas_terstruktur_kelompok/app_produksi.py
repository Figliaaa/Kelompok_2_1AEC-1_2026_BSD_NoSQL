import os
import logging
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv
from datetime import datetime
import calendar

# --- KONFIGURASI LOGGING ---
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- MEMUAT ENVIRONMENT VARIABLES ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# --- KONEKSI DATABASE ---
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping') # Test koneksi
    db = client[DB_NAME]
    col = db["produksi"]
    logging.info("Berhasil terhubung ke database MongoDB.")
except ConnectionFailure:
    logging.error("Gagal terhubung ke MongoDB. Pastikan server berjalan.")
    print("Error: Tidak dapat terhubung ke database. Cek app.log untuk detail.")
    exit(1)

# --- FUNGSI MENU ---

def input_data():
    print("\n--- 1. Input Data Produksi ---")
    try:
        batch = input("Masukkan Batch: ")
        mesin = input("Masukkan Nama Mesin: ")
        jumlah = int(input("Masukkan Jumlah Produksi: "))
        reject = int(input("Masukkan Jumlah Reject: "))
        tanggal_str = input("Masukkan Tanggal (YYYY-MM-DD): ")
        
        tanggal = datetime.strptime(tanggal_str, "%Y-%m-%d")
        
        data = {
            "batch": batch,
            "mesin": mesin,
            "jumlah": jumlah,
            "reject": reject,
            "tanggal": tanggal
        }
        
        col.insert_one(data)
        print("[SUKSES] Data berhasil disimpan.")
        logging.info(f"Data batch {batch} untuk mesin {mesin} berhasil diinsert.")
        
    except ValueError as e:
        print("[ERROR] Format input salah. Pastikan jumlah/reject berupa angka dan tanggal berformat YYYY-MM-DD.")
        logging.error(f"Error input data: {e}")
    except PyMongoError as e:
        print("[ERROR] Terjadi kesalahan pada database.")
        logging.error(f"Database error saat insert: {e}")

def tampil_data_mesin():
    print("\n--- 2. Tampilkan Data per Mesin ---")
    mesin_input = input("Masukkan Nama Mesin: ")
    
    try:
        data = list(col.find({"mesin": mesin_input}, {"_id": 0}))
        
        if not data:
            print(f"Tidak ada data untuk mesin: {mesin_input}")
            logging.info(f"Pencarian data mesin {mesin_input} tidak menemukan hasil.")
            return

        df = pd.DataFrame(data)
        print("\nData Produksi:")
        print(df.to_string(index=False))
        logging.info(f"Berhasil menampilkan {len(data)} data untuk mesin {mesin_input}.")
        
    except PyMongoError as e:
        print("[ERROR] Terjadi kesalahan saat mengambil data.")
        logging.error(f"Database error saat query mesin: {e}")

def hitung_reject_rate():
    print("\n--- 3. Batch dengan Reject Rate > 5% ---")
    
    pipeline = [
        {
            "$addFields": {
                "reject_rate": {
                    "$cond": [
                        {"$eq": ["$jumlah", 0]}, 0, # Hindari division by zero
                        {"$multiply": [{"$divide": ["$reject", "$jumlah"]}, 100]}
                    ]
                }
            }
        },
        {
            "$match": {"reject_rate": {"$gt": 5}}
        },
        {
            "$project": {
                "_id": 0,
                "batch": 1,
                "mesin": 1,
                "jumlah": 1,
                "reject": 1,
                "reject_rate": {"$round": ["$reject_rate", 2]}
            }
        }
    ]
    
    try:
        hasil = list(col.aggregate(pipeline))
        
        if not hasil:
            print("Tidak ada batch dengan reject rate di atas 5%.")
            logging.info("Agregasi reject rate dijalankan, tidak ada hasil > 5%.")
            return
            
        df = pd.DataFrame(hasil)
        df.rename(columns={"reject_rate": "Reject Rate (%)"}, inplace=True)
        print("\nData Batch Bermasalah:")
        print(df.to_string(index=False))
        logging.info(f"Menampilkan {len(hasil)} data batch dengan reject rate tinggi.")
        
    except PyMongoError as e:
        print("[ERROR] Terjadi kesalahan saat menghitung reject rate.")
        logging.error(f"Database error saat agregasi reject rate: {e}")

def ekspor_laporan():
    print("\n--- 4. Ekspor Laporan Bulanan ---")
    periode = input("Masukkan Bulan dan Tahun (MM-YYYY): ")
    
    try:
        bulan, tahun = map(int, periode.split("-"))
        
        # Tentukan rentang tanggal
        tanggal_mulai = datetime(tahun, bulan, 1)
        hari_terakhir = calendar.monthrange(tahun, bulan)[1]
        tanggal_selesai = datetime(tahun, bulan, hari_terakhir, 23, 59, 59)
        
        pipeline = [
            {
                "$match": {
                    "tanggal": {"$gte": tanggal_mulai, "$lte": tanggal_selesai}
                }
            },
            {
                "$group": {
                    "_id": "$mesin",
                    "total_produksi": {"$sum": "$jumlah"},
                    "total_reject": {"$sum": "$reject"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        hasil = list(col.aggregate(pipeline))
        
        if not hasil:
            print(f"Tidak ada data produksi pada bulan {periode}.")
            logging.info(f"Ekspor laporan {periode} dibatalkan: data kosong.")
            return
            
        df = pd.DataFrame(hasil)
        df.rename(columns={"_id": "Mesin", "total_produksi": "Total Produksi", "total_reject": "Total Reject"}, inplace=True)
        
        nama_file = f"laporan_{periode}.csv"
        df.to_csv(nama_file, index=False)
        print(f"[SUKSES] Laporan berhasil diekspor ke file: {nama_file}")
        logging.info(f"Berhasil mengekspor laporan bulanan ke {nama_file}.")
        
    except ValueError:
        print("[ERROR] Format bulan-tahun salah. Harap gunakan MM-YYYY (contoh: 10-2023).")
        logging.error("Error input format periode laporan.")
    except PyMongoError as e:
        print("[ERROR] Terjadi kesalahan saat memproses laporan.")
        logging.error(f"Database error saat ekspor laporan: {e}")

# --- MAIN LOOP ---

def main():
    while True:
        print("\n===============================")
        print(" SISTEM MANAJEMEN PRODUKSI")
        print("===============================")
        print("1. Input data produksi baru")
        print("2. Tampilkan data produksi per mesin")
        print("3. Hitung batch dengan Reject Rate > 5%")
        print("4. Ekspor laporan bulanan (CSV)")
        print("5. Keluar")
        
        pilihan = input("Pilih menu (1-5): ")
        
        if pilihan == '1':
            input_data()
        elif pilihan == '2':
            tampil_data_mesin()
        elif pilihan == '3':
            hitung_reject_rate()
        elif pilihan == '4':
            ekspor_laporan()
        elif pilihan == '5':
            print("Keluar dari aplikasi. Sampai jumpa!")
            logging.info("Aplikasi ditutup oleh pengguna.")
            break
        else:
            print("[WARNING] Pilihan tidak valid.")

if __name__ == "__main__":
    main()