#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yorum Ekleme Hatası Debug Scripti
"""

from app import app, db
from models import DOF, DOFAction, User
from utils import save_file, allowed_file
import tempfile
import os

def test_add_comment():
    """Yorum ekleme işlemini test et"""
    
    with app.app_context():
        print("🔍 Yorum Ekleme Debug Testi")
        print("=" * 50)
        
        # Mevcut DÖF'ü bul
        dof = DOF.query.order_by(DOF.created_at.desc()).first()
        if not dof:
            print("❌ Test edilecek DÖF bulunamadı!")
            return
            
        print(f"📋 DÖF: #{dof.id} - {dof.title}")
        print(f"📊 Durum: {dof.status_name}")
        
        # Aktif kullanıcı bul
        user = User.query.filter_by(active=True).first()
        if not user:
            print("❌ Aktif kullanıcı bulunamadı!")
            return
            
        print(f"👤 Kullanıcı: {user.full_name}")
        
        # Test yorum oluştur
        try:
            action = DOFAction(
                dof_id=dof.id,
                user_id=user.id,
                action_type=1,  # Yorum
                comment="Test yorumu - Debug amaçlı eklendi.",
                old_status=None,
                new_status=None
            )
            
            db.session.add(action)
            db.session.flush()  # ID'yi al
            
            print(f"✅ DOFAction oluşturuldu: ID #{action.id}")
            
            # Test dosyası oluştur
            test_content = b"Bu bir test dosyasidir."
            
            # Temporary dosya oluştur
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_path = temp_file.name
            
            print(f"📁 Test dosyası oluşturuldu: {temp_path}")
            
            # save_file fonksiyonunu test et
            from werkzeug.datastructures import FileStorage
            with open(temp_path, 'rb') as f:
                test_file = FileStorage(
                    stream=f,
                    filename='test.txt',
                    content_type='text/plain'
                )
                
                print("🔧 save_file fonksiyonu test ediliyor...")
                file_data = save_file(test_file)
                print(f"✅ save_file sonucu: {file_data}")
                
                # ActionAttachment oluştur
                from models import ActionAttachment
                attachment = ActionAttachment(
                    action_id=action.id,
                    filename=file_data['filename'],
                    file_path=file_data['file_path'],
                    file_size=file_data['file_size'],
                    file_type=file_data['file_type'],
                    uploaded_by=user.id
                )
                
                db.session.add(attachment)
                print(f"✅ ActionAttachment oluşturuldu")
            
            # Cleanup
            os.unlink(temp_path)
            
            # Commit test
            db.session.commit()
            print("✅ Veritabanı commit başarılı")
            
            # Kontrol et
            saved_action = DOFAction.query.get(action.id)
            attachments = saved_action.attachments.all()
            print(f"📎 Kaydedilen ek sayısı: {len(attachments)}")
            
            for att in attachments:
                print(f"   - {att.filename}")
                
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
            import traceback
            print(f"Detay: {traceback.format_exc()}")
            db.session.rollback()

if __name__ == "__main__":
    test_add_comment() 