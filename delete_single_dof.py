#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tek DÖF Silme Scripti - Test için güvenli DÖF silme
"""

import sys
from app import app, db
from models import DOF, DOFAction, Attachment, ActionAttachment, Notification, UserActivity

def delete_single_dof(dof_id):
    """Belirtilen ID'ye sahip DÖF'ü ve tüm ilişkili verilerini siler"""
    
    with app.app_context():
        # DÖF'ü bul
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"❌ DÖF #{dof_id} bulunamadı!")
            return False
        
        print(f"🔍 DÖF #{dof_id} bulundu:")
        print(f"   📋 Başlık: {dof.title}")
        print(f"   👤 Oluşturan: {dof.creator.full_name if dof.creator else 'Bilinmiyor'}")
        print(f"   🏢 Departman: {dof.department.name if dof.department else 'Belirtilmemiş'}")
        print(f"   📅 Oluşturma: {dof.created_at.strftime('%d.%m.%Y %H:%M')}")
        print(f"   📊 Durum: {dof.status_name}")
        
        # Onay iste
        print(f"\n⚠️  Bu DÖF'ü ve tüm ilişkili verilerini silmek istediğinizden emin misiniz?")
        confirmation = input("   Silmek için 'EVET' yazın (diğer herhangi bir tuş = iptal): ").strip().upper()
        
        if confirmation != 'EVET':
            print("❌ İşlem iptal edildi.")
            return False
        
        try:
            # İlişkili kayıtları say
            actions = DOFAction.query.filter_by(dof_id=dof_id).all()
            attachments = Attachment.query.filter_by(dof_id=dof_id).all()
            action_attachments = []
            for action in actions:
                action_attachments.extend(ActionAttachment.query.filter_by(action_id=action.id).all())
            notifications = Notification.query.filter_by(dof_id=dof_id).all()
            activities = UserActivity.query.filter_by(related_id=dof_id, activity_type='dof_action').all()
            
            print(f"\n📊 Silinecek veriler:")
            print(f"   🎯 1 DÖF")
            print(f"   💬 {len(actions)} aksiyon/yorum")
            print(f"   📎 {len(attachments)} DÖF eki")
            print(f"   📁 {len(action_attachments)} yorum eki")
            print(f"   🔔 {len(notifications)} bildirim")
            print(f"   📝 {len(activities)} aktivite kaydı")
            
            # Son onay
            final_confirmation = input("\n❓ Devam etmek istediğinizden emin misiniz? 'EVET' yazın: ").strip().upper()
            if final_confirmation != 'EVET':
                print("❌ İşlem iptal edildi.")
                return False
            
            # Silme işlemi
            print("\n🗑️  Silme işlemi başlıyor...")
            
            # 1. Yorum ekleri
            for attachment in action_attachments:
                db.session.delete(attachment)
            print(f"   ✅ {len(action_attachments)} yorum eki silindi")
            
            # 2. DÖF eylemi/yorumları
            for action in actions:
                db.session.delete(action)
            print(f"   ✅ {len(actions)} aksiyon/yorum silindi")
            
            # 3. DÖF ekleri
            for attachment in attachments:
                db.session.delete(attachment)
            print(f"   ✅ {len(attachments)} DÖF eki silindi")
            
            # 4. Bildirimler
            for notification in notifications:
                db.session.delete(notification)
            print(f"   ✅ {len(notifications)} bildirim silindi")
            
            # 5. Aktiviteler
            for activity in activities:
                db.session.delete(activity)
            print(f"   ✅ {len(activities)} aktivite kaydı silindi")
            
            # 6. Ana DÖF kaydı
            db.session.delete(dof)
            print(f"   ✅ DÖF #{dof_id} silindi")
            
            # Değişiklikleri kaydet
            db.session.commit()
            
            print(f"\n🎉 DÖF #{dof_id} başarıyla silindi!")
            return True
            
        except Exception as e:
            print(f"\n❌ Hata oluştu: {str(e)}")
            db.session.rollback()
            return False

def main():
    if len(sys.argv) != 2:
        print("❌ Kullanım: python delete_single_dof.py <dof_id>")
        print("   Örnek: python delete_single_dof.py 123")
        sys.exit(1)
    
    try:
        dof_id = int(sys.argv[1])
    except ValueError:
        print("❌ DÖF ID'si sayı olmalı!")
        sys.exit(1)
    
    if dof_id <= 0:
        print("❌ DÖF ID'si pozitif bir sayı olmalı!")
        sys.exit(1)
    
    print("🚀 Tek DÖF Silme Scripti")
    print("=" * 50)
    
    success = delete_single_dof(dof_id)
    
    if success:
        print("\n✅ İşlem başarıyla tamamlandı.")
        sys.exit(0)
    else:
        print("\n❌ İşlem başarısız.")
        sys.exit(1)

if __name__ == "__main__":
    main() 