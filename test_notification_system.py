"""
Yeni Merkezi Bildirim Sistemini Test Etmek İçin Script
"""
from flask import Flask
from app import app, db  # create_app yerine doğrudan app nesnesi import edildi
from models import User, DOF, Department, UserRole
import time
import sys
from flask import current_app
import logging

def setup_logging():
    """Basit loglama kurulumu"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('test_notifications')

def test_notifications():
    """Bildirim sistemini test eder"""
    logger = setup_logging()
    
    # Uygulama bağlamı içinde çalıştır
    # Not: app doğrudan import edildiği için create_app'e gerek yok
    with app.app_context():
        try:
            logger.info("Bildirim sistemi testi başlıyor...")
            
            # Test için DÖF seçimi
            print("\nMevcut DÖF'ler:")
            dofs = DOF.query.order_by(DOF.id.desc()).limit(5).all()
            
            if not dofs:
                logger.error("Test için DÖF bulunamadı!")
                return
            
            for i, dof in enumerate(dofs):
                print(f"{i+1}. DÖF #{dof.id}: {dof.title}")
            
            try:
                selection = int(input("\nTest için DÖF numarasını seçin (1-5): "))
                if selection < 1 or selection > len(dofs):
                    logger.error("Geçersiz seçim!")
                    return
                
                selected_dof = dofs[selection-1]
                logger.info(f"Seçilen DÖF: #{selected_dof.id} - {selected_dof.title}")
                
                # Test menüsü
                print("\nTest işlemi seçin:")
                print("1. DÖF Oluşturma Bildirimi")
                print("2. Departman Atama Bildirimi")
                print("3. DÖF Güncelleme Bildirimi")
                
                test_type = int(input("\nTest tipini seçin (1-3): "))
                
                # İlgili bildirim işlemini çağır
                from notification_system import notify_for_dof_event, notify_department_assignment
                
                if test_type == 1:
                    # DÖF oluşturma bildirimi
                    logger.info(f"DÖF #{selected_dof.id} için 'oluşturma' bildirimi gönderiliyor...")
                    notification_count = notify_for_dof_event(selected_dof.id, "create", None)
                    logger.info(f"Toplam {notification_count} bildirim gönderildi")
                
                elif test_type == 2:
                    # Departman atama bildirimi
                    # Önce tüm departmanları göster
                    departments = Department.query.filter_by(is_active=True).all()
                    
                    print("\nDepartmanlar:")
                    for i, dept in enumerate(departments):
                        print(f"{i+1}. {dept.name}")
                    
                    dept_selection = int(input("\nAtanacak departmanı seçin (1-{}): ".format(len(departments))))
                    if dept_selection < 1 or dept_selection > len(departments):
                        logger.error("Geçersiz departman seçimi!")
                        return
                    
                    selected_dept = departments[dept_selection-1]
                    logger.info(f"Seçilen departman: {selected_dept.name}")
                    
                    # Departman atama bildirimini gönder
                    logger.info(f"DÖF #{selected_dof.id} için '{selected_dept.name}' departmanına atama bildirimi gönderiliyor...")
                    notification_count = notify_department_assignment(selected_dof.id, selected_dept.id, None)
                    logger.info(f"Toplam {notification_count} bildirim gönderildi")
                
                elif test_type == 3:
                    # DÖF güncelleme bildirimi  
                    logger.info(f"DÖF #{selected_dof.id} için 'güncelleme' bildirimi gönderiliyor...")
                    notification_count = notify_for_dof_event(selected_dof.id, "update", None)
                    logger.info(f"Toplam {notification_count} bildirim gönderildi")
                
                else:
                    logger.error("Geçersiz test tipi!")
                    return
                
                logger.info("Test başarıyla tamamlandı!")
                
            except ValueError:
                logger.error("Lütfen geçerli bir sayı girin!")
                return
            
        except Exception as e:
            logger.error(f"Test sırasında hata oluştu: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_notifications()
