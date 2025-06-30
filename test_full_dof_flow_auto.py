"""
DÖF sürecini otomatik olarak test eden script.
Bu script şunları yapar:
1. Departman kullanıcısı olarak bir DÖF oluşturur
2. Kalite yöneticisi olarak giriş yapıp DÖF'ü inceler ve bir departmana atar
3. Atanan departman yöneticisi olarak giriş yapıp aksiyon planı oluşturur
4. Kalite yöneticisi olarak giriş yapıp aksiyon planını onaylar
5. Atanan departman yöneticisi olarak aksiyonları tamamlar
6. Kaynak departman yöneticisi olarak çözümü onaylar
7. Kalite yöneticisi olarak DÖF'ü kapatır

Kullanım:
python test_full_dof_flow_auto.py
"""
import os
import time
import random
from flask import Flask, session
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

def create_test_dof():
    """Departman kullanıcısı olarak bir DÖF oluştur"""
    print("\n1. Departman kullanıcısı olarak DÖF oluşturuluyor...")
    
    # DÖF başlığı ve açıklaması
    dof_title = f"Otomatik Test DÖF - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    dof_description = "Bu DÖF otomatik test scripti tarafından oluşturulmuştur."
    
    # DÖF oluştur
    dof = DOF(
        title=dof_title,
        description=dof_description,
        status=DOFStatus.SUBMITTED,  # Doğrudan gönderildi olarak oluştur
        dof_type=1,  # Düzeltici Faaliyet
        dof_source=1,  # İç Denetim
        priority=2,  # Orta
        created_by=TEST_USERS['department_user'].id,
        department_id=TEST_DEPARTMENTS['source_department'].id,  # Kaynak departman
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.session.add(dof)
    db.session.commit()
    
    print(f"DÖF oluşturuldu: #{dof.id} - {dof_title}")
    return dof

def review_and_assign_dof(dof):
    """Kalite yöneticisi olarak DÖF'ü incele ve bir departmana ata"""
    print(f"\n2. Kalite yöneticisi olarak DÖF #{dof.id} inceleniyor ve atanıyor...")
    
    try:
        # Önce veritabanından güncel DÖF'u alalım
        fresh_dof = DOF.query.get(dof.id)
        if not fresh_dof:
            print(f"HATA: DÖF #{dof.id} veritabanında bulunamadı")
            return False
            
        print(f"DEBUG: Şu anki DÖF durumu: {fresh_dof.status}, departmanı: {fresh_dof.department_id}")
        
        # DÖF'ü atama durumuna güncelle
        fresh_dof.status = DOFStatus.ASSIGNED
        fresh_dof.department_id = TEST_DEPARTMENTS['assigned_department'].id
        fresh_dof.assigned_to = TEST_USERS['assigned_dept_manager'].id
        fresh_dof.updated_at = datetime.now()
        
        print(f"DEBUG: DÖF güncellendi, yeni durum: {fresh_dof.status}, yeni departman: {fresh_dof.department_id}")
        
        # İşlem kaydı oluştur
        action = DOFAction(
            dof_id=fresh_dof.id,
            user_id=TEST_USERS['quality_manager'].id,
            action_type=2,  # Durum Değişikliği
            comment="Otomatik test: DÖF incelendi ve departmana atandı",
            old_status=DOFStatus.SUBMITTED,
            new_status=DOFStatus.ASSIGNED,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        print("DEBUG: İşlem kaydı oluşturuldu")
        
        # Bildirim oluştur
        notification = Notification(
            user_id=TEST_USERS['assigned_dept_manager'].id,
            dof_id=fresh_dof.id,
            message=f"DÖF #{fresh_dof.id} departmanınıza atandı. Lütfen inceleyip aksiyon planı hazırlayın.",
            is_read=False,
            created_at=datetime.now()
        )
        
        db.session.add(notification)
        print("DEBUG: Bildirim oluşturuldu")
        
        # Veritabanı işlemlerini tamamla
        db.session.commit()
        print("DEBUG: Veritabanı işlemleri tamamlandı")
        
        print(f"DÖF #{fresh_dof.id} {TEST_DEPARTMENTS['assigned_department'].name} departmanına atandı")
        return True
    except Exception as e:
        print(f"HATA: DÖF inceleme ve atama sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def create_action_plan(dof):
    """Atanan departman yöneticisi olarak aksiyon planı oluştur"""
    print(f"\n3. Atanan departman yöneticisi olarak DÖF #{dof.id} için aksiyon planı oluşturuluyor...")
    
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
        comment="Otomatik test: Aksiyon planı hazırlandı",
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

def approve_action_plan(dof):
    """Kalite yöneticisi olarak aksiyon planını onayla"""
    print(f"\n4. Kalite yöneticisi olarak DÖF #{dof.id} aksiyon planı onaylanıyor...")
    
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

def complete_actions(dof):
    """Atanan departman yöneticisi olarak aksiyonları tamamla"""
    print(f"\n5. Atanan departman yöneticisi olarak DÖF #{dof.id} aksiyonları tamamlanıyor...")
    
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
    
    # Bildirim oluştur - Hem kalite hem kaynak departman yöneticisine
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

def approve_solution(dof):
    """Kaynak departman yöneticisi olarak çözümü onayla"""
    print(f"\n6. Kaynak departman yöneticisi olarak DÖF #{dof.id} çözümü onaylanıyor...")
    
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

def close_dof(dof):
    """Kalite yöneticisi olarak DÖF'ü kapat"""
    print(f"\n7. Kalite yöneticisi olarak DÖF #{dof.id} kapatılıyor...")
    
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
    
    # Bildirim oluştur
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

def run_test_flow():
    """Tüm test akışını çalıştır"""
    print("DÖF test akışı başlatılıyor...")
    
    # Uygulama bağlamı içinde çalış
    with app.app_context():
        try:
            # Test ortamını hazırla
            if not setup_test_environment():
                print("Test ortamı hazırlanamadı. Test iptal ediliyor.")
                return
                
            print("\n---- Test ortamı başarıyla hazırlandı, DÖF oluşturuluyor ----")
            # DÖF oluştur
            dof = create_test_dof()
            if not dof:
                print("DÖF oluşturma başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} başarıyla oluşturuldu, inceleme ve atama aşamasına geçiliyor ----")
            # İşlemler arasında bekleme
            time.sleep(3)
            
            # DÖF'ü incele ve ata
            if not review_and_assign_dof(dof):
                print("DÖF inceleme ve atama başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} başarıyla incelendi ve atandı, aksiyon planı oluşturuluyor ----")
            time.sleep(3)
            
            # Aksiyon planı oluştur
            if not create_action_plan(dof):
                print("Aksiyon planı oluşturma başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} için aksiyon planı başarıyla oluşturuldu, plan onaylanıyor ----")
            time.sleep(3)
            
            # Aksiyon planını onayla
            if not approve_action_plan(dof):
                print("Aksiyon planı onaylama başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} aksiyon planı başarıyla onaylandı, aksiyonlar tamamlanıyor ----")
            time.sleep(3)
            
            # Aksiyonları tamamla
            if not complete_actions(dof):
                print("Aksiyonları tamamlama başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} aksiyonları başarıyla tamamlandı, çözüm onaylanıyor ----")
            time.sleep(3)
            
            # Çözümü onayla
            if not approve_solution(dof):
                print("Çözüm onaylama başarısız. Test iptal ediliyor.")
                return
            
            print(f"\n---- DÖF #{dof.id} çözümü başarıyla onaylandı, DÖF kapatılıyor ----")
            time.sleep(3)
            
            # DÖF'ü kapat
            if not close_dof(dof):
                print("DÖF kapatma başarısız. Test iptal ediliyor.")
                return
            
            print(f"\nDÖF #{dof.id} için tam test akışı başarıyla tamamlandı!")
            print(f"Test DÖF'un son durumu: {dof.status} (Kapatıldı)")
            print("\nTest tamamlandı!")
            
        except Exception as e:
            print(f"\nHATA: Test sırasında bir istisna oluştu: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("DÖF SÜRECİ TAM TESTİ BAŞLATILIYOR")
    print("=" * 50 + "\n")
    
    # Uygulama bağlamı içinde çalış
    with app.app_context():
        try:
            # Test ortamını hazırla
            print("\n" + "-" * 50)
            print("ADIM 0: Test Ortamı Hazırlanıyor")
            print("-" * 50)
            if not setup_test_environment():
                print("\nHATA: Test ortamı hazırlanamadı.")
                exit(1)
            print("\nBaşarılı: Test ortamı hazırlandı!")
            
            # ADIM 1: DÖF Oluşturma
            print("\n" + "-" * 50)
            print("ADIM 1: DÖF Oluşturuluyor")
            print("-" * 50)
            dof = create_test_dof()
            if not dof:
                print("\nHATA: DÖF oluşturulamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} oluşturuldu!")
            time.sleep(2)
            
            # ADIM 2: DÖF İnceleme ve Atama
            print("\n" + "-" * 50)
            print("ADIM 2: DÖF İnceleniyor ve Atanıyor")
            print("-" * 50)
            if not review_and_assign_dof(dof):
                print("\nHATA: DÖF inceleme ve atama başarısız.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} incelendi ve atandı!")
            time.sleep(2)
            
            # ADIM 3: Aksiyon Planı Oluşturma
            print("\n" + "-" * 50)
            print("ADIM 3: Aksiyon Planı Oluşturuluyor")
            print("-" * 50)
            if not create_action_plan(dof):
                print("\nHATA: Aksiyon planı oluşturulamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} için aksiyon planı oluşturuldu!")
            time.sleep(2)
            
            # ADIM 4: Aksiyon Planı Onaylama
            print("\n" + "-" * 50)
            print("ADIM 4: Aksiyon Planı Onaylanıyor")
            print("-" * 50)
            if not approve_action_plan(dof):
                print("\nHATA: Aksiyon planı onaylanamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} aksiyon planı onaylandı!")
            time.sleep(2)
            
            # ADIM 5: Aksiyonları Tamamlama
            print("\n" + "-" * 50)
            print("ADIM 5: Aksiyonlar Tamamlanıyor")
            print("-" * 50)
            if not complete_actions(dof):
                print("\nHATA: Aksiyonlar tamamlanamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} aksiyonları tamamlandı!")
            time.sleep(2)
            
            # ADIM 6: Çözüm Onaylama
            print("\n" + "-" * 50)
            print("ADIM 6: Çözüm Onaylanıyor")
            print("-" * 50)
            if not approve_solution(dof):
                print("\nHATA: Çözüm onaylanamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} çözümü onaylandı!")
            time.sleep(2)
            
            # ADIM 7: DÖF Kapatma
            print("\n" + "-" * 50)
            print("ADIM 7: DÖF Kapatılıyor")
            print("-" * 50)
            if not close_dof(dof):
                print("\nHATA: DÖF kapatılamadı.")
                exit(1)
            print(f"\nBaşarılı: DÖF #{dof.id} kapatıldı!")
            
            # TEST TAMAMLANDI
            print("\n" + "=" * 50)
            print(f"DÖF #{dof.id} İÇİN TAM TEST SÜRECİ BAŞARIYLA TAMAMLANDI!")
            print(f"Son durum: {dof.status_name}")
            print("=" * 50 + "\n")
            
        except Exception as e:
            print(f"\nKRİTİK HATA: Test sırasında beklenmeyen bir hata oluştu!")
            print(f"Hata: {str(e)}")
            import traceback
            traceback.print_exc()
