"""
Basit örnek DÖF'ler oluşturan betik
Bu betik temel DÖF örnekleri oluşturur
"""
from app import app, db
from models import DOF, DOFStatus, DOFType, Department, User, UserRole
from datetime import datetime, timedelta
import random

def create_sample_dofs():
    with app.app_context():
        # Departmanları al
        departments = Department.query.all()
        if not departments:
            print("Önce departmanları oluşturun (setup_departments.py)")
            return
        
        # Kullanıcıları al
        users = User.query.all()
        if not users:
            print("Önce kullanıcıları oluşturun (setup_departments.py)")
            return
        
        # DÖF başlıkları ve içerikleri
        dof_titles = [
            "Ürün etiketleme hatası",
            "Tedarikçi kalite sorunu",
            "Müşteri şikayeti",
            "Malzeme uygunsuzluğu",
            "Süreç iyileştirme önerisi"
        ]
        
        dof_descriptions = [
            "Ürün etiketlerinde eksik bilgiler tespit edildi.",
            "Tedarikçiden gelen malzemelerde kalite sorunları mevcut.",
            "Müşteriden gelen şikayet sonucunda inceleme yapılması gerekiyor.",
            "Kullanılan ham madde spesifikasyonlara uygun değil.",
            "Mevcut süreçte iyileştirme yapılması öneriliyor."
        ]
        
        # Farklı durumlarda DÖF'ler oluşturalım
        statuses = [
            DOFStatus.DRAFT,           # Taslak
            DOFStatus.SUBMITTED,       # Gönderildi
            DOFStatus.IN_REVIEW,       # İncelemede
            DOFStatus.ASSIGNED,        # Atanmış
            DOFStatus.IN_PROGRESS,     # Devam Ediyor
            DOFStatus.RESOLVED,        # Çözüldü
            DOFStatus.CLOSED,          # Kapatılmış
            DOFStatus.REJECTED         # Reddedilmiş
        ]
        
        dof_types = [DOFType.CORRECTIVE, DOFType.PREVENTIVE]
        priorities = [1, 2, 3]  # Düşük, Orta, Yüksek
        
        # Her durum için birkaç DÖF oluştur
        for status in statuses:
            for _ in range(3):  # Her durum için 3 örnek
                # Rastgele departman ve kullanıcı seç
                dept = random.choice(departments)
                user = random.choice(users)
                
                # Bugünden rastgele gün sayısı geriye git (oluşturma tarihi için)
                days_ago = random.randint(5, 60)
                created_date = datetime.now() - timedelta(days=days_ago)
                
                # Yeni DÖF oluştur
                new_dof = DOF(
                    title=random.choice(dof_titles),
                    description=random.choice(dof_descriptions),
                    dof_type=random.choice(dof_types),
                    dof_source=random.randint(1, 3),
                    status=status,
                    priority=random.choice(priorities),
                    department_id=dept.id,
                    created_by=user.id,
                    created_at=created_date,
                    updated_at=created_date
                )
                
                # Duruma göre ek alanları doldur
                if status in [DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.RESOLVED, DOFStatus.CLOSED]:
                    # Departman yöneticisine ata
                    dept_manager = User.query.filter_by(department_id=dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
                    if dept_manager:
                        new_dof.assigned_to = dept_manager.id
                    else:
                        # Departman yöneticisi yoksa herhangi bir kullanıcıya ata
                        new_dof.assigned_to = random.choice(users).id
                    
                    # Deadline belirle (gelecekte veya geçmişte)
                    if random.choice([True, False]):  # %50 ihtimalle termin süresi geçmiş olsun
                        new_dof.deadline = datetime.now() - timedelta(days=random.randint(1, 10))
                    else:
                        new_dof.deadline = datetime.now() + timedelta(days=random.randint(5, 30))
                
                if status in [DOFStatus.IN_PROGRESS, DOFStatus.RESOLVED, DOFStatus.CLOSED]:
                    # Kök neden analizleri ekle
                    new_dof.root_cause1 = "Eğitim eksikliği"
                    new_dof.root_cause2 = "Prosedür hatası"
                    new_dof.root_cause3 = "İletişim sorunu"
                    
                    # Aksiyon planı ekle
                    new_dof.action_plan = "1. Personel eğitimi düzenlenecek\n2. Prosedürler güncellenecek\n3. İletişim toplantıları artırılacak"
                
                if status in [DOFStatus.RESOLVED, DOFStatus.CLOSED]:
                    # Tamamlanma tarihi ekle
                    completion_date = datetime.now() - timedelta(days=random.randint(1, 10))
                    new_dof.completion_date = completion_date
                
                if status == DOFStatus.CLOSED:
                    # Kapanış tarihi ekle
                    closed_date = datetime.now() - timedelta(days=random.randint(1, 5))
                    new_dof.closed_at = closed_date
                
                if status == DOFStatus.REJECTED:
                    # Ret nedeni ekle
                    reject_reasons = [
                        "Bu DÖF departmanımızla ilgili değil.",
                        "Açıklanan durum yeterince açık değil.",
                        "Bu sorun daha önce ele alındı.",
                        "Öncelik olarak değerlendirilmiyor."
                    ]
                    new_dof.root_cause1 = random.choice(reject_reasons)
                
                # DÖF'ü kaydet
                db.session.add(new_dof)
                db.session.commit()
                print(f"DÖF oluşturuldu: {new_dof.title} | Durumu: {status}")
        
        print("\nToplam DÖF sayısı:", DOF.query.count())
        print("Her durumda DÖF'ler başarıyla oluşturuldu!")

if __name__ == "__main__":
    print("Örnek DÖF'ler oluşturuluyor...")
    create_sample_dofs()
