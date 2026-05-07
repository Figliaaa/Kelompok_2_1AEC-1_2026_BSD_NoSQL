===================================================
DASHBOARD MONITORING SUHU MESIN (STT Studi Kasus)
===================================================

A. DESKRIPSI
Program ini adalah dashboard berbasis konsol untuk memonitor data suhu mesin dari database MongoDB. Program akan menampilkan suhu terkini, rata-rata suhu dalam 1 jam terakhir, dan mencetak alarm jika suhu mesin melebihi batas aman (90 derajat Celcius). Alarm juga akan didokumentasikan otomatis ke dalam file 'alarm.log'.

B. PRASYARAT
Pastikan Anda sudah menginstal pustaka berikut di environment Python Anda:
- pymongo
- pandas
(Perintah instalasi: pip install pymongo pandas)

C. CARA PERSIAPAN DATA (TESTING)
Jika database Anda masih kosong, Anda dapat menggunakan skrip seeder yang disediakan untuk membuat data fiktif secara otomatis:
1. Jalankan perintah: python seeder.py
2. Skrip akan memasukkan puluhan baris data suhu mesin fiktif dengan timestamp sesuai waktu saat ini (UTC).

D. CARA MENJALANKAN DASHBOARD
1. Pastikan service MongoDB (mongod) di komputer Anda sedang berjalan di port 27017.
2. Buka terminal atau command prompt.
3. Arahkan ke direktori tempat file disimpan.
4. Jalankan perintah: python monitor.py
5. Hasil berupa tabel dashboard akan langsung tercetak di terminal.
6. Periksa direktori yang sama, jika ada mesin yang suhunya di atas 90 derajat, akan muncul file baru bernama 'alarm.log'.

E. FITUR PENANGANAN ERROR
Jika MongoDB Anda dalam kondisi mati (offline), program tidak akan mengeluarkan error merah yang panjang (traceback). Sebaliknya, program akan melakukan fail-safe (maksimal 2 detik loading) dan memberikan pesan yang jelas: "Sistem sedang offline: Gagal terhubung ke database MongoDB."