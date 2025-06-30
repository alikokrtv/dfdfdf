#!/usr/bin/env python3
"""
DÖF istatistiklerini test etmek için script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import DOF, Department, DOFStatus
from daily_email_scheduler import get_dof_statistics
from datetime import datetime, timedelta

def test_dof_statistics():
    """DÖF istatistiklerini test et"""
    
    with app.app_context():
        print("=" * 70)
        print("📊 DÖF İSTATİSTİK TESTİ")
        print("=" * 70)
        
        # Örnek departmanlardan birkaçını test et
        test_departments = [
            {"id": 2, "name": "Müşteri İlişkileri"},
            {"id": 4, "name": "Emaar Şube"}, 
            {"id": 5, "name": "Kanyon Şube"},
            {"id": 11, "name": "Zorlu Şube"}
        ]
        
        for dept_info in test_departments:
            dept_id = dept_info["id"]
            dept_name = dept_info["name"]
            
            print(f"\n🏢 DEPARTMAN: {dept_name} (ID: {dept_id})")
            print("-" * 50)
            
            # Bu departmandaki DÖF'leri kontrol et
            all_dofs = DOF.query.filter_by(department_id=dept_id).all()
            print(f"📊 Toplam DÖF: {len(all_dofs)}")
            
            if all_dofs:
                # Durum dağılımı
                status_counts = {}
                for dof in all_dofs:
                    status_name = DOFStatus.get_label(dof.status)
                    status_counts[status_name] = status_counts.get(status_name, 0) + 1
                
                print("📈 Durum Dağılımı:")
                for status, count in status_counts.items():
                    print(f"   • {status}: {count}")
                
                # Tarih kontrolü
                today = datetime.now()
                week_ago = today - timedelta(days=7)
                
                open_dofs = [dof for dof in all_dofs if dof.status != DOFStatus.CLOSED]
                closed_recent = [dof for dof in all_dofs if dof.status == DOFStatus.CLOSED and dof.closed_at and dof.closed_at >= week_ago]
                
                print(f"🔓 Açık DÖF: {len(open_dofs)}")
                print(f"✅ Son 7 günde kapatılan: {len(closed_recent)}")
                
                # Yaklaşan ve gecikmiş termin tarihleri
                next_week = today + timedelta(days=7)
                upcoming = [dof for dof in open_dofs if dof.deadline and today <= dof.deadline <= next_week]
                overdue = [dof for dof in open_dofs if dof.deadline and dof.deadline < today]
                
                print(f"⏰ Yaklaşan termin (7 gün): {len(upcoming)}")
                print(f"⚠️ Gecikmiş: {len(overdue)}")
            
            # İstatistik fonksiyonunu test et
            print(f"\n🧪 get_dof_statistics([{dept_id}]) sonucu:")
            statistics = get_dof_statistics([dept_id])
            
            if statistics:
                print(f"   📊 total_open: {statistics.get('total_open', 'N/A')}")
                print(f"   ✅ total_closed_week: {statistics.get('total_closed_week', 'N/A')}")
                print(f"   ⏰ total_upcoming: {statistics.get('total_upcoming', 'N/A')}")
                print(f"   ⚠️ total_overdue: {statistics.get('total_overdue', 'N/A')}")
                
                # Toplam DÖF kontrolü
                total_dofs = statistics.get('total_open', 0) + statistics.get('total_closed_week', 0)
                print(f"   🎯 Toplam (açık + kapatılan): {total_dofs}")
                
                if total_dofs == 0:
                    print("   ❌ Bu departman için E-POSTA GÖNDERİLMEYECEK!")
                else:
                    print("   ✅ Bu departman için e-posta gönderilecek")
            else:
                print("   ❌ İstatistik alınamadı!")
        
        print("\n" + "=" * 70)
        print("📋 GENEL DÖF DURUM KONTROLÜ")
        print("=" * 70)
        
        # Tüm DÖF'lerin genel durumu
        all_dofs = DOF.query.all()
        print(f"📊 Toplam DÖF sayısı: {len(all_dofs)}")
        
        # Durum dağılımı
        status_counts = {}
        for dof in all_dofs:
            status_name = DOFStatus.get_label(dof.status)
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        print("📈 Genel Durum Dağılımı:")
        for status, count in sorted(status_counts.items()):
            print(f"   • {status}: {count}")
        
        # Son 7 günde kapatılan DÖF'ler
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        recent_closed = DOF.query.filter(
            DOF.status == DOFStatus.CLOSED,
            DOF.closed_at >= week_ago
        ).all()
        
        print(f"\n✅ Son 7 günde kapatılan DÖF: {len(recent_closed)}")
        
        if recent_closed:
            print("📋 Son kapatılan DÖF'ler:")
            for dof in recent_closed[:5]:  # İlk 5 tanesi
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                print(f"   • DÖF #{dof.id}: {dof.title[:40]}... ({dept_name})")

if __name__ == "__main__":
    test_dof_statistics() 