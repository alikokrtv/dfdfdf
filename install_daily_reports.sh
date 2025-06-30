#!/bin/bash

# DÖF Günlük Rapor Sistemi Otomatik Kurulum Scripti
# Bu script sistemin kurulumunu otomatikleştirir

set -e  # Hata durumunda çık

echo "🚀 DÖF Günlük Rapor Sistemi Kurulum Başlıyor..."
echo "=" * 50

# Kullanıcıdan temel bilgileri al
read -p "DÖF uygulamanızın tam yolu: " APP_DIR
read -p "Sunucu IP adresi ve port (örn: 192.168.1.100:5000): " SERVER_URL
read -p "Python executable yolu [/usr/bin/python3]: " PYTHON_PATH
PYTHON_PATH=${PYTHON_PATH:-/usr/bin/python3}

# Girilen bilgileri doğrula
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Hata: Belirtilen dizin mevcut değil: $APP_DIR"
    exit 1
fi

if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Hata: Python executable bulunamadı: $PYTHON_PATH"
    exit 1
fi

echo "✅ Temel kontroller tamamlandı"

# 1. Gerekli dizinleri oluştur
echo "📁 Log dizinlerini oluşturuyor..."
sudo mkdir -p /var/log/dof
sudo chown $USER:$USER /var/log/dof
sudo touch /var/log/dof_daily_reports.log
sudo chown $USER:$USER /var/log/dof_daily_reports.log

# 2. run_daily_reports.sh dosyasını güncelle
echo "⚙️  Konfigürasyon dosyasını güncelliyor..."
sed -i "s|APP_DIR=\"/path/to/your/dof/application\"|APP_DIR=\"$APP_DIR\"|g" "$APP_DIR/run_daily_reports.sh"
sed -i "s|PYTHON_PATH=\"/usr/bin/python3\"|PYTHON_PATH=\"$PYTHON_PATH\"|g" "$APP_DIR/run_daily_reports.sh"
sed -i "s|SERVER_URL=\"http://your-server-ip:5000\"|SERVER_URL=\"http://$SERVER_URL\"|g" "$APP_DIR/run_daily_reports.sh"

# 3. İzinleri ayarla
echo "🔐 İzinleri ayarlıyor..."
chmod +x "$APP_DIR/run_daily_reports.sh"
chmod +x "$APP_DIR/send_daily_dof_reports.py"

# 4. Manuel test yap
echo "🧪 Manuel test yapılıyor..."
cd "$APP_DIR"
echo "Test 1: Python scripti kontrolü..."
if $PYTHON_PATH -c "import sys; sys.path.append('$APP_DIR'); from app import app; print('✅ Import test başarılı')"; then
    echo "✅ Python scripti test edildi"
else
    echo "⚠️  Python scripti test edilemedi, lütfen manuel kontrol edin"
fi

# 5. Cron job ekle
echo "⏰ Cron job ekleniyor..."
CRON_JOB="0 17 * * * $APP_DIR/run_daily_reports.sh"

# Mevcut crontab'ı al
crontab -l > temp_crontab 2>/dev/null || touch temp_crontab

# Bu job zaten var mı kontrol et
if grep -q "run_daily_reports.sh" temp_crontab; then
    echo "⚠️  Cron job zaten mevcut, güncelleniyor..."
    grep -v "run_daily_reports.sh" temp_crontab > temp_crontab_new
    mv temp_crontab_new temp_crontab
fi

# Yeni job ekle
echo "$CRON_JOB" >> temp_crontab

# Crontab'ı güncelle
crontab temp_crontab
rm temp_crontab

echo "✅ Cron job eklendi: Her gün 17:00"

# 6. Cron servisini kontrol et
echo "🔄 Cron servisini kontrol ediyor..."
if systemctl is-active --quiet cron 2>/dev/null; then
    echo "✅ Cron servisi çalışıyor"
elif systemctl is-active --quiet crond 2>/dev/null; then
    echo "✅ Crond servisi çalışıyor"
else
    echo "⚠️  Cron servisi çalışmıyor, başlatılıyor..."
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl start cron 2>/dev/null || sudo systemctl start crond 2>/dev/null || echo "❌ Cron servisi başlatılamadı"
    fi
fi

# 7. Test çalıştırması öner
echo ""
echo "=" * 50
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "📋 Kurulum Özeti:"
echo "   • Uygulama Dizini: $APP_DIR"
echo "   • Python Yolu: $PYTHON_PATH"
echo "   • Sunucu URL: http://$SERVER_URL"
echo "   • Cron Job: Her gün 17:00"
echo "   • Log Dosyası: /var/log/dof_daily_reports.log"
echo ""
echo "🔧 Test Komutları:"
echo "   # Manuel test:"
echo "   cd $APP_DIR && python3 send_daily_dof_reports.py"
echo ""
echo "   # Shell script test:"
echo "   $APP_DIR/run_daily_reports.sh"
echo ""
echo "   # Cron job kontrol:"
echo "   crontab -l | grep daily_reports"
echo ""
echo "   # Log izleme:"
echo "   tail -f /var/log/dof_daily_reports.log"
echo ""
echo "⚠️  İlk test için aşağıdaki komutu çalıştırın:"
echo "   cd $APP_DIR && AUTO_SEND_REPORTS=false python3 send_daily_dof_reports.py"
echo ""
echo "📚 Daha fazla bilgi için: DAILY_REPORTS_SETUP.md dosyasını okuyun" 