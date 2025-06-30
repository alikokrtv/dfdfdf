"""
Örnek DÖF'ler oluşturan betik
Farklı durumlarda örnek DÖF'ler ekler:
- Taslak (henüz incelenmemiş)
- İncelemede (kalite tarafından incelenen)
- Yanıtlanmış (departman tarafından yanıtlanan)
- Departman tarafından reddedilen
- Kalite tarafından reddedilen
- Termin süresi geçmiş
- Aksiyonları tamamlanmış
- Kapatılmış
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
        
        # Kalite yöneticisi
        quality_manager = User.query.filter_by(role=UserRole.QUALITY_MANAGER).first()
        if not quality_manager:
            print("Kalite yöneticisi bulunamadı")
            return
            
        # Departman yöneticileri
        dept_managers = User.query.filter_by(role=UserRole.DEPARTMENT_MANAGER).all()
        if not dept_managers:
            print("Departman yöneticisi bulunamadı")
            return
            
        # Normal kullanıcılar
        normal_users = User.query.filter_by(role=UserRole.USER).all()
        if not normal_users:
            # Kullanıcı yoksa herhangi birini al
            normal_users = users[:2] if len(users) > 1 else [users[0]]
        
        # DÖF başlıkları ve içerikleri
        dof_titles = [
            "Ürün etiketleme hatası",
            "Tedarikçi kalite sorunu",
            "Müşteri şikayeti",
            "Malzeme uygunsuzluğu",
            "Süreç iyileştirme önerisi",
            "Dokümantasyon eksikliği",
            "Kalibrasyon hatası",
            "Eğitim ihtiyacı",
            "Bakım gerektiren ekipman",
            "İletişim sorunu",
            "Gecikmiş teslimat",
            "Depolama hatası",
            "Güvenlik uyarısı",
            "Çevre etkisi tespiti",
            "Yazılım hatası"
        ]
        
        dof_descriptions = [
            "Ürün etiketlerinde eksik bilgiler tespit edildi.",
            "Tedarikçiden gelen malzemelerde kalite sorunları mevcut.",
            "Müşteriden gelen şikayet sonucunda inceleme yapılması gerekiyor.",
            "Kullanılan ham madde spesifikasyonlara uygun değil.",
            "Mevcut süreçte iyileştirme yapılması öneriliyor.",
            "Süreç dokümanları eksik veya güncel değil.",
            "Ölçüm cihazlarında kalibrasyon sorunları tespit edildi.",
            "Personelin eğitim ihtiyacı bulunduğu tespit edildi.",
            "Ekipmanların bakımında eksiklikler tespit edildi.",
            "Departmanlar arası iletişim sorunu yaşanıyor.",
            "Mal ve hizmet tesliminde gecikmeler yaşanıyor.",
            "Depo alanında ürünlerin yanlış istiflenmesi sorunu var.",
            "Çalışma alanında güvenlik riski tespit edildi.",
            "Üretim sürecinin çevresel etkileri değerlendirilmeli.",
            "Yazılım sisteminde hata tespit edildi."
        ]
        
        root_causes = [
            "Eğitim eksikliği",
            "Doküman eksikliği",
            "Prosedür hatası",
            "İletişim eksikliği",
            "Yetersiz kontrol",
            "Teknik arıza",
            "İnsan hatası",
            "Planlama hatası",
            "Tedarikçi kaynaklı",
            "Ekipman yetersizliği"
        ]
        
        actions = [
            "Personel eğitimi düzenlenecek",
            "Dokümanlar güncellenecek",
            "Prosedür revize edilecek",
            "İletişim toplantıları yapılacak",
            "Kontrol noktaları artırılacak",
            "Teknik bakım yapılacak",
            "Denetim sıklığı artırılacak",
            "Planlama süreci revize edilecek",
            "Tedarikçi değiştirilecek",
            "Yeni ekipman alınacak"
        ]
        
        # Farklı döf tipleri oluştur
        dof_count = 0
        
        # 1. Taslak DÖF
        dof_count += 1
        print(f"{dof_count}. Taslak DÖF oluşturuluyor...")
        
        draft_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.DRAFT,
            department_id=random.choice(departments).id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1)
        )
        db.session.add(draft_dof)
        db.session.commit()
        
        # 2. İncelemede olan DÖF
        dof_count += 1
        print(f"{dof_count}. İncelemede olan DÖF oluşturuluyor...")
        
        review_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.IN_REVIEW,
            department_id=random.choice(departments).id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=5),
            updated_at=datetime.now() - timedelta(days=3)
        )
        db.session.add(review_dof)
        db.session.commit()
        
        # 3. Departmana atanmış DÖF (Kalite onaylanmış)
        dof_count += 1
        print(f"{dof_count}. Departmana atanmış DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        assigned_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.ASSIGNED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=10),
            updated_at=datetime.now() - timedelta(days=8),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=8),
            deadline=datetime.now() + timedelta(days=30)
        )
        db.session.add(assigned_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=assigned_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=8),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # 4. Yanıtlanmış DÖF (Kök neden ve aksiyon planı girilmiş)
        dof_count += 1
        print(f"{dof_count}. Yanıtlanmış DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        responded_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.RESPONDED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=15),
            updated_at=datetime.now() - timedelta(days=10),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=13),
            deadline=datetime.now() + timedelta(days=15),
            root_cause=random.choice(root_causes)
        )
        db.session.add(responded_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=responded_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=13),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # Aksiyon ekle
        action = DOFAction(
            dof_id=responded_dof.id,
            description=random.choice(actions),
            responsible_id=target_manager.id,
            deadline=datetime.now() + timedelta(days=15),
            created_at=datetime.now() - timedelta(days=10)
        )
        db.session.add(action)
        db.session.commit()
        
        # 5. Termin süresi geçmiş DÖF
        dof_count += 1
        print(f"{dof_count}. Termin süresi geçmiş DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        overdue_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.ASSIGNED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=45),
            updated_at=datetime.now() - timedelta(days=40),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=40),
            deadline=datetime.now() - timedelta(days=5)
        )
        db.session.add(overdue_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=overdue_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=40),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # 6. Tamamlanmış DÖF
        dof_count += 1
        print(f"{dof_count}. Tamamlanmış DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        completed_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.COMPLETED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=5),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=28),
            deadline=datetime.now() - timedelta(days=10),
            root_cause=random.choice(root_causes),
            completed_at=datetime.now() - timedelta(days=5)
        )
        db.session.add(completed_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=completed_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=28),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # Aksiyon ekle
        action = DOFAction(
            dof_id=completed_dof.id,
            description=random.choice(actions),
            responsible_id=target_manager.id,
            deadline=datetime.now() - timedelta(days=10),
            created_at=datetime.now() - timedelta(days=25),
            completed_at=datetime.now() - timedelta(days=5),
            status="COMPLETED"
        )
        db.session.add(action)
        db.session.commit()
        
        # 7. Kapatılmış DÖF
        dof_count += 1
        print(f"{dof_count}. Kapatılmış DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        closed_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.CLOSED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=60),
            updated_at=datetime.now() - timedelta(days=30),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=58),
            deadline=datetime.now() - timedelta(days=30),
            root_cause=random.choice(root_causes),
            completed_at=datetime.now() - timedelta(days=35),
            closed_at=datetime.now() - timedelta(days=30)
        )
        db.session.add(closed_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=closed_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=58),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # Aksiyon ekle
        action = DOFAction(
            dof_id=closed_dof.id,
            description=random.choice(actions),
            responsible_id=target_manager.id,
            deadline=datetime.now() - timedelta(days=40),
            created_at=datetime.now() - timedelta(days=55),
            completed_at=datetime.now() - timedelta(days=35),
            status="COMPLETED"
        )
        db.session.add(action)
        db.session.commit()
        
        # Kapanış değerlendirmesi
        closure = DOFClosure(
            dof_id=closed_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=30),
            is_approved=True,
            comment="Aksiyonlar başarıyla uygulanmış, sorun çözülmüştür."
        )
        db.session.add(closure)
        db.session.commit()
        
        # 8. Departman tarafından reddedilen DÖF
        dof_count += 1
        print(f"{dof_count}. Departman tarafından reddedilen DÖF oluşturuluyor...")
        
        target_dept = random.choice(departments)
        target_manager = User.query.filter_by(department_id=target_dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        if not target_manager:
            target_manager = random.choice(dept_managers)
        
        dept_rejected_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.REJECTED,
            department_id=target_dept.id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=20),
            updated_at=datetime.now() - timedelta(days=18),
            assigned_to=target_manager.id,
            assigned_at=datetime.now() - timedelta(days=19),
            rejected_at=datetime.now() - timedelta(days=18),
            reject_reason="Bu DÖF departmanımızla ilgili değil. Farklı departmana yönlendirilmeli."
        )
        db.session.add(dept_rejected_dof)
        db.session.commit()
        
        # Kalite onayını ekle
        quality_review = DOFReview(
            dof_id=dept_rejected_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=19),
            is_approved=True,
            comment="DÖF incelendi ve onaylandı."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        # 9. Kalite tarafından reddedilen DÖF
        dof_count += 1
        print(f"{dof_count}. Kalite tarafından reddedilen DÖF oluşturuluyor...")
        
        quality_rejected_dof = DOF(
            title=random.choice(dof_titles),
            description=random.choice(dof_descriptions),
            type=random.choice([DOFType.CORRECTIVE, DOFType.PREVENTIVE]),
            severity=random.choice([DOFSeverity.LOW, DOFSeverity.MEDIUM, DOFSeverity.HIGH, DOFSeverity.CRITICAL]),
            status=DOFStatus.REJECTED,
            department_id=random.choice(departments).id,
            created_by=random.choice(normal_users).id,
            created_at=datetime.now() - timedelta(days=7),
            updated_at=datetime.now() - timedelta(days=6),
            rejected_at=datetime.now() - timedelta(days=6),
            reject_reason="Bu DÖF kapsamında bildirilen sorun yeterince açık değil. Daha detaylı açıklama gerekli."
        )
        db.session.add(quality_rejected_dof)
        db.session.commit()
        
        # Kalite ret değerlendirmesi
        quality_review = DOFReview(
            dof_id=quality_rejected_dof.id,
            reviewer_id=quality_manager.id,
            review_date=datetime.now() - timedelta(days=6),
            is_approved=False,
            comment="Açıklanan durum yeterince açık değil, daha fazla bilgi gerekli."
        )
        db.session.add(quality_review)
        db.session.commit()
        
        print(f"\nToplam {dof_count} adet örnek DÖF oluşturuldu!")
        print("Farklı durumlardaki DÖF'leri test etmek için sisteme giriş yapabilirsiniz.")

if __name__ == "__main__":
    print("Örnek DÖF'ler oluşturuluyor...")
    create_sample_dofs()
