#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
E-posta ayarlarını veritabanına kaydetme aracı
Bu script, e-posta ayarlarını veritabanına kaydeder ve
sonraki tüm e-posta gönderimlerinin bu ayarları kullanmasını sağlar.
"""

from app import app, db
from models import EmailSettings, User
import logging
import sys

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("EmailSetup")

def setup_email_settings():
    """E-posta ayarlarını veritabanına kaydeder"""
    with app.app_context():
        # Veritabanında EmailSettings var mı kontrol et
        settings = EmailSettings.query.first()
        
        if settings:
            logger.info("E-posta ayarları zaten tanımlanmış, güncelleniyor...")
        else:
            logger.info("E-posta ayarları oluşturuluyor...")
            settings = EmailSettings()
        
        # Admin kullanıcısını bul
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            logger.error("Admin kullanıcısı bulunamadı!")
            return False
        
        # Kurumsal e-posta ayarlarını tanımla
        settings.mail_service = 'smtp'
        settings.smtp_host = 'mail.kurumsaleposta.com'
        settings.smtp_port = 465
        settings.smtp_use_tls = False
        settings.smtp_use_ssl = True
        settings.smtp_user = 'df@beraber.com.tr'
        settings.smtp_pass = '=z5-5MNKn=ip5P4@'
        settings.default_sender = 'info@pluskitchen.com.tr'
        settings.updated_by = admin.id
        
        # Veritabanına kaydet
        try:
            db.session.add(settings)
            db.session.commit()
            logger.info("E-posta ayarları başarıyla kaydedildi")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Hata oluştu: {str(e)}")
            return False

if __name__ == "__main__":
    print("E-posta Ayarlarını Kurma Aracı")
    print("------------------------")
    if setup_email_settings():
        print("✓ E-posta ayarları başarıyla veritabanına kaydedildi")
        print("✓ Artık tüm e-posta bildirimlerinde bu ayarlar kullanılacak")
    else:
        print("✗ E-posta ayarları kaydedilemedi")
    print("------------------------")
