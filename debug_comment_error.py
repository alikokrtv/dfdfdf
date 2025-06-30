#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yorum ekleme hatası debug scripti
"""

import sys
import os
from datetime import datetime

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import DOF, User, DOFAction, UserRole
    from flask import request
    import traceback

    def test_comment_functionality():
        print("🔍 Yorum Ekleme Hata Debug")
        print("=" * 50)
        
        with app.app_context():
            try:
                # Test DÖF'ü bul
                dof = DOF.query.order_by(DOF.created_at.desc()).first()
                if not dof:
                    print("❌ Hiç DÖF bulunamadı")
                    return
                
                print(f"📋 Test DÖF: #{dof.id} - {dof.title}")
                print(f"📊 DÖF Durumu: {dof.status}")
                
                # Departman yöneticisi bul
                dept_manager = User.query.filter_by(role=UserRole.DEPARTMENT_MANAGER).first()
                if not dept_manager:
                    print("❌ Departman yöneticisi bulunamadı")
                    return
                
                print(f"👤 Departman Yöneticisi: {dept_manager.full_name}")
                print(f"🏢 Departman: {dept_manager.department.name if dept_manager.department else 'Yok'}")
                
                # Yorum ekleme testi
                print("\n📝 Yorum ekleme testi başlıyor...")
                
                # DOFAction oluştur
                action = DOFAction(
                    dof_id=dof.id,
                    user_id=dept_manager.id,
                    action_type=1,  # Yorum
                    comment="TEST: Debug yorum ekleme testi",
                    created_at=datetime.now()
                )
                
                print("✓ DOFAction nesnesi oluşturuldu")
                
                # Veritabanına ekle
                db.session.add(action)
                print("✓ Session'a eklendi")
                
                # Commit yap
                db.session.commit()
                print("✓ Veritabanına kaydedildi")
                
                print("✅ Yorum başarıyla eklendi!")
                print(f"📝 Yorum ID: {action.id}")
                
            except Exception as e:
                print(f"❌ Hata: {str(e)}")
                print("\n🔍 Detaylı hata bilgisi:")
                print(traceback.format_exc())
                
                # Rollback yap
                try:
                    db.session.rollback()
                    print("↩️ Session rollback yapıldı")
                except:
                    pass

    if __name__ == "__main__":
        test_comment_functionality()
        
except ImportError as e:
    print(f"❌ Import hatası: {str(e)}")
except Exception as e:
    print(f"❌ Genel hata: {str(e)}")
    import traceback
    print(traceback.format_exc()) 