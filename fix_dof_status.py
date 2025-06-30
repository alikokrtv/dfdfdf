"""
DÖF Durum Düzeltme Betiği

Bu betik, tamamlanmış ancak SOURCE_REVIEW durumuna geçmemiş DÖF kayıtlarını bulur
ve düzeltir, ayrıca eksik durum geçiş kayıtlarını da ekler.
"""
from app import app, db
from models import DOF, DOFAction, DOFStatus, User, Department
from datetime import datetime
import logging
import sys

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dof_status_fix.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def fix_dof_status():
    """DÖF durumlarını ve eksik akış kayıtlarını düzeltir"""
    with app.app_context():
        # Özel DÖF kaydını bulalım
        dof_19 = DOF.query.filter_by(id=19).first()
        if dof_19:
            logging.info(f"DÖF #19 mevcut. Durumu: {dof_19.status} ")
            logging.info(f"DOFStatus.COMPLETED={DOFStatus.COMPLETED}, DOFStatus.SOURCE_REVIEW={DOFStatus.SOURCE_REVIEW}, "
                         f"DOFStatus.RESOLVED={DOFStatus.RESOLVED}")
        else:
            logging.info("DÖF #19 bulunamadı!")

        # RESOLVED durumunda olan, ancak SOURCE_REVIEW'a geçmemiş DÖF'leri bul
        # Bu DÖF'ler, doğrudan COMPLETED'dan (10) RESOLVED'a (5) geçmiş olanlardır
        resolved_dofs = DOF.query.filter_by(status=DOFStatus.RESOLVED).all()
        logging.info(f"Toplam {len(resolved_dofs)} adet DÖF RESOLVED durumunda bulundu")
        
        # COMPLETED durumunda olan DÖF'leri bul
        completed_dofs = DOF.query.filter_by(status=DOFStatus.COMPLETED).all()
        logging.info(f"Toplam {len(completed_dofs)} adet DÖF COMPLETED durumunda bulundu")
        
        fixed_count = 0
        
        # Önce RESOLVED durumundaki kayıtları düzelt
        for dof in resolved_dofs:
            try:
                logging.info(f"RESOLVED durumundaki DÖF #{dof.id} için işlem yapılıyor...")
                
                # Son action kaydı ve kim tarafından yapıldığını bul
                last_action = DOFAction.query.filter_by(
                    dof_id=dof.id,
                    new_status=DOFStatus.RESOLVED
                ).order_by(DOFAction.created_at.desc()).first()
                
                action_creator_id = None
                if last_action:
                    action_creator_id = last_action.user_id
                else:
                    action_creator_id = dof.updated_by if hasattr(dof, 'updated_by') else None
                
                # SOURCE_REVIEW durumunu set et ve bu geçiş için yeni bir aksiyon kaydı oluştur
                old_status = dof.status
                dof.status = DOFStatus.SOURCE_REVIEW
                db.session.add(DOFAction(
                    dof_id=dof.id,
                    user_id=action_creator_id,
                    action_type=2,  # Status change
                    old_status=old_status,
                    new_status=DOFStatus.SOURCE_REVIEW,
                    notes="DÖF, kaynak departman değerlendirmesine aktarıldı.",
                    created_at=datetime.now()
                ))
                db.session.commit()
                logging.info(f"DÖF #{dof.id}: Status {old_status} → {DOFStatus.SOURCE_REVIEW} olarak güncellendi")
                fixed_count += 1
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"DÖF #{dof.id} güncellenirken hata: {e}")
        
        # Sonra COMPLETED durumundaki kayıtları da düzelt
        for dof in completed_dofs:
            try:
                logging.info(f"COMPLETED durumundaki DÖF #{dof.id} için işlem yapılıyor...")
                
                # Son action kaydı ve kim tarafından yapıldığını bul
                completion_action = DOFAction.query.filter_by(
                    dof_id=dof.id,
                    new_status=DOFStatus.COMPLETED
                ).order_by(DOFAction.created_at.desc()).first()
                
                action_creator_id = None
                if completion_action:
                    action_creator_id = completion_action.user_id
                else:
                    action_creator_id = dof.updated_by if hasattr(dof, 'updated_by') else None
                
                # SOURCE_REVIEW durumunu set et ve bu geçiş için yeni bir aksiyon kaydı oluştur
                old_status = dof.status
                dof.status = DOFStatus.SOURCE_REVIEW
                db.session.add(DOFAction(
                    dof_id=dof.id,
                    user_id=action_creator_id,
                    action_type=2,  # Status change
                    old_status=old_status,
                    new_status=DOFStatus.SOURCE_REVIEW,
                    notes="DÖF, kaynak departman değerlendirmesine gönderildi.",
                    created_at=datetime.now()
                ))
                db.session.commit()
                logging.info(f"DÖF #{dof.id}: Status {old_status} → {DOFStatus.SOURCE_REVIEW} olarak güncellendi")
                fixed_count += 1
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"DÖF #{dof.id} güncellenirken hata: {e}")
        
        if fixed_count > 0:
            db.session.commit()
            logging.info(f"Toplam {fixed_count} adet DÖF durumu düzeltildi ve kayıtları tamamlandı")
        else:
            logging.info("Düzeltilecek DÖF bulunamadı")

if __name__ == "__main__":
    answer = input("Bu betik, COMPLETED durumundaki DÖF'leri düzeltecek. Devam etmek istiyor musunuz? (e/h): ")
    if answer.lower() == 'e':
        fix_dof_status()
        print("İşlem tamamlandı. Detaylar için dof_status_fix.log dosyasını kontrol edin.")
    else:
        print("İşlem iptal edildi.")
