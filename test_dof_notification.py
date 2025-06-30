#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test betiği: Emaar'dan Kanyon'a yeni bir DÖF oluşturur ve e-posta bildirimlerini test eder
"""

import sys
import os
import logging
from datetime import datetime
import time

# Loglama
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='dof_test_logs.txt',
    filemode='a'
)
logger = logging.getLogger('DOF_TEST')

# Ana uygulama ve modelleri import et
from flask import current_app
from app import app, db
from models import DOF, User, Department, DOFStatus, DOFAction
from direct_email import send_direct_email

def create_test_dof():
    """
    Test için bir DÖF oluşturur ve e-posta gönderimini loglar
    """
    with app.app_context():
        try:
            # Emaar departmanını bul
            emaar_dept = Department.query.filter(Department.name.like('%Emaar%')).first()
            if not emaar_dept:
                logger.error("Emaar departmanı bulunamadı")
                print("Emaar departmanı bulunamadı")
                return False
                
            # Kanyon departmanını bul
            kanyon_dept = Department.query.filter(Department.name.like('%Kanyon%')).first()
            if not kanyon_dept:
                logger.error("Kanyon departmanı bulunamadı")
                print("Kanyon departmanı bulunamadı")
                return False
            
            # Emaar departmanının bir kullanıcısını bul (oluşturucu)
            emaar_user = User.query.filter_by(department_id=emaar_dept.id).first()
            if not emaar_user:
                logger.error("Emaar departmanında kullanıcı bulunamadı")
                print("Emaar departmanında kullanıcı bulunamadı")
                return False
                
            # Kanyon departmanının bir kullanıcısını bul (atanacak kişi)
            kanyon_user = User.query.filter_by(department_id=kanyon_dept.id).first()
            if not kanyon_user:
                logger.error("Kanyon departmanında kullanıcı bulunamadı")
                print("Kanyon departmanında kullanıcı bulunamadı")
                return False
            
            # Kalite yöneticilerini al
            quality_managers = User.query.filter_by(role=2).all()
            quality_emails = [qm.email for qm in quality_managers if qm and qm.email]
            
            # Verileri logla
            logger.info(f"Emaar Departmanı: {emaar_dept.name} (ID: {emaar_dept.id})")
            logger.info(f"Kanyon Departmanı: {kanyon_dept.name} (ID: {kanyon_dept.id})")
            logger.info(f"Oluşturucu: {emaar_user.full_name} (ID: {emaar_user.id}, Email: {emaar_user.email})")
            logger.info(f"Atanacak Kişi: {kanyon_user.full_name} (ID: {kanyon_user.id}, Email: {kanyon_user.email})")
            logger.info(f"Kalite Yöneticileri: {', '.join(quality_emails)}")
            
            # Yeni DÖF oluştur
            current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            title = f"Emaar-Kanyon Test DÖF ({current_time})"
            description = f"""Bu bir test DÖF'tür. Emaar departmanından Kanyon departmanına gönderilmiştir.
            
            Oluşturulma Zamanı: {current_time}
            Oluşturan: {emaar_user.full_name}
            Atanan: {kanyon_user.full_name}
            
            E-posta bildirimlerini test etmek amacıyla oluşturulmuştur.
            """
            
            # DÖF nesnesini oluştur
            dof = DOF(
                title=title,
                description=description,
                created_by=emaar_user.id,
                department_id=kanyon_dept.id,
                assigned_to=kanyon_user.id,
                status=DOFStatus.SUBMITTED,  # SUBMITTED durumu (Gönderildi)
                dof_type=1,  # Düzeltici Faaliyet
                dof_source=1,  # İç Denetim
                priority=2,  # Orta öncelik
                created_at=datetime.now()
            )
            
            # Veritabanına kaydet
            db.session.add(dof)
            db.session.commit()
            logger.info(f"Test DÖF oluşturuldu: ID={dof.id}, Başlık={title}")
            
            # Bir aksiyon ekle
            action = DOFAction(
                dof_id=dof.id,
                user_id=emaar_user.id,
                action_type=0,  # Oluşturma
                comment="Test DÖF oluşturuldu",
                created_at=datetime.now()
            )
            db.session.add(action)
            db.session.commit()
            logger.info("DÖF aksiyon kaydı oluşturuldu")
            
            # Doğrudan e-posta bildirimlerini gönder
            recipients = quality_emails + [kanyon_user.email]
            recipients = list(set(recipients))  # Tekrarları kaldır
            
            subject = f"DÖF Sistemi - Test Bildirimi: {title}"
            html_content = f"""
            <html>
                <body>
                    <h2>Test DÖF Bildirimi</h2>
                    <p>Bu bir test DÖF bildirimidir.</p>
                    <p><strong>DÖF ID:</strong> {dof.id}</p>
                    <p><strong>Başlık:</strong> {title}</p>
                    <p><strong>Oluşturan:</strong> {emaar_user.full_name}</p>
                    <p><strong>Atanan:</strong> {kanyon_user.full_name}</p>
                    <p><strong>Tarih/Saat:</strong> {current_time}</p>
                    <p>Bu bir test e-postasıdır. Bu e-postayı aldıysanız, e-posta bildirimleri çalışıyor demektir.</p>
                </body>
            </html>
            """
            text_content = f"""Test DÖF Bildirimi
            
            Bu bir test DÖF bildirimidir.
            
            DÖF ID: {dof.id}
            Başlık: {title}
            Oluşturan: {emaar_user.full_name}
            Atanan: {kanyon_user.full_name}
            Tarih/Saat: {current_time}
            
            Bu bir test e-postasıdır. Bu e-postayı aldıysanız, e-posta bildirimleri çalışıyor demektir.
            """
            
            logger.info(f"E-posta alıcıları: {', '.join(recipients)}")
            for recipient in recipients:
                logger.info(f"Test e-postası gönderiliyor: {recipient}")
                try:
                    result = send_direct_email(recipient, subject, html_content, text_content)
                    logger.info(f"E-posta gönderim sonucu: {'Başarılı' if result else 'Başarısız'}")
                except Exception as e:
                    logger.error(f"E-posta gönderim hatası: {str(e)}")
            
            print(f"Test DÖF başarıyla oluşturuldu. DÖF ID: {dof.id}")
            print(f"E-posta alıcıları: {', '.join(recipients)}")
            print("Detaylı log için dof_test_logs.txt dosyasını kontrol edin.")
            return True
            
        except Exception as e:
            logger.error(f"Test DÖF oluşturma hatası: {str(e)}")
            print(f"HATA: {str(e)}")
            return False

if __name__ == "__main__":
    print("Test DÖF oluşturma aracı başlatılıyor...")
    logger.info("=== Test DÖF oluşturma işlemi başlatıldı ===")
    
    result = create_test_dof()
    
    logger.info("=== Test DÖF oluşturma işlemi tamamlandı ===")
    print("İşlem tamamlandı!")
