"""
DÖF bildirim sistemini düzeltme scripti - Formla oluşturulan DÖF'ler için bildirimler doğru gönderilmiyor
Sorunu çözmek için DÖF.py dosyasında doğrudan bildirim kodu ekleyeceğiz.
"""

from app import app, db
from models import DOF, DOFStatus, UserRole, User, Notification
import datetime

def fix_notification_system():
    print("DÖF sistemi bildirim düzeltme scripti çalışıyor...")
    
    # DÖF ve create_dof.py'de bulunacak ve eklenecek kodları hazırla
    notification_fix_code = """
# DÖF oluşturma işlemi tamamlandıktan sonra doğrudan kalite yöneticilerine bildirim gönder
def send_direct_notifications_to_quality_managers(dof_id, creator_name, dof_title):
    current_app.logger.info(f"Doğrudan bildirim sistemi çalışıyor (DÖF #{dof_id})")
    try:
        # DÖF kontrolü
        dof = DOF.query.get(dof_id)
        if not dof:
            current_app.logger.error(f"DÖF bulunamadı: {dof_id}")
            return False
            
        # Kalite yöneticilerini bul - UserRole.QUALITY_MANAGER kullanarak
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        current_app.logger.info(f"{len(quality_managers)} kalite yöneticisi bulundu")
        
        # Her kalite yöneticisine bildirim gönder
        notification_count = 0
        for qm in quality_managers:
            try:
                # Bildirim oluştur
                notification = Notification(
                    user_id=qm.id,
                    dof_id=dof_id,
                    message=f"{creator_name} tarafından '{dof_title}' (#{dof_id}) başlıklı yeni bir DÖF oluşturuldu.",
                    created_at=datetime.datetime.now(),
                    is_read=False
                )
                db.session.add(notification)
                current_app.logger.info(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
                notification_count += 1
            except Exception as e:
                current_app.logger.error(f"Bildirim oluşturma hatası ({qm.username}): {str(e)}")
        
        # Veritabanına kaydet
        if notification_count > 0:
            db.session.commit()
            current_app.logger.info(f"Toplam {notification_count} bildirim veritabanına kaydedildi")
            return True
        
        return False
    except Exception as e:
        current_app.logger.error(f"Bildirim sistemi genel hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False
"""

    # DÖF oluşturma kodundan sonra çağrılacak kod
    implementation_code = """
        # Kalite yöneticilerine doğrudan bildirim gönder
        try:
            send_direct_notifications_to_quality_managers(dof.id, current_user.full_name, dof.title)
            current_app.logger.info(f"DÖF oluşturma sonrası doğrudan bildirim gönderim çağrısı tamamlandı: {dof.id}")
        except Exception as e:
            current_app.logger.error(f"Doğrudan bildirim hatası: {str(e)}")
"""

    print("Bu scripti dof.py dosyasını güncellemeniz gerekiyor.")
    print("\n1. DOF.py dosyasının başına şu fonksiyonu ekleyin:")
    print("-" * 80)
    print(notification_fix_code)
    print("-" * 80)
    
    print("\n2. DÖF oluşturma kodunun sonuna, flash mesajından ÖNCE şu kodu ekleyin:")
    print("-" * 80)
    print(implementation_code)
    print("-" * 80)
    
    print("\nBu değişiklikler, DÖF formunu doldurduğunuzda bildirimlerin doğrudan kalite yöneticilerine gönderilmesini sağlayacaktır.")
    print("Uygulamayı yeniden başlattıktan sonra yeni bir DÖF oluşturarak test edin.")
    
if __name__ == "__main__":
    fix_notification_system()
