from app import app, db
from models import ActionClass, DOF
from datetime import datetime
from flask_login import current_user

def create_default_action_classes():
    """Varsayılan aksiyon sınıflarını oluşturur"""
    action_classes = [
        {'name': 'Acil', 'description': 'En kısa sürede müdahale gerektiren aksiyonlar'},
        {'name': 'Normal', 'description': 'Standart süreçle ilerleyecek aksiyonlar'},
        {'name': 'Rutin', 'description': 'Düzenli olarak tekrarlanan aksiyonlar'},
        {'name': 'Önleyici', 'description': 'Potansiyel sorunları önlemek için yapılan aksiyonlar'}
    ]
    
    for ac in action_classes:
        # Eğer bu isimde bir aksiyon sınıfı yoksa oluştur
        if not ActionClass.query.filter_by(name=ac['name']).first():
            action_class = ActionClass(
                name=ac['name'],
                description=ac['description'],
                is_active=True
            )
            db.session.add(action_class)
    
    db.session.commit()
    print("Varsayılan aksiyon sınıfları oluşturuldu.")

def update_existing_dofs():
    """Mevcut DÖF kayıtlarını günceller"""
    # Aksiyon planı hazırlama aşamasındaki veya daha ileride olan DÖF'lere Normal aksiyon sınıfı ata
    normal_class = ActionClass.query.filter_by(name='Normal').first()
    
    if normal_class:
        # Aksiyon planı hazırlama aşamasındaki veya daha ileri durumdaki DÖF'leri bul
        planning_dofs = DOF.query.filter(DOF.status >= 8).all()
        
        for dof in planning_dofs:
            dof.action_class_id = normal_class.id
            
            # Eğer atama bilgileri eksikse, bunları da doldur
            if dof.department_id and not dof.assigned_by:
                # Atayan bilgisi yoksa kalite yöneticisi olarak ata 
                # (gerçek veri olmadığı için geçici çözüm)
                from models import User, UserRole
                quality_manager = User.query.filter_by(role=UserRole.QUALITY_MANAGER).first()
                
                if quality_manager:
                    dof.assigned_by = quality_manager.id
                    if not dof.assigned_at:
                        dof.assigned_at = dof.created_at
        
        db.session.commit()
        print(f"{len(planning_dofs)} adet DÖF güncellendi, aksiyon sınıfları ve atama bilgileri eklendi.")
    else:
        print("Aksiyon sınıfı bulunamadı!")

def run_db_updates():
    """Tüm veritabanı güncellemelerini çalıştırır"""
    with app.app_context():
        print("Veritabanı güncellemeleri başlatılıyor...")
        
        # Aksiyon sınıflarını oluştur
        create_default_action_classes()
        
        # Mevcut DÖF'leri güncelle
        update_existing_dofs()
        
        print("Veritabanı güncellemeleri tamamlandı.")

if __name__ == "__main__":
    run_db_updates()
