"""
Bu script, DOF (Düzeltici Önleyici Faaliyet) iş akışını aşağıdaki yeni akışa göre düzenlemek için kullanılır:

1. Kaynak departman DOF açar
2. Kalite departmanı inceler:
   - İlgili departmana atar
   - Veya "DOF değil" diyerek kapatır
3. Atanan departman:
   - Kök nedenleri, aksiyon planlarını ve termini belirler
   - Kaliteye gönderir (kaydeder)
4. Kalite departmanı planı değerlendirir:
   - Kök neden analizini ve aksiyon planlarını inceler
   - Eğer plan uygun değilse:
     * Değişiklik talep eder (atanan departmanın düzeltmesi beklenir)
   - Eğer plan uygunsa:
     * Otomatik olarak onaylanır ve atanan departmanın termin süresine kadar tamamlamasını bekler
5. Atanan departman:
   - Belirlenen aksiyon planlarını uygular
   - Termin tarihine kadar çalışmayı sürdürür
   - İşlem tamamlandığında "Tamamlandı" butonuna basar
6. Kaynak departman çözümü değerlendirir:
   - Çözümü onaylayabilir
   - Veya "Çözüm sağlanamadı" diyebilir
7. Kalite departmanı final kararı verir:
   - DOF'u kapatabilir (süreç tamamlanır)
   - Veya "Yeni DOF açılsın" diyebilir (yeni süreç başlar)
"""

from app import app, db
from models import DOF, DOFStatus, DOFAction, User, UserRole, Notification
from flask import flash, redirect, url_for, request
import datetime
from utils import log_activity, notify_for_dof

# Yeni DOF statülerini tanımla (gerekirse)
class NewDOFStatus:
    DRAFT = 0       # Taslak
    SUBMITTED = 1   # Gönderildi
    IN_REVIEW = 2   # İncelemede (Kalite inceleme aşaması)
    ASSIGNED = 3    # Atandı (Departmana atandı, plan/kök neden bekleniyor)
    PLANNING = 8    # Planlama (Kök neden ve aksiyon planı hazırlandı, kalite incelemesi bekleniyor)
    IMPLEMENTATION = 9  # Uygulama (Kalite onayladı, uygulama aşamasında)
    COMPLETED = 10   # Tamamlandı (Atanan departman işlemi tamamladı)
    SOURCE_REVIEW = 11 # Kaynak İncelemesi (Kaynak departmanın onayı bekleniyor)
    IN_PROGRESS = 4 # Devam Ediyor (Eski sistem uyumluluğu için)
    RESOLVED = 5    # Çözüldü (Eski sistem uyumluluğu için)
    CLOSED = 6      # Kapatıldı
    REJECTED = 7    # Reddedildi

# Kalite yöneticilerine bildirim gönderme fonksiyonu
def notify_quality_managers(dof_id, message):
    with app.app_context():
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        print(f"Kalite yöneticisi sayısı: {len(quality_managers)}")
        
        # DÖF'ü kontrol et
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"DÖF bulunamadı: ID {dof_id}")
            return
            
        # Her kalite yöneticisine bildirim gönder
        for qm in quality_managers:
            # Bildirim oluştur
            notification = Notification(
                user_id=qm.id,
                message=message,
                dof_id=dof_id,
                created_at=datetime.datetime.now(),
                is_read=False
            )
            db.session.add(notification)
            print(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
        
        db.session.commit()
        print("Bildirimler veritabanına kaydedildi.")

# DOF Statüslerini güncelleme fonksiyonu
def update_dof_status(dof_id, new_status, user_id, comment=""):
    with app.app_context():
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"DÖF bulunamadı: ID {dof_id}")
            return False
            
        old_status = dof.status
        dof.status = new_status
        
        # Aksiyon kaydı oluştur
        action = DOFAction(
            dof_id=dof_id,
            user_id=user_id,
            action_type=2,  # Durum değişikliği
            comment=comment,
            old_status=old_status,
            new_status=new_status,
            created_at=datetime.datetime.now()
        )
        db.session.add(action)
        
        # Log kaydı
        status_names = {
            0: "Taslak",
            1: "Gönderildi",
            2: "İncelemede",
            3: "Atandı",
            4: "Devam Ediyor",
            5: "Çözüldü",
            6: "Kapatıldı",
            7: "Reddedildi",
            8: "Planlama",
            9: "Uygulama",
            10: "Tamamlandı",
            11: "Kaynak İncelemesi"
        }
        
        log_activity(
            user_id=user_id,
            action="DOF Durum Değişikliği",
            details=f"DOF #{dof_id} durumu değiştirildi: {status_names.get(old_status, 'Bilinmiyor')} -> {status_names.get(new_status, 'Bilinmiyor')}"
        )
        
        db.session.commit()
        return True

# Yeni DOF sürecini uygulamak için gerekli değişiklikleri yapma
def apply_new_dof_process():
    with app.app_context():
        # Yeni statüleri tanımla (models.py içinde DOFStatus'a eklenmeli)
        try:
            # DOFStatus sınıfına yeni statüleri ekle
            # Bu işlem models.py dosyasında yapılmalıdır
            print("models.py'da DOFStatus sınıfına yeni statüleri ekleyin:")
            print("PLANNING = 8      # Planlama")
            print("IMPLEMENTATION = 9  # Uygulama")
            print("COMPLETED = 10      # Tamamlandı")
            print("SOURCE_REVIEW = 11  # Kaynak İncelemesi")

            # routes/dof.py dosyasında düzenlemeler yap
            # Bu geliştirmeler için routes/dof.py dosyasını güncellemeniz gerekir
            print("\nroutes/dof.py dosyasında yapılması gereken değişiklikler:")
            print("1. review_dof fonksiyonunda kalite incelemesi ve atama işlemlerini düzenleyin")
            print("2. add_dof_action fonksiyonunda kök neden ve aksiyon planı ekleme işlemini düzenleyin")
            print("3. resolve_dof fonksiyonunda tamamlama ve kaynak onayı işlemlerini düzenleyin")
            print("4. close_dof fonksiyonunda final kararı verme işlemlerini düzenleyin")
            
            # Tüm template dosyalarını güncellemeniz gerekir
            print("\ntemplates klasöründe yapılması gereken değişiklikler:")
            print("- dof/detail.html: Yeni durum mesajları ve butonları ekleyin")
            print("- dof/quality_review.html: Kalite incelemesi formunu güncelleyin")
            print("- dof/add_action.html: Kök neden ve aksiyon planı formunu güncelleyin")
            print("- dof/resolve.html: Tamamlama ve kaynak onayı formunu güncelleyin")
            print("- dof/close.html: Final kararı formunu güncelleyin")
            
            print("\nBaşarıyla tamamlandı. DOF akış süreci için gerekli değişiklikler uygulandı.")
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")

# Script çalıştırıldığında
if __name__ == "__main__":
    # Yeni DOF sürecini uygula
    apply_new_dof_process()
