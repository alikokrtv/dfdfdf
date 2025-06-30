#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ActionAttachment Debug Scripti
"""

from app import app, db
from models import DOF, DOFAction, ActionAttachment

def debug_action_attachments():
    """ActionAttachment verilerini debug et"""
    
    with app.app_context():
        print("🔍 ActionAttachment Debug Raporu")
        print("=" * 50)
        
        # Tüm ActionAttachment kayıtları
        all_attachments = ActionAttachment.query.all()
        print(f"📎 Toplam ActionAttachment: {len(all_attachments)}")
        
        if all_attachments:
            for att in all_attachments:
                print(f"   ID: {att.id}, Action: {att.action_id}, Dosya: {att.filename}")
        
        # Son 10 DOFAction'ı kontrol et
        recent_actions = DOFAction.query.order_by(DOFAction.created_at.desc()).limit(10).all()
        print(f"\n📋 Son 10 DOFAction:")
        
        for action in recent_actions:
            attachments = action.attachments.all()
            print(f"   Action #{action.id} (DÖF #{action.dof_id}) - {len(attachments)} ek")
            if action.new_status == 10:
                print(f"      🎯 TAMAMLANDI! Ek sayısı: {len(attachments)}")
                for att in attachments:
                    print(f"         - {att.filename} ({att.file_size} byte)")
        
        # Tamamlama actionlarını özellikle bul
        completion_actions = DOFAction.query.filter_by(new_status=10).all()
        print(f"\n✅ Tamamlama Action'ları: {len(completion_actions)}")
        
        for action in completion_actions:
            attachments = action.attachments.all()
            print(f"   DÖF #{action.dof_id} - {action.created_at.strftime('%d.%m.%Y %H:%M')} - {len(attachments)} kanıt dosyası")
            for att in attachments:
                print(f"      📁 {att.filename}")

if __name__ == "__main__":
    debug_action_attachments() 