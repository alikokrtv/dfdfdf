#!/bin/bash

# Günlük DÖF Raporu Çalıştırma Scripti
# Her akşam 17:00'da cron job ile çalıştırılır

# Çalışma dizini (DÖF uygulamasının bulunduğu dizin)
APP_DIR="/path/to/your/dof/application"

# Log dizini
LOG_DIR="/var/log/dof"

# Python executable path
PYTHON_PATH="/usr/bin/python3"

# Çevre değişkenleri
export SERVER_URL="http://your-server-ip:5000"
export AUTO_SEND_REPORTS="true"  # Otomatik gönderim için onay isteme
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# Log dosyası
DATE=$(date '+%Y-%m-%d')
LOG_FILE="$LOG_DIR/daily_reports_$DATE.log"

# Log dizinini oluştur
mkdir -p $LOG_DIR

# Script başlangıç logu
echo "$(date '+%Y-%m-%d %H:%M:%S') - Günlük DÖF raporu başlatılıyor..." >> $LOG_FILE

# Çalışma dizinine git
cd $APP_DIR

# Python scriptini çalıştır
$PYTHON_PATH send_daily_dof_reports.py >> $LOG_FILE 2>&1

# Exit code kontrolü
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Günlük DÖF raporu başarıyla tamamlandı" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Günlük DÖF raporu hatayla sonlandı (Exit Code: $EXIT_CODE)" >> $LOG_FILE
fi

# Eski log dosyalarını temizle (30 günden eski olanları)
find $LOG_DIR -name "daily_reports_*.log" -type f -mtime +30 -delete

exit $EXIT_CODE 