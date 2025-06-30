#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hızlı Test DÖF'i Oluşturma Scripti
"""

from datetime import datetime, timedelta
from app import app, db
from models import DOF, User, Department, DOFStatus, DOFType, DOFSource

def create_test_dof(target_department_name=None):
    """Test için hızlı DÖF oluşturur - tamamlanma testi için"""
    
    with app.app_context():
        try:
            # Hedef departmanı belirle
            if target_department_name:
                department = Department.query.filter_by(name=target_department_name, is_active=True).first()
                if not department:
                    # Kısmi eşleşme ile dene
                    department = Department.query.filter(
                        Department.name.ilike(f'%{target_department_name}%'),
                        Department.is_active == True
                    ).first()
            else:
                # Varsayılan: Bilgi İşlem departmanını bul
                department = Department.query.filter_by(name='Bilgi İşlem', is_active=True).first()
                if not department:
                    # Alternatif isimlerle dene
                    department = Department.query.filter(
                        Department.name.ilike('%bilgi%'),
                        Department.is_active == True
                    ).first()
                
            if not department:
                search_name = target_department_name or 'Bilgi İşlem'
                print(f"❌ '{search_name}' departmanı bulunamadı!")
                print("📋 Mevcut aktif departmanlar:")
                all_departments = Department.query.filter_by(is_active=True).all()
                for dept in all_departments:
                    print(f"   - {dept.name}")
                return None
            
            # İlk aktif kullanıcıyı bul (oluşturan olarak)
            user = User.query.filter_by(active=True).first()
            if not user:
                print("❌ Aktif kullanıcı bulunamadı!")
                return None
            
            # Test DÖF'i oluştur
            test_dof = DOF(
                title="TEST DÖF - Tamamlama Testi",
                description="Bu DÖF tamamlama özelliğini test etmek için oluşturulmuştur. Test sonrası silinecektir.",
                dof_type=DOFType.CORRECTIVE,
                dof_source=DOFSource.INTERNAL_AUDIT,
                status=DOFStatus.IMPLEMENTATION,  # Doğrudan uygulama aşamasında başlat
                department_id=department.id,
                created_by=user.id,
                created_at=datetime.now(),
                due_date=datetime.now() + timedelta(days=7),
                # Test için gerekli alanları doldur
                root_cause1="Test kök neden analizi",
                action_plan="Test aksiyon planı - Bu planın tamamlanma testi yapılacak",
                deadline=datetime.now() + timedelta(days=5)
            )
            
            db.session.add(test_dof)
            db.session.commit()
            
            print(f"✅ Test DÖF'i oluşturuldu!")
            print(f"   🆔 DÖF ID: {test_dof.id}")
            print(f"   📋 Başlık: {test_dof.title}")
            print(f"   👤 Oluşturan: {user.full_name}")
            print(f"   🏢 Departman: {department.name}")
            print(f"   📊 Durum: {test_dof.status_name}")
            print(f"\n🎯 Bu DÖF'te 'Tamamlandı' butonunu test edebilirsiniz.")
            print(f"💡 Test tamamlandıktan sonra şu komutla silebilirsiniz:")
            print(f"   python delete_single_dof.py {test_dof.id}")
            
            return test_dof.id
            
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
            db.session.rollback()
            return None

def main():
    import sys
    
    print("🚀 Hızlı Test DÖF'i Oluşturma")
    print("=" * 50)
    
    # Departman adı parametre olarak verilebilir
    target_department = None
    if len(sys.argv) > 1:
        target_department = sys.argv[1]
        print(f"🎯 Hedef departman: {target_department}")
    else:
        print("🎯 Hedef departman: Bilgi İşlem (varsayılan)")
        print("💡 Farklı departman için: python create_test_dof_quick.py 'Departman Adı'")
    
    dof_id = create_test_dof(target_department)
    
    if dof_id:
        print(f"\n✅ Test DÖF'i başarıyla oluşturuldu (ID: {dof_id})")
        print("🔗 Sistemde bu DÖF'e giderek 'Tamamlandı' özelliğini test edebilirsiniz.")
        print(f"🗑️  Test sonrası silmek için: python delete_single_dof.py {dof_id}")
    else:
        print("\n❌ Test DÖF'i oluşturulamadı.")

if __name__ == "__main__":
    main() 