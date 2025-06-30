#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-posta takip sistemi kontrol scripti
"""

import sys
import os
from datetime import datetime, timedelta

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import EmailTrack, DOF, User, DOFAction, Notification
    from sqlalchemy import desc
    import traceback

    def check_email_tracking():
        print("📧 E-posta Takip Sistemi Kontrolü")
        print("=" * 60)
        
        with app.app_context():
            try:
                # Son 24 saatteki e-posta kayıtlarını kontrol et
                yesterday = datetime.now() - timedelta(hours=24)
                
                recent_emails = EmailTrack.query.filter(
                    EmailTrack.created_at >= yesterday
                ).order_by(desc(EmailTrack.created_at)).all()
                
                if not recent_emails:
                    print("❌ Son 24 saatte e-posta kaydı bulunamadı.")
                    print("\n🔍 Tüm e-posta kayıtlarını kontrol ediyorum...")
                    
                    all_emails = EmailTrack.query.order_by(desc(EmailTrack.created_at)).limit(10).all()
                    if all_emails:
                        print(f"📊 Toplam {len(all_emails)} e-posta kaydı bulundu (son 10 tanesi):")
                        for email in all_emails:
                            print(f"   📧 {email.created_at.strftime('%d.%m.%Y %H:%M')} - {email.subject} - Durum: {email.status}")
                    else:
                        print("❌ Hiç e-posta kaydı bulunamadı. EmailTrack tablosu boş.")
                else:
                    print(f"📊 Son 24 saatte {len(recent_emails)} e-posta kaydı bulundu:")
                    print()
                    
                    for email in recent_emails:
                        status_icon = "✅" if email.status == "sent" else "❌" if email.status == "failed" else "⏳"
                        print(f"{status_icon} {email.created_at.strftime('%d.%m.%Y %H:%M')}")
                        print(f"   📧 Konu: {email.subject}")
                        print(f"   👤 Alıcılar: {email.recipients}")
                        print(f"   📊 Durum: {email.status}")
                        if email.error:
                            print(f"   ❌ Hata: {email.error}")
                        if email.completed_at:
                            print(f"   ⏰ Tamamlandı: {email.completed_at.strftime('%d.%m.%Y %H:%M')}")
                        print()
                
                # Son DOF aksiyonlarını kontrol et
                print("\n" + "=" * 60)
                print("🔄 Son DÖF Aksiyonları (Departman Değişiklikleri)")
                print("=" * 60)
                
                recent_actions = DOFAction.query.filter(
                    DOFAction.created_at >= yesterday,
                    DOFAction.action_type == 2  # Durum değişikliği
                ).order_by(desc(DOFAction.created_at)).all()
                
                if recent_actions:
                    for action in recent_actions:
                        dof = DOF.query.get(action.dof_id)
                        user = User.query.get(action.user_id)
                        print(f"📋 DÖF #{dof.id} - {action.created_at.strftime('%d.%m.%Y %H:%M')}")
                        print(f"   👤 Kullanıcı: {user.full_name}")
                        print(f"   🔄 Durum: {action.old_status} → {action.new_status}")
                        print(f"   💬 Yorum: {action.comment if action.comment else 'Yok'}")
                        if dof.department:
                            print(f"   🏢 Atanan Departman: {dof.department.name}")
                        print()
                else:
                    print("❌ Son 24 saatte DOF aksiyonu bulunamadı.")
                
                # Son bildirimleri kontrol et
                print("\n" + "=" * 60)
                print("🔔 Son Bildirimler")
                print("=" * 60)
                
                recent_notifications = Notification.query.filter(
                    Notification.created_at >= yesterday
                ).order_by(desc(Notification.created_at)).all()
                
                if recent_notifications:
                    for notif in recent_notifications:
                        user = User.query.get(notif.user_id)
                        read_status = "✅ Okundu" if notif.is_read else "📩 Okunmadı"
                        print(f"🔔 {notif.created_at.strftime('%d.%m.%Y %H:%M')} - {read_status}")
                        print(f"   👤 Alıcı: {user.full_name}")
                        print(f"   📧 Mesaj: {notif.message}")
                        if notif.dof_id:
                            print(f"   📋 DÖF: #{notif.dof_id}")
                        print()
                else:
                    print("❌ Son 24 saatte bildirim bulunamadı.")
                    
            except Exception as e:
                print(f"❌ Hata: {str(e)}")
                print("\n🔍 Detaylı hata bilgisi:")
                print(traceback.format_exc())

    if __name__ == "__main__":
        check_email_tracking()
        
except ImportError as e:
    print(f"❌ Import hatası: {str(e)}")
except Exception as e:
    print(f"❌ Genel hata: {str(e)}")
    import traceback
    print(traceback.format_exc()) 