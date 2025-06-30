# dof_clear_script.py - DÖF'leri temizleme scripti

from app import create_app, db
from models import DOF, DOFComment, DOFActionPlan, DOFAttachment, Notification, Activity

def clear_dofs():
    """Tüm DÖF kayıtlarını ve ilişkili verileri veritabanından siler"""
    print("🚨 UYARI: TÜM DÖF'LER SİLİNECEK!")
    print("=" * 50)
    print("Bu işlem GERİ ALINAMAZ ve TÜM DÖF verilerini siler!")
    
    # İlk onay
    print("\n⚠️  Tüm DÖF'leri silmek istediğinizden emin misiniz?")
    confirmation = input("   Devam etmek için 'TÜMÜNÜ SİL' yazın (diğer herhangi bir tuş = iptal): ").strip()
    
    if confirmation != 'TÜMÜNÜ SİL':
        print("❌ İşlem iptal edildi. Hiçbir veri silinmedi.")
        return False
    
    # İkinci onay
    print("\n🔴 SON UYARI: Bu işlem tüm DÖF verilerini kalıcı olarak silecek!")
    final_confirmation = input("   Gerçekten devam etmek için 'EVET EVET EVET' yazın: ").strip()
    
    if final_confirmation != 'EVET EVET EVET':
        print("❌ İşlem iptal edildi. Hiçbir veri silinmedi.")
        return False
    
    print("\nDÖF temizleme işlemi başlatılıyor...")
    
    app = create_app()
    with app.app_context():
        # İlişkili kayıtları önce silmeliyiz
        
        # 1. DÖF Bildirimleri
        notifications = Notification.query.filter(Notification.dof_id.isnot(None)).all()
        notification_count = len(notifications)
        for notification in notifications:
            db.session.delete(notification)
        print(f"- {notification_count} DÖF bildirimi silindi")
        
        # 2. DÖF Yorumları
        comments = DOFComment.query.all()
        comment_count = len(comments)
        for comment in comments:
            db.session.delete(comment)
        print(f"- {comment_count} DÖF yorumu silindi")
        
        # 3. DÖF Aksiyon Planları
        action_plans = DOFActionPlan.query.all()
        action_plan_count = len(action_plans)
        for plan in action_plans:
            db.session.delete(plan)
        print(f"- {action_plan_count} DÖF aksiyon planı silindi")
        
        # 4. DÖF Ekleri
        attachments = DOFAttachment.query.all()
        attachment_count = len(attachments)
        for attachment in attachments:
            db.session.delete(attachment)
        print(f"- {attachment_count} DÖF eki silindi")
        
        # 5. DOF Aktiviteleri
        activities = Activity.query.filter(Activity.activity_type.like('%DOF%')).all()
        activity_count = len(activities)
        for activity in activities:
            db.session.delete(activity)
        print(f"- {activity_count} DÖF aktivitesi silindi")
        
        # 6. Ana DÖF kayıtları
        dofs = DOF.query.all()
        dof_count = len(dofs)
        for dof in dofs:
            db.session.delete(dof)
        print(f"- {dof_count} DÖF kaydı silindi")
        
        # Değişiklikleri kaydet
        db.session.commit()
        print("\nToplam temizlenen kayıtlar:")
        print(f"- {dof_count} DÖF")
        print(f"- {notification_count} Bildirim")
        print(f"- {comment_count} Yorum")
        print(f"- {action_plan_count} Aksiyon planı")
        print(f"- {attachment_count} Dosya eki")
        print(f"- {activity_count} Aktivite kaydı")
        print("\nDÖF temizleme işlemi tamamlandı.")
        return True

if __name__ == "__main__":
    print("🚀 Toplu DÖF Temizleme Scripti")
    print("=" * 50)
    
    success = clear_dofs()
    
    if success:
        print("\n✅ Tüm DÖF'ler başarıyla silindi.")
    else:
        print("\n✅ İşlem iptal edildi, hiçbir veri silinmedi.")
