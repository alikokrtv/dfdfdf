"""
Tek bir DÖF işlem adımını test eden script.
Bu script, belirli bir DÖF ID'si için sadece tek bir adımı çalıştırır.
"""
import os
import time
import random
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import app, db
from models import User, DOF, DOFStatus, DOFAction, Department, UserRole, Notification

# Test için kullanılacak kullanıcılar ve departmanlar
TEST_USERS = {
    'department_user': None,  # Departman kullanıcısı (DÖF oluşturan)
    'quality_manager': None,  # Kalite yöneticisi
    'assigned_dept_manager': None,  # Atanan departman yöneticisi
    'source_dept_manager': None,  # Kaynak departman yöneticisi
}

TEST_DEPARTMENTS = {
    'source_department': None,  # Kaynak departman
    'assigned_department': None,  # Atanan departman
}

def setup_test_environment():
    """Test ortamını hazırla - kullanıcıları ve departmanları belirle"""
    print("Test ortamı hazırlanıyor...")
    
    # Admin kullanıcısını bul (bir çok rol için yedek olarak kullanacağız)
    admin_user = User.query.filter_by(role=UserRole.ADMIN, active=True).first()
    
    # Kalite yöneticisini bul
    quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
    if quality_managers:
        TEST_USERS['quality_manager'] = quality_managers[0]
    elif admin_user:  # Admin'i yedek olarak kullan
        TEST_USERS['quality_manager'] = admin_user
    else:
        print("HATA: Aktif kalite yöneticisi veya admin bulunamadı")
        return False
        
    print(f"Kalite yöneticisi: {TEST_USERS['quality_manager'].username}")
    
    # Aktif departmanları al
    departments = Department.query.filter_by(is_active=True).all()
    if not departments:
        print("HATA: Aktif departman bulunamadı")
        return False
        
    # Kaynak departmanı belirle
    TEST_DEPARTMENTS['source_department'] = departments[0]
    print(f"Kaynak departman: {TEST_DEPARTMENTS['source_department'].name}")
    
    # Atanan departmanı belirle (farklı bir departman olmalı)
    if len(departments) >= 2:
        # Farklı bir departman var, onu kullan
        for dept in departments:
            if dept.id != TEST_DEPARTMENTS['source_department'].id:
                TEST_DEPARTMENTS['assigned_department'] = dept
                break
    else:
        # Sadece bir departman var, aynısını kullan
        TEST_DEPARTMENTS['assigned_department'] = departments[0]
        
    print(f"Atanan departman: {TEST_DEPARTMENTS['assigned_department'].name}")
    
    # Kaynak departman kullanıcılarını bul
    source_dept_users = User.query.filter_by(
        department_id=TEST_DEPARTMENTS['source_department'].id, 
        active=True
    ).all()
    
    # Eğer kaynak departmanda hiç kullanıcı yoksa, genel kullanıcıları kullan
    if not source_dept_users:
        print(f"Uyarı: {TEST_DEPARTMENTS['source_department'].name} departmanında aktif kullanıcı yok, genel kullanıcılar kullanılacak")
        source_dept_users = User.query.filter_by(active=True).all()
        if not source_dept_users:
            print("HATA: Sistemde aktif kullanıcı yok")
            return False
    
    # Önce departman yöneticisini bulalım
    dept_manager = None
    for user in source_dept_users:
        if user.role == UserRole.DEPARTMENT_MANAGER:
            dept_manager = user
            break
    
    # Eğer departman yöneticisi bulunamadıysa, admin kullanıcısını dene
    if not dept_manager:
        dept_manager = admin_user
    
    # Hala bulunamadıysa, ilk kullanıcıyı seç
    if not dept_manager and source_dept_users:
        dept_manager = source_dept_users[0]
    
    # Kaynak departman yöneticisi ataması
    TEST_USERS['source_dept_manager'] = dept_manager
    
    # Normal kullanıcı bulalım
    normal_user = None
    for user in source_dept_users:
        if user.role == UserRole.USER:
            normal_user = user
            break
    
    # Normal kullanıcı bulunamadıysa, departman yöneticisini kullan
    if not normal_user:
        normal_user = dept_manager
    
    # Departman kullanıcısı ataması
    TEST_USERS['department_user'] = normal_user
    
    # Atanan departman yöneticisini bulalım
    assigned_dept_users = User.query.filter_by(
        department_id=TEST_DEPARTMENTS['assigned_department'].id,
        role=UserRole.DEPARTMENT_MANAGER,
        active=True
    ).all()
    
    if assigned_dept_users:
        TEST_USERS['assigned_dept_manager'] = assigned_dept_users[0]
    else:
        # Eğer atanan departmanda yönetici yoksa, genel bir yönetici veya admin kullan
        TEST_USERS['assigned_dept_manager'] = dept_manager or admin_user
    
    # Geriye kalan tüm None kullanıcıları için admin kullanıcısını kullan
    for key in TEST_USERS:
        if TEST_USERS[key] is None:
            TEST_USERS[key] = admin_user
    
    # Kullanıcı bilgilerini göster
    print(f"Departman kullanıcısı: {TEST_USERS['department_user'].username}")
    print(f"Kaynak departman yöneticisi: {TEST_USERS['source_dept_manager'].username}")
    print(f"Atanan departman yöneticisi: {TEST_USERS['assigned_dept_manager'].username}")
    
    return True

def review_and_assign_dof(dof_id):
    """Kalite yöneticisi olarak DÖF'ü incele ve bir departmana ata"""
    print(f"\nAdım: Kalite yöneticisi olarak DÖF #{dof_id} inceleniyor ve atanıyor...")
    
    try:
        # Önce veritabanından güncel DÖF'u alalım
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        print(f"Şu anki DÖF durumu: {dof.status}, departmanı: {dof.department_id}")
        
        # DÖF'ü atama durumuna güncelle
        dof.status = DOFStatus.ASSIGNED
        dof.department_id = TEST_DEPARTMENTS['assigned_department'].id
        dof.assigned_to = TEST_USERS['assigned_dept_manager'].id
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['quality_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: DÖF incelendi ve departmana atandı",
            old_status=DOFStatus.SUBMITTED,
            new_status=DOFStatus.ASSIGNED,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirim oluştur
        notification = Notification(
            user_id=TEST_USERS['assigned_dept_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} departmanınıza atandı. Lütfen inceleyip aksiyon planı hazırlayın.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        print(f"DÖF #{dof.id} {TEST_DEPARTMENTS['assigned_department'].name} departmanına atandı")
        return True
    except Exception as e:
        print(f"HATA: DÖF inceleme ve atama sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def create_action_plan(dof_id):
    """Atanan departman yöneticisi olarak aksiyon planı oluştur"""
    print(f"\nAdım: Atanan departman yöneticisi olarak DÖF #{dof_id} için aksiyon planı oluşturuluyor...")
    
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        # DÖF'ü planlama durumuna güncelle
        dof.status = DOFStatus.PLANNING
        dof.root_cause = "Otomatik test: Kök neden açıklaması"
        dof.action_plan = "Otomatik test: Aksiyon planı açıklaması"
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['assigned_dept_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: Aksiyon planı oluşturuldu",
            old_status=DOFStatus.ASSIGNED,
            new_status=DOFStatus.PLANNING,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirim oluştur
        notification = Notification(
            user_id=TEST_USERS['quality_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} için aksiyon planı hazırlandı. Lütfen inceleyip onaylayın.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        print(f"DÖF #{dof.id} için aksiyon planı oluşturuldu")
        return True
    except Exception as e:
        print(f"HATA: Aksiyon planı oluşturma sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def approve_action_plan(dof_id):
    """Kalite yöneticisi olarak aksiyon planını onayla"""
    print(f"\nAdım: Kalite yöneticisi olarak DÖF #{dof_id} aksiyon planı onaylanıyor...")
    
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        # DÖF'ü uygulama durumuna güncelle
        dof.status = DOFStatus.IMPLEMENTATION
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['quality_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: Aksiyon planı onaylandı",
            old_status=DOFStatus.PLANNING,
            new_status=DOFStatus.IMPLEMENTATION,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirim oluştur
        notification = Notification(
            user_id=TEST_USERS['assigned_dept_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} aksiyon planınız onaylandı. Lütfen aksiyonları uygulamaya başlayın.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        print(f"DÖF #{dof.id} aksiyon planı onaylandı")
        return True
    except Exception as e:
        print(f"HATA: Aksiyon planı onaylama sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def complete_actions(dof_id):
    """Atanan departman yöneticisi olarak aksiyonları tamamla"""
    print(f"\nAdım: Atanan departman yöneticisi olarak DÖF #{dof_id} aksiyonları tamamlanıyor...")
    
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        # DÖF'ü tamamlandı durumuna güncelle
        dof.status = DOFStatus.COMPLETED
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['assigned_dept_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: Aksiyonlar tamamlandı",
            old_status=DOFStatus.IMPLEMENTATION,
            new_status=DOFStatus.COMPLETED,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirimler oluştur
        notification1 = Notification(
            user_id=TEST_USERS['quality_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} aksiyonları tamamlandı. Bilginize.",
            is_read=False,
            created_at=datetime.now()
        )
        
        notification2 = Notification(
            user_id=TEST_USERS['source_dept_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} aksiyonları tamamlandı. Lütfen inceleyip onaylayın.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification1)
        db.session.add(notification2)
        db.session.commit()
        
        print(f"DÖF #{dof.id} aksiyonları tamamlandı")
        return True
    except Exception as e:
        print(f"HATA: Aksiyonları tamamlama sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def approve_solution(dof_id):
    """Kaynak departman yöneticisi olarak çözümü onayla"""
    print(f"\nAdım: Kaynak departman yöneticisi olarak DÖF #{dof_id} çözümü onaylanıyor...")
    
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        # DÖF'ü çözüldü durumuna güncelle
        dof.status = DOFStatus.RESOLVED
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['source_dept_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: Çözüm onaylandı",
            old_status=DOFStatus.COMPLETED,
            new_status=DOFStatus.RESOLVED,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirim oluştur
        notification = Notification(
            user_id=TEST_USERS['quality_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} çözümü kaynak departman tarafından onaylandı. Son kapatma işlemi için değerlendirme yapabilirsiniz.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        print(f"DÖF #{dof.id} çözümü onaylandı")
        return True
    except Exception as e:
        print(f"HATA: Çözüm onaylama sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def close_dof(dof_id):
    """Kalite yöneticisi olarak DÖF'ü kapat"""
    print(f"\nAdım: Kalite yöneticisi olarak DÖF #{dof_id} kapatılıyor...")
    
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"HATA: DÖF #{dof_id} veritabanında bulunamadı")
            return False
            
        # DÖF'ü kapatıldı durumuna güncelle
        dof.status = DOFStatus.CLOSED
        dof.closing_notes = "Otomatik test: DÖF başarıyla kapatılmıştır."
        dof.closed_at = datetime.now()
        dof.updated_at = datetime.now()
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=TEST_USERS['quality_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: DÖF kapatıldı",
            old_status=DOFStatus.RESOLVED,
            new_status=DOFStatus.CLOSED,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        
        # Bildirimler oluştur
        notification1 = Notification(
            user_id=TEST_USERS['source_dept_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} kalite departmanı tarafından kapatıldı.",
            is_read=False,
            created_at=datetime.now()
        )
        
        notification2 = Notification(
            user_id=TEST_USERS['assigned_dept_manager'].id,
            dof_id=dof.id,
            message=f"DÖF #{dof.id} kalite departmanı tarafından kapatıldı.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification1)
        db.session.add(notification2)
        db.session.commit()
        
        print(f"DÖF #{dof.id} kapatıldı")
        return True
    except Exception as e:
        print(f"HATA: DÖF kapatma sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Kullanım: python test_single_step.py <dof_id> <işlem_adımı>")
        print("İşlem adımları:")
        print("1 - İnceleme ve Atama")
        print("2 - Aksiyon Planı Oluşturma")
        print("3 - Aksiyon Planı Onaylama")
        print("4 - Aksiyonları Tamamlama")
        print("5 - Çözüm Onaylama")
        print("6 - DÖF Kapatma")
        sys.exit(1)
    
    dof_id = int(sys.argv[1])
    step = int(sys.argv[2])
    
    with app.app_context():
        try:
            # Test ortamını hazırla
            if not setup_test_environment():
                print("Test ortamı hazırlanamadı.")
                sys.exit(1)
            
            # Belirtilen adımı çalıştır
            if step == 1:
                result = review_and_assign_dof(dof_id)
            elif step == 2:
                result = create_action_plan(dof_id)
            elif step == 3:
                result = approve_action_plan(dof_id)
            elif step == 4:
                result = complete_actions(dof_id)
            elif step == 5:
                result = approve_solution(dof_id)
            elif step == 6:
                result = close_dof(dof_id)
            else:
                print(f"Geçersiz adım: {step}")
                sys.exit(1)
            
            if result:
                print(f"\nAdım {step} başarıyla tamamlandı!")
            else:
                print(f"\nAdım {step} başarısız oldu!")
                
        except Exception as e:
            print(f"Hata: {str(e)}")
            import traceback
            traceback.print_exc()
