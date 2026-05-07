# 🏭 Sistem Predictive Maintenance IoT 

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-green.svg)](https://www.mongodb.com/)
[![MQTT](https://img.shields.io/badge/MQTT-Paho-orange.svg)](https://mqtt.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)

*Read this document in [English](#-iot-predictive-maintenance-system-group-6) below.*

---

## 🇮🇩 Deskripsi Proyek
Sistem pemantauan kualitas dan kesehatan mesin pabrik manufaktur secara *real-time* berbasis arsitektur **Publish-Subscribe MQTT** dan basis data **NoSQL MongoDB**. Sistem ini dirancang untuk mendeteksi anomali pada sensor mesin (Getaran, Suhu, Tekanan Oli, dan Arus Listrik) guna mencegah kerusakan fatal sebelum terjadi (*Predictive Maintenance*).

Sistem ini menerapkan arsitektur *Microservices*, di mana setiap komponen (pengumpulan data, penyimpanan, analisis, dan antarmuka) berjalan secara independen.

## 👥 Anggota Tim
1. **[Nama Anggota 1]** - MQTT Publisher (Simulasi Sensor Mesin)
2. **[Nama Anggota 2]** - MQTT Subscriber & Integrasi Database
3. **[Nama Anggota 3]** - Analisis Data & Visualisasi (Pandas & Matplotlib)
4. **[Nama Anggota 4]** - UI/UX Streamlit Dashboard & Dokumentasi

## 🛠️ Prasyarat (Requirements)
1. Pastikan **MongoDB Server** telah terinstal dan berjalan di `localhost:27017`.
2. Pastikan Anda menggunakan Python versi 3.8 atau lebih baru.
3. Instal seluruh *library* yang dibutuhkan dengan menjalankan perintah berikut di terminal:
   ```bash
   pip install paho-mqtt pymongo pandas matplotlib streamlit plotly seaborn colorama

🚀 Cara Menjalankan Sistem

Karena sistem ini terdistribusi, Anda perlu menjalankan skrip di Terminal (Command Prompt) yang berbeda-beda sesuai urutan berikut:

Terminal 1 (Jalankan Subscriber / Penyerap Data):
Bash

python sub_mesin.py

(Subscriber akan bersiap mendengarkan pesan dari broker MQTT dan menyimpannya ke database MongoDB).

Terminal 2 (Jalankan Publisher / Simulasi Sensor):
Bash

python pub_mesin.py

(Data mesin tiruan akan mulai dihasilkan dan dikirimkan ke jaringan setiap beberapa detik).

Terminal 3 (Hasilkan Analisis & Grafik):
Bash

python analisis_mesin.py

(Tunggu beberapa saat setelah Publisher berjalan agar ada data historis yang terkumpul. Skrip ini akan mengekspor file .png untuk grafik statis dan .csv untuk data tabular).

Terminal 4 (Jalankan UI Dashboard):
Bash

streamlit run app.py

(Browser bawaan Anda akan otomatis terbuka dan menampilkan antarmuka dashboard interaktif).


Berikut adalah draf README.md yang disusun secara profesional dan siap untuk langsung diunggah ke repositori GitHub Anda. Draf ini berisi dua bahasa (Indonesia dan Inggris) agar proyek kelompok Anda terlihat lebih berskala global.

Anda tinggal menyalin kode di bawah ini:
Markdown

# 🏭 Sistem Predictive Maintenance IoT (Kelompok 6)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-green.svg)](https://www.mongodb.com/)
[![MQTT](https://img.shields.io/badge/MQTT-Paho-orange.svg)](https://mqtt.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)

*Read this document in [English](#-iot-predictive-maintenance-system-group-6) below.*

---

## 🇮🇩 Deskripsi Proyek
Sistem pemantauan kualitas dan kesehatan mesin pabrik manufaktur secara *real-time* berbasis arsitektur **Publish-Subscribe MQTT** dan basis data **NoSQL MongoDB**. Sistem ini dirancang untuk mendeteksi anomali pada sensor mesin (Getaran, Suhu, Tekanan Oli, dan Arus Listrik) guna mencegah kerusakan fatal sebelum terjadi (*Predictive Maintenance*).

Sistem ini menerapkan arsitektur *Microservices*, di mana setiap komponen (pengumpulan data, penyimpanan, analisis, dan antarmuka) berjalan secara independen.

## 🛠️ Prasyarat (Requirements)
1. Pastikan **MongoDB Server** telah terinstal dan berjalan di `localhost:27017`.
2. Pastikan Anda menggunakan Python versi 3.8 atau lebih baru.
3. Instal seluruh *library* yang dibutuhkan dengan menjalankan perintah berikut di terminal:
   ```bash
   pip install paho-mqtt pymongo pandas matplotlib streamlit plotly seaborn colorama

🚀 Cara Menjalankan Sistem

Karena sistem ini terdistribusi, Anda perlu menjalankan skrip di Terminal (Command Prompt) yang berbeda-beda sesuai urutan berikut:

Terminal 1 (Jalankan Subscriber / Penyerap Data):
Bash

python sub_mesin.py

(Subscriber akan bersiap mendengarkan pesan dari broker MQTT dan menyimpannya ke database MongoDB).

Terminal 2 (Jalankan Publisher / Simulasi Sensor):
Bash

python pub_mesin.py

(Data mesin tiruan akan mulai dihasilkan dan dikirimkan ke jaringan setiap beberapa detik).

Terminal 3 (Hasilkan Analisis & Grafik):
Bash

python analisis_mesin.py

(Tunggu beberapa saat setelah Publisher berjalan agar ada data historis yang terkumpul. Skrip ini akan mengekspor file .png untuk grafik statis dan .csv untuk data tabular).

Terminal 4 (Jalankan UI Dashboard):
Bash

streamlit run app.py

(Browser bawaan Anda akan otomatis terbuka dan menampilkan antarmuka dashboard interaktif).
🇬🇧 IoT Predictive Maintenance System (Group 6)
📝 Project Description

A real-time manufacturing machine health monitoring system based on the MQTT Publish-Subscribe architecture and MongoDB NoSQL database. This system is designed to detect anomalies in machine sensors (Vibration, Temperature, Oil Pressure, and Electrical Current) to prevent fatal breakdowns before they occur (Predictive Maintenance).

The system implements a Microservices architecture, where each component (data generation, storage, analysis, and interface) runs independently.

🛠️ Prerequisites

    Ensure MongoDB Server is installed and running on localhost:27017.

    Ensure you have Python 3.8 or newer installed.

    Install all required dependencies by running the following command in your terminal:
    Bash

    pip install paho-mqtt pymongo pandas matplotlib streamlit plotly seaborn colorama

🚀 How to Run the System

Since this is a distributed system, you need to execute the scripts in separate Terminals in the following order:

Terminal 1 (Run the Subscriber):
Bash

python sub_mesin.py

(The subscriber will listen for incoming messages from the MQTT broker and safely store them in the MongoDB database).

Terminal 2 (Run the Publisher):
Bash

python pub_mesin.py

(The simulated machine data will start generating and broadcasting to the network every few seconds).

Terminal 3 (Generate Analysis & Charts):
Bash

python analisis_mesin.py

(Wait a few moments after the Publisher runs to allow historical data accumulation. This script will process the data and export .png charts and .csv datasets).

Terminal 4 (Run the UI Dashboard):
Bash

streamlit run app.py

(Your default web browser will automatically open and display the interactive dashboard interface).
