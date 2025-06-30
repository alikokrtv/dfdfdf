#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tam DÖF Akışı Test Scripti
Emaar'dan Kanyon'a DÖF oluşturma, inceleme, atama ve yanıtlama süreçlerini test eder
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

def test_full_dof_flow():
    """
    Tam DÖF akışını test et:
    1. Emaar DÖF oluşturur
    2. Kalite inceler ve onaylar
    3. Kanyon'a atanır
    4. Kanyon yanıtlar
    """
    with app.app_context():
        print_separator()
        print("TAM DÖF AKIŞI TEST SENARYOSU")
        print("Emaar -> Kalite -> Kanyon -> Çözüm")
        print_separator()
        
        try:
            # Departman ve kullanıcıları hazırla
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
            
            # Kanyon departmanı için bir kullanıcı bul veya oluştur
            kanyon_user = User.query.filter_by(department_id=kanyon_dept.id).first()
            if not kanyon_user and admin_user:
                # Test için admin kullanıcısını kullan
                kanyon_user = admin_user
                print(f"! Kanyon departmanı için kullanıcı bulunamadı, test için admin kullanılacak")
            
            if not admin_user or not quality_manager:
                print("✗ Gerekli kullanıcılar bulunamadı!")
                return False
                
            print(f"✓ Emaar için kullanıcı: {admin_user.username} ({admin_user.email})")
            print(f"✓ Kalite yöneticisi: {quality_manager.username} ({quality_manager.email})")
            print(f"✓ Kanyon için kullanıcı: {kanyon_user.username} ({kanyon_user.email})")
            
            # 1. ADIM: Emaar'dan DÖF oluştur
            print_separator()
            print("1. ADIM: Emaar'dan Kanyon'a DÖF oluşturuluyor...")
            
            new_dof = DOF(
                title="TAM AKIŞ TEST DÖF - Emaar'dan Kanyon'a",
                description="Bu bir tam akış test DÖF'üdür. Emaar'dan Kanyon'a gönderilmiştir.",
                dof_type=DOFType.CORRECTIVE,  # Düzeltici faaliyet
                dof_source=DOFSource.NONCONFORMITY,  # Uygunsuzluk
                priority=2,  # Orta
                department_id=kanyon_dept.id,  # Hedef departman: Kanyon
                created_by=admin_user.id,  # Emaar temsilcisi olarak admin
                status=DOFStatus.SUBMITTED,  # Gönderildi
                created_at=datetime.datetime.now(),
                due_date=datetime.datetime.now() + datetime.timedelta(days=7)  # 7 gün sonra
            )
            
            db.session.add(new_dof)
            db.session.commit()
            print(f"✓ Yeni DÖF oluşturuldu: #{new_dof.id} - {new_dof.title}")
            
            # DÖF bildirimi gönder
            notify_for_dof(new_dof, "create", admin_user)
            print(f"✓ DÖF #{new_dof.id} oluşturuldu bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(3)  # E-posta gönderimi için bekle
            
            # 2. ADIM: Kalite Yöneticisi DÖF'ü inceler
            print_separator()
            print("2. ADIM: Kalite Yöneticisi DÖF'ü inceliyor...")
            
            new_dof.status = DOFStatus.IN_REVIEW
            db.session.commit()
            
            # İnceleme aksiyonu ekle
            review_action = DOFAction(
                dof_id=new_dof.id,
                user_id=quality_manager.id,
                action_type=2,  # 2: Durum değişikliği
                comment="DOF incelemeye alindi",
                old_status=DOFStatus.SUBMITTED,
                new_status=DOFStatus.IN_REVIEW,
                created_at=datetime.datetime.now()
            )
            db.session.add(review_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", quality_manager)
            print(f"✓ DÖF #{new_dof.id} incelemeye alındı bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(3)  # E-posta gönderimi için bekle
            
            # 3. ADIM: DÖF Kanyon'a atanır
            print_separator()
            print("3. ADIM: DÖF Kanyon departmanına atanıyor...")
            
            new_dof.status = DOFStatus.ASSIGNED
            new_dof.assigned_to = kanyon_user.id
            db.session.commit()
            
            # Atama aksiyonu ekle
            assign_action = DOFAction(
                dof_id=new_dof.id,
                user_id=quality_manager.id,
                action_type=3,  # 3: Atama
                comment=f"DOF Kanyon departmanina atandi.",
                old_status=DOFStatus.IN_REVIEW,
                new_status=DOFStatus.ASSIGNED,
                created_at=datetime.datetime.now()
            )
            db.session.add(assign_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "assign", quality_manager)
            print(f"✓ DÖF #{new_dof.id} Kanyon'a atandı bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(3)  # E-posta gönderimi için bekle
            
            # 4. ADIM: Kanyon DÖF üzerinde çalışmaya başlar
            print_separator() 
            print("4. ADIM: Kanyon DÖF üzerinde çalışmaya başlıyor...")
            
            new_dof.status = DOFStatus.IN_PROGRESS
            db.session.commit()
            
            # İşlem aksiyonu ekle
            progress_action = DOFAction(
                dof_id=new_dof.id,
                user_id=kanyon_user.id,
                action_type=2,  # 2: Durum değişikliği
                comment="DOF uzerinde calisma baslatildi",
                old_status=DOFStatus.ASSIGNED,
                new_status=DOFStatus.IN_PROGRESS,
                created_at=datetime.datetime.now()
            )
            db.session.add(progress_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", kanyon_user)
            print(f"✓ DÖF #{new_dof.id} üzerinde çalışmaya başlandı bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(3)  # E-posta gönderimi için bekle
            
            # 5. ADIM: Kanyon çözümü tamamlar
            print_separator()
            print("5. ADIM: Kanyon çözümü tamamlıyor...")
            
            new_dof.status = DOFStatus.RESOLVED
            new_dof.action_plan = "Tespit edilen sorun icin uretim hatti duzenlendi ve personel egitildi."
            db.session.commit()
            
            # Çözüm aksiyonu ekle
            resolve_action = DOFAction(
                dof_id=new_dof.id,
                user_id=kanyon_user.id,
                action_type=2,  # 2: Durum değişikliği
                comment="DOF cozumu tamamlandi. Kalite onayina gonderildi.",
                old_status=DOFStatus.IN_PROGRESS,
                new_status=DOFStatus.RESOLVED,
                created_at=datetime.datetime.now()
            )
            db.session.add(resolve_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", kanyon_user)
            print(f"✓ DÖF #{new_dof.id} çözüm bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            time.sleep(3)  # E-posta gönderimi için bekle
            
            # 6. ADIM: Kalite yöneticisi DÖF'ü kapatır
            print_separator()
            print("6. ADIM: Kalite yöneticisi DÖF'ü kapatıyor...")
            
            new_dof.status = DOFStatus.CLOSED
            new_dof.closed_at = datetime.datetime.now()
            db.session.commit()
            
            # Kapatma aksiyonu ekle
            close_action = DOFAction(
                dof_id=new_dof.id,
                user_id=quality_manager.id,
                action_type=2,  # 2: Durum değişikliği
                comment="Yapilan cozum uygun bulundu. DOF kapatildi.",
                old_status=DOFStatus.RESOLVED,
                new_status=DOFStatus.CLOSED,
                created_at=datetime.datetime.now()
            )
            db.session.add(close_action)
            db.session.commit()
            
            # Bildirim gönder
            notify_for_dof(new_dof, "status_change", quality_manager)
            print(f"✓ DÖF #{new_dof.id} kapatıldı bildirimi gönderildi")
            print("  ℹ E-posta kutunuzu kontrol edin!")
            
            print_separator()
            print(f"TAM DÖF AKIŞI TESTİ TAMAMLANDI! DÖF #{new_dof.id}")
            print("E-posta kutunuzu kontrol ederek bildirimlerin gelip gelmediğini doğrulayın.")
            print_separator()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Test sırasında hata oluştu: {str(e)}")
            print(f"✗ HATA: {str(e)}")
            return False

if __name__ == "__main__":
    print("\nTAM DÖF AKIŞI TEST ARACI")
    print("------------------------")
    test_full_dof_flow()
    print("------------------------")
