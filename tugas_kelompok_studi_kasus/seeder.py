from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb://localhost:27017/")
collection = client["studi_kasus_pertemuan6"]["suhu_mesin"]

collection.delete_many({})

data = []
waktu_sekarang = datetime.utcnow()

mesin_list = ["Mesin-Potong-A", "Mesin-Potong-B", "Genset-01"]

for i in range(50):
    waktu_data = waktu_sekarang - timedelta(minutes=50-i)
    for mesin in mesin_list:
        suhu_dasar = 80 if mesin == "Genset-01" else 65
        suhu = suhu_dasar + random.randint(0, 15)
        
        data.append({
            "mesin": mesin,
            "suhu": suhu,
            "timestamp": waktu_data
        })

collection.insert_many(data)
print(f"Berhasil memasukkan {len(data)} data fiktif ke koleksi suhu_mesin.")