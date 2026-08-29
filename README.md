# 🎮 Heartwood Bot v4.2

**Automated Mining Bot untuk LDPlayer dengan ADB Drag & Tap**

Bot ini dirancang untuk otomasi farming cotton di game Heartwood menggunakan LDPlayer dengan koneksi ADB.

## 🌟 Fitur Utama

- ✅ **ADB Drag untuk Joystick**: Menggunakan ADB untuk drag joystick game
- ✅ **ADB Tap untuk Gather**: Click langsung pada icon gather di game
- ✅ **Template Matching**: Deteksi cotton dengan OpenCV
- ✅ **Auto Navigation**: Navigasi otomatis menuju target terdekat
- ✅ **Real-time GUI**: Monitor bot dengan interface grafis
- ✅ **Cotton Counter**: Hitung jumlah cotton yang dikumpulkan

## 📋 Requirements

- Python 3.8+
- LDPlayer 9 (atau emulator Android lainnya yang support ADB)
- Android SDK Platform Tools (ADB)
- Dependencies:
  ```bash
  pip install opencv-python numpy pyautogui pygetwindow
  ```

## 🔧 Setup

### 1. Install ADB

**Windows:**
- Download dari: https://developer.android.com/studio/command-line/adb
- Extract dan tambahkan ke PATH, atau letakkan di folder yang sama dengan script

**Linux/Mac:**
```bash
sudo apt-get install android-tools-adb  # Ubuntu/Debian
brew install android-platform-tools     # macOS
```

### 2. Enable ADB di LDPlayer

1. Buka LDPlayer
2. Settings → Advanced → Enable ADB
3. Restart LDPlayer (jika diperlukan)

### 3. Konfigurasi Koordinat

**PENTING:** Anda HARUS menentukan koordinat gather button di game:

1. Buka game di LDPlayer
2. Catat koordinat icon untuk gather/collect
3. Edit `botjelabot.py` pada line ~46-47:
   ```python
   GATHER_BUTTON_X = 380  # Ubah ke X coordinate icon gather
   GATHER_BUTTON_Y = 540  # Ubah ke Y coordinate icon gather
   ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Template Images

Buat folder struktur berikut dan masukkan template images:
```
MISC/
├── mining/
│   ├── cotton/          (letakkan cotton screenshots di sini)
│   ├── Capture.JPG      (gather prompt)
│   ├── chop.jpg
│   ├── mine.jpg
│   └── pickup.jpg
└── game/
    ├── died.JPG
    └── town.JPG
```

## 🚀 Cara Menggunakan

### 1. Jalankan Script
```bash
python botjelabot.py
```

### 2. Test Input
Click tombol "🧪 TEST INPUT" untuk verifikasi:
- Bot akan drag joystick ke 8 arah
- Bot akan tap gather button
- Perhatikan apakah pergerakan terjadi di game

### 3. Mulai Bot
Jika test berhasil, click "▶️ START" untuk mulai farming

### 4. Stop Bot
Click "⏹️ STOP" untuk menghentikan bot

## ⚙️ Konfigurasi Lanjutan

Edit parameter di `botjelabot.py` untuk menyesuaikan behavior:

```python
# Joystick position
JOYSTICK_CENTER_X = 130       # X center joystick
JOYSTICK_CENTER_Y = 550       # Y center joystick
JOYSTICK_PUSH_RADIUS = 70     # Jarak push maksimal

# Drag parameters
DRAG_DURATION_MS = 500        # Durasi drag (ms)
DISTANCE_THRESHOLD = 20       # Jarak untuk stop di target
DIRECTION_RECALC_INTERVAL = 0.15  # Update direction setiap X detik

# Detection
THRESHOLD_COTTON_DETECTION = 0.78
MAX_DISTANCE_TO_COTTON = 450
```

## 🐛 Troubleshooting

### ADB tidak terkoneksi
- Pastikan LDPlayer running
- Pastikan ADB enabled di LDPlayer settings
- Coba: `adb connect localhost:5555`

### Bot tidak bergerak
- Cek apakah joystick coordinates benar
- Coba tingkatkan `DRAG_DURATION_MS` (misalnya 800ms)
- Coba tingkatkan `push_dist` dari 0.4 menjadi 0.5

### Gather tidak bekerja
- Pastikan `GATHER_BUTTON_X` dan `GATHER_BUTTON_Y` benar
- Ambil screenshot dan cek posisi icon gather
- Gunakan TEST INPUT untuk verify coordinates

### Template matching tidak deteksi cotton
- Pastikan cotton images ada di `MISC/mining/cotton/` folder
- Cek threshold `THRESHOLD_COTTON_DETECTION`
- Pastikan image quality cukup (minimal 6x6px)

## 📊 Output Log

Bot menampilkan log real-time:
```
✅ ADB Device: localhost:5555
🔎 Scanning 3 templates
🔒 Target locked! Dist=250px, Conf=0.85
🎮 → ADB Drag: (130,550) → (200,550) dur=500ms
📍 Distance: 200px | Dir: (70, 0)
✅ REACHED TARGET!
🌾 Gather found! Clicking gather button
✅ Gathering... wait 3s
```

## 📝 Notes

- Bot menggunakan template matching, pastikan lighting konsisten
- Jangan gerakkan mouse saat bot berjalan (bisa ganggu screenshot)
- Bot akan pause saat gathering (selama 3 detik)
- Cotton counter terupdate real-time di GUI

## 🎯 Tips Optimal

1. **Setup LDPlayer**
   - Gunakan resolusi konsisten (misal 720x1280)
   - Disable auto-lock screen
   - Pastikan render quality bagus

2. **Template Images**
   - Capture cotton dari berbagai posisi
   - Gunakan quality tinggi (minimal 1080p screenshot)
   - Hindari artifacts atau blur

3. **Tuning**
   - Mulai dengan default values
   - Adjust berdasarkan performa game Anda
   - Use TEST INPUT untuk debug

## 📄 License

MIT License

## ⚠️ Disclaimer

Bot ini dibuat untuk tujuan educational. Penggunaan untuk game online mungkin melanggar ToS. Gunakan dengan risiko Anda sendiri.

---

**Need Help?** Check the logs atau buat issue di repository.
