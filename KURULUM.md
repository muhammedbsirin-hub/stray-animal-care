# Kurulum (her bilgisayarda bir kez)

Gerekenler: **MySQL Server 8.0 + MySQL Workbench** (labda kurduk), **Python 3.11 veya üstü**, **PyCharm**.

1. **Zip'i aç.** Örneğin Masaüstüne çıkar. İçinden `stray-animal-db` klasörü çıkar.

2. **MySQL kullanıcısını oluştur.**
   - MySQL Workbench'i aç, **Local instance (root)** ile bağlan.
   - File → Open SQL Script → `stray-animal-db/database/00_setup_user.sql`
   - Sarı şimşek ⚡ butonuna bas. Altta yeşil tikler görmelisin.

3. **Projeyi PyCharm'da aç.**
   - File → Open → `stray-animal-db` klasörünü seç.
   - Sağ altta "No interpreter" yazıyorsa: Add New Interpreter → Add Local Interpreter →
     Virtualenv Environment → OK (PyCharm `.venv` klasörünü kendisi oluşturur).

4. **Kütüphaneleri kur.** PyCharm'ın altındaki **Terminal** sekmesinde:
   ```
   pip install -r requirements.txt
   ```

5. **Veritabanını kur** (aynı terminalde):
   ```
   python tools/setup_database.py
   ```
   "Database is ready." yazmalı.
   Olmazsa Workbench'te sırayla şu dosyaları çalıştır: `01_schema.sql`, `02_functions_views.sql`,
   `03_procedures_triggers.sql`, `05_seed_data.sql`.

6. **Çalıştır.** `main.py` dosyasına sağ tıkla → **Run 'main'**.

## Giriş hesapları (hepsinin şifresi `Demo1234!`)

- `admin` → yönetici
- `vet01` → veteriner (gelen vakası ve geciken aşıları var)
- `elif_yildiz` → gönüllü + sahiplenen

## Bilmeniz gerekenler

- Herkesin veritabanı **kendi bilgisayarında**. Birinin uygulamaya girdiği kayıt diğerlerinde görünmez.
  Sunumda tek bir bilgisayar kullanılacak.
- `python tools/setup_database.py` komutu veritabanını **sıfırlar**: örnek veriye geri döner.
- Harita için internet bağlantısı gerekir.
- Hata alırsanız ekran görüntüsünü gruba atın.
