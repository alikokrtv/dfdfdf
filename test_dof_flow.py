#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DÖF akışı test scripti - Emaar'dan Kanyon'a DÖF oluşturma ve süreç ilerletme testi
Bu script, DÖF oluşturma ve süreçleri ilerletme işlemlerini test eder
ve bu süreçlerde e-postaların doğru şekilde gönderilip gönderilmediğini kontrol eder.
"""

from app import app, db
from models import User, Department, DOF, DOFAction, DOFStatus, DOFType, DOFSource
from utils import notify_for_dof, create_notification
import logging
import sys
import datetime
import time

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DOF_TEST")

def print_separator():
    print("\n" + "="*70 + "\n")

def test_dof_flow():
    """
    DÖF oluşturma ve süreçleri test et
    """
    with app.app_context():
        print_separator()
        print("Emaar'dan Kanyon'a DÖF Oluşturma ve Süreç Testi")
        print_separator()
        
        try:
            # Test için departmanları ve kullanıcıları kontrol et
            emaar_dept = Department.query.filter_by(name='Emaar').first()
            kanyon_dept = Department.query.filter_by(name='Kanyon').first()
            
            if not emaar_dept:
                emaar_dept = Department(name='Emaar', description='Emaar Departmanı', is_active=True)
                db.session.add(emaar_dept)
                db.session.commit()
                print(f"✓ Emaar departmanı oluşturuldu (id: {emaar_dept.id})")
            else:
                print(f"✓ Emaar departmanı bulundu (id: {emaar_dept.id})")
                
            if not kanyon_dept:
                kanyon_dept = Department(name='Kanyon', description='Kanyon Departmanı', is_active=True)
                db.session.add(kanyon_dept)
                db.session.commit()
                print(f"✓ Kanyon departmanı oluşturuldu (id: {kanyon_dept.id})")
            else:
                print(f"✓ Kanyon departmanı bulundu (id: {kanyon_dept.id})")
            
            # Kullanıcıları bul
            admin_user = User.query.filter_by(username='admin').first()
            quality_manager = User.query.filter_by(role=2).first()  # Kalite yöneticisi
            
            if not admin_user:
                print("✗ Admin kullanıcısı bulunamadı!")
                return False
            
            if not quality_manager:
                print("✗ Kalite yöneticisi bulunamadı!")
                return False
                
            print(f"✓ Admin kullanıcısı: {admin_user.username} ({admin_user.email})")
            print(f"✓ Kalite yöneticisi: {quality_manager.username} ({quality_manager.email})")
            
            # 1. Emaar'dan Kanyon'a bir DÖF oluştur
            print_separator()
            print("1. ADIM: Emaar'dan Kanyon'a DÖF oluşturuluyor...")
            
            new_dof = DOF(
                title="Test DÖF - Emaar'dan Kanyon'a",
                description="Bu bir test DÖF'üdür. Emaar'dan Kanyon'a gönderilmiştir.",
                dof_type=DOFType.CORRECTIVE,  # Düzeltici faaliyet
                dof_source=DOFSource.NONCONFORMITY,  # Uygunsuzluk
                priority=2,  # Orta
                department_id=kanyon_dept.id,  # Hedef departman: Kanyon
                created_by=admin_user.id,
                status=DOFStatus.SUBMITTED,  # Gönderildi
                created_at=datetime.datetime.now(),
                due_date=datetime.datetime.now() + datetime.timedelta(days=7)  # 7 gün sonra
            )
            
            db.session.add(new_dof)
            db.session.commit()
            print(f"✓ Yeni DÖF oluşturuldu: #{new_dof.id} - {new_dof.title}")
            
            # DÖF bildirimi gönder
            notify_for_dof(new_dof, "create", admin_user)
            print(f"✓ DÖF #{new_dof.id} için bildirim e-postaları gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(2)  # E-posta gönderimi için kısa bekle
            
            # 2. DÖF durumunu incelemeye al
            print_separator()
            print("2. ADIM: DÖF incelemeye alınıyor...")
            
            new_dof.status = DOFStatus.IN_REVIEW
            db.session.commit()
            
            # İnceleme aksiyonu ekle
            review_action = DOFAction(
                dof_id=new_dof.id,
                user_id=quality_manager.id,
                action_type=2,  # 2: Durum değişikliği
                comment="DÖF incelemeye alındı",
                old_status=DOFStatus.SUBMITTED,
                new_status=DOFStatus.IN_REVIEW,
                created_at=datetime.datetime.now()
            )
            db.session.add(review_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", quality_manager)
            print(f"✓ DÖF #{new_dof.id} incelemeye alındı")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(2)  # E-posta gönderimi için kısa bekle
            
            # 3. DÖF'ü ilgili kişiye ata
            print_separator()
            print("3. ADIM: DÖF ilgili kişiye atanıyor...")
            
            new_dof.status = DOFStatus.ASSIGNED
            new_dof.assigned_to = admin_user.id  # Test için admin'e atanıyor
            db.session.commit()
            
            # Atama aksiyonu ekle
            assign_action = DOFAction(
                dof_id=new_dof.id,
                user_id=quality_manager.id,
                action_type=3,  # 3: Atama
                comment=f"DOF {admin_user.full_name} kullanicisina atandi",
                old_status=DOFStatus.IN_REVIEW,
                new_status=DOFStatus.ASSIGNED,
                created_at=datetime.datetime.now()
            )
            db.session.add(assign_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "assign", quality_manager)
            print(f"✓ DÖF #{new_dof.id}, {admin_user.full_name} kullanıcısına atandı")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(2)  # E-posta gönderimi için kısa bekle
            
            # 4. DÖF üzerinde çalışmaya başla
            print_separator() 
            print("4. ADIM: DÖF üzerinde çalışmaya başlanıyor...")
            
            new_dof.status = DOFStatus.IN_PROGRESS
            db.session.commit()
            
            # İşlem aksiyonu ekle
            progress_action = DOFAction(
                dof_id=new_dof.id,
                user_id=admin_user.id,
                action_type=2,  # 2: Durum değişikliği
                comment="DOF uzerinde calismaya baslandi",
                old_status=DOFStatus.ASSIGNED,
                new_status=DOFStatus.IN_PROGRESS,
                created_at=datetime.datetime.now()
            )
            db.session.add(progress_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", admin_user)
            print(f"✓ DÖF #{new_dof.id} üzerinde çalışmaya başlandı")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            print_separator()
            print(f"TEST TAMAMLANDI! DÖF #{new_dof.id} başarıyla oluşturuldu ve süreçleri test edildi.")
            print("E-posta kutunuzu kontrol ederek bildirimlerin gelip gelmediğini doğrulayın.")
            print_separator()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Test sırasında hata oluştu: {str(e)}")
            print(f"✗ HATA: {str(e)}")
            return False

if __name__ == "__main__":
    print("DÖF Süreci Test Aracı")
    print("---------------------")
    test_dof_flow()
    print("---------------------")
