#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit Yorum Ekleme Debug Scripti
"""

from app import app, db
from models import DOF, DOFAction, User
from flask import request

def simple_comment_test():
    """En basit yorum ekleme testi"""
    
    with app.app_context():
        print("🔍 Basit Yorum Ekleme Debug")
        print("=" * 50)
        
        try:
            # Son DÖF'ü bul
            dof = DOF.query.order_by(DOF.created_at.desc()).first()
            print(f"📋 DÖF bulundu: #{dof.id}")
            
            # Aktif kullanıcı bul
            user = User.query.filter_by(active=True).first()
            print(f"👤 Kullanıcı bulundu: {user.full_name}")
            
            # Sadece basit yorum ekle - dosya yok
            action = DOFAction(
                dof_id=dof.id,
                user_id=user.id,
                action_type=1,  # Yorum
                comment="TEST: Basit yorum ekleme testi"
            )
            
            db.session.add(action)
            db.session.commit()
            
            print("✅ Basit yorum eklendi!")
            
            # Kontrolü
            last_action = DOFAction.query.filter_by(dof_id=dof.id).order_by(DOFAction.created_at.desc()).first()
            print(f"📝 Son yorum: {last_action.comment}")
            
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            import traceback
            print(traceback.format_exc())
            db.session.rollback()

if __name__ == "__main__":
    simple_comment_test() 