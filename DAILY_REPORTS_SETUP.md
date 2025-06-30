# Günlük DÖF Raporu Sistemi Kurulum Talimatları

Bu sistem her akşam 17:00'da otomatik olarak çalışarak departman yöneticilerine, bölge müdürlerine ve direktörlere günlük DÖF raporları gönderir.

## Sistem Gereksinimleri

- Linux sunucu (Ubuntu/CentOS/RHEL)
- Python 3.x
- MySQL veritabanı
- SMTP e-posta sunucusu
- Cron daemon

## Kurulum Adımları

### 1. Dosyaları Sunucuya Yükleyin

Aşağıdaki dosyaları DÖF uygulamanızın ana dizinine yükleyin:
- `send_daily_dof_reports.py` - Ana rapor scripti
- `run_daily_reports.sh` - Cron job çalıştırma scripti

### 2. Çevre Değişkenlerini Ayarlayın

`run_daily_reports.sh` dosyasını düzenleyin:

```bash
# Çalışma dizini - DÖF uygulamanızın gerçek yolunu yazın
APP_DIR="/home/user/dof-application"

# Sunucu URL'nizi güncelleyin
export SERVER_URL="http://your-actual-server-ip:5000"
```

### 3. İzinleri Ayarlayın

```bash
# Script çalıştırma izni verin
chmod +x run_daily_reports.sh

# Log dizini oluşturun ve izin verin
sudo mkdir -p /var/log/dof
sudo chown $USER:$USER /var/log/dof
```

### 4. Log Dizinini Hazırlayın

```bash
# Python scriptindeki log yolunu güncelleyin
sudo mkdir -p /var/log
sudo touch /var/log/dof_daily_reports.log
sudo chown $USER:$USER /var/log/dof_daily_reports.log
```

### 5. Manuel Test

Kurulum öncesi test edin:

```bash
# Çalışma dizinine gidin
cd /home/user/dof-application

# Manuel olarak çalıştırın
python3 send_daily_dof_reports.py

# Shell script ile test edin
./run_daily_reports.sh
```

### 6. Cron Job Kurulumu

Her akşam 17:00'da otomatik çalıştırmak için:

```bash
# Crontab düzenleyicisini açın
crontab -e

# Aşağıdaki satırı ekleyin (17:00 = saat 17:00)
0 17 * * * /home/user/dof-application/run_daily_reports.sh

# Kaydedin ve çıkın (:wq)
```

#### Cron Job Formatı Açıklaması:
```
0 17 * * * komut
│ │  │ │ │
│ │  │ │ └── Haftanın günü (0-7, 0 ve 7 = Pazar)
│ │  │ └──── Ay (1-12)
│ │  └────── Ayın günü (1-31)
│ └──────── Saat (0-23)
└────────── Dakika (0-59)
```

### 7. Alternatif Saatler

Farklı saatlerde çalıştırmak için:

```bash
# Her gün saat 09:00
0 9 * * * /home/user/dof-application/run_daily_reports.sh

# Her gün saat 18:30
30 18 * * * /home/user/dof-application/run_daily_reports.sh

# Sadece hafta içi saat 17:00 (Pazartesi-Cuma)
0 17 * * 1-5 /home/user/dof-application/run_daily_reports.sh
```

### 8. Cron Job Kontrolü

```bash
# Aktif cron jobları görüntüleyin
crontab -l

# Cron servisinin çalışıp çalışmadığını kontrol edin
sudo systemctl status cron     # Ubuntu/Debian
sudo systemctl status crond    # CentOS/RHEL

# Cron servisi başlatma (gerekirse)
sudo systemctl start cron      # Ubuntu/Debian
sudo systemctl start crond     # CentOS/RHEL
```

### 9. Log İzleme

```bash
# Günlük rapor loglarını izleyin
tail -f /var/log/dof_daily_reports.log

# Cron job loglarını izleyin
tail -f /var/log/dof/daily_reports_$(date +%Y-%m-%d).log

# Sistem cron logları
tail -f /var/log/cron          # CentOS/RHEL
tail -f /var/log/syslog        # Ubuntu/Debian
```

## Sorun Giderme

### 1. E-posta Gönderilmiyor

- SMTP ayarlarını kontrol edin (`app.py` veya `config.py`)
- E-posta sunucusu erişilebilir mi test edin
- Güvenlik duvarı ayarlarını kontrol edin

### 2. Veritabanı Bağlantı Hatası

- MySQL servisinin çalıştığını kontrol edin: `sudo systemctl status mysql`
- Veritabanı kullanıcı izinlerini kontrol edin
- Bağlantı string'ini doğrulayın

### 3. Cron Job Çalışmıyor

```bash
# Cron servisini yeniden başlatın
sudo systemctl restart cron

# Mail servisini kontrol edin (cron hata mesajları için)
sudo systemctl status postfix

# Cron job loglarını kontrol edin
grep CRON /var/log/syslog
```

### 4. İzin Hataları

```bash
# Script izinlerini kontrol edin
ls -la run_daily_reports.sh

# Log dizini izinlerini kontrol edin
ls -la /var/log/dof/

# Gerekirse izinleri düzeltin
chmod +x run_daily_reports.sh
sudo chown -R $USER:$USER /var/log/dof/
```

### 5. Python Path Hataları

`run_daily_reports.sh` dosyasında doğru Python yolunu ayarlayın:

```bash
# Python yolunu bulun
which python3

# Virtual environment kullanıyorsanız
/home/user/venv/bin/python
```

## Test Senaryoları

### 1. Manuel Test
```bash
cd /your/app/directory
python3 send_daily_dof_reports.py
```

### 2. Shell Script Test
```bash
./run_daily_reports.sh
```

### 3. Cron Test (1 dakika sonra çalışacak şekilde)
```bash
# Geçici olarak 1 dakika sonra çalışacak şekilde ayarlayın
# Örnek: şu anda 14:30 ise, 31 14 * * * şeklinde
```

## Sistem Durumu Kontrolü

### Günlük Kontrol Scripti

```bash
#!/bin/bash
echo "=== DÖF Rapor Sistemi Durumu ==="
echo "Cron Jobs:"
crontab -l | grep daily_reports

echo -e "\nSon Log Girdileri:"
tail -5 /var/log/dof_daily_reports.log

echo -e "\nMySQL Durumu:"
sudo systemctl status mysql | head -3

echo -e "\nDisk Kullanımı:"
df -h | grep -E "(Filesystem|/var/log)"
```

## Güvenlik Notları

1. **Log Dosya İzinleri**: Log dosyalarına sadece gerekli kullanıcıların erişebildiğinden emin olun
2. **E-posta Güvenliği**: SMTP şifrelerini güvenli şekilde saklayın
3. **Veritabanı Güvenliği**: DÖF veritabanı kullanıcısının sadece gerekli izinlere sahip olduğundan emin olun
4. **Sistem Güncellemeleri**: Sunucuyu düzenli olarak güncelleyin

## Performans Optimizasyonu

1. **Log Rotasyonu**: Eski log dosyalarını otomatik temizleyin (script içinde mevcut)
2. **E-posta Batch**: Çok sayıda kullanıcı için batch gönderim düşünün
3. **Veritabanı İndeks**: Sık kullanılan kolonlarda indeks oluşturun

## Bakım

- **Haftalık**: Log dosyalarını kontrol edin
- **Aylık**: Cron job loglarını gözden geçirin
- **Üç Aylık**: E-posta teslim oranlarını analiz edin 