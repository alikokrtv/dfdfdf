"""DÖF durumunu kontrol etmek için script"""
from app import app, db
from models import DOF, Department, DOFStatus

# DÖF ID'si
DOF_ID = 514

with app.app_context():
    # DÖF'ü sorgula
    dof = DOF.query.get(DOF_ID)
    
    if dof:
        # Departman bilgisini al
        dept_name = "Yok"
        if dof.department_id:
            dept = Department.query.get(dof.department_id)
            if dept:
                dept_name = dept.name
        
        # Durum açıklaması
        status_names = {
            DOFStatus.DRAFT: "Taslak",
            DOFStatus.SUBMITTED: "Gönderildi",
            DOFStatus.IN_REVIEW: "İncelemede",
            DOFStatus.ASSIGNED: "Atandı",
            DOFStatus.IN_PROGRESS: "Devam Ediyor",
            DOFStatus.RESOLVED: "Çözüldü",
            DOFStatus.CLOSED: "Kapatıldı",
            DOFStatus.REJECTED: "Reddedildi",
            DOFStatus.PLANNING: "Aksiyon Planı İncelemede",
            DOFStatus.IMPLEMENTATION: "Aksiyon Planı Uygulama Aşamasında",
            DOFStatus.COMPLETED: "Aksiyonlar Tamamlandı",
            DOFStatus.SOURCE_REVIEW: "Kaynak Değerlendirmesinde"
        }
        
        status_desc = status_names.get(dof.status, f"Bilinmeyen ({dof.status})")
        
        print(f"\nDÖF #{dof.id} Bilgileri:")
        print(f"Başlık: {dof.title}")
        print(f"Durum: {status_desc} (Kod: {dof.status})")
        print(f"Departman: {dept_name} (ID: {dof.department_id})")
        print(f"Oluşturulma: {dof.created_at}")
        print(f"Son Güncelleme: {dof.updated_at}")
    else:
        print(f"DÖF #{DOF_ID} bulunamadı!")
