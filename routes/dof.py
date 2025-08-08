from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify, session, send_file, make_response
from flask_login import login_required, current_user
from models import DOF, DOFAction, Department, Attachment, ActionAttachment, User, Notification, UserRole, DOFStatus, DOFType, DOFSource, UserActivity, DepartmentGroup
from forms import DOFForm, DOFActionForm, DOFResolveForm, QualityReviewForm, QualityClosureForm, SearchForm
# app import'u blueprint tanımından sonra yapılacak
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os, uuid
from sqlalchemy import or_, and_, func, desc
import json
from export_utils import export_dofs_to_excel, export_dofs_to_pdf
from utils import allowed_file, save_file, log_activity, notify_for_dof, get_dof_status_counts, can_user_edit_dof, can_user_change_status, send_email_async, optimize_db_operations
from generate_dof_code import generate_dof_code
import os
import time

# Güzel DÖF e-posta bildirimi fonksiyonu
def send_beautiful_dof_email(dof, dof_id, dof_title, dof_description, creator_name):
    """
    Tek bir güzel e-posta gönderir - modern tasarımlı ve yeşil butonlu
    Bu fonksiyon, DÖF bildirimleri için güzel tasarımlı e-posta gönderir
    """
    current_app.logger.info(f"Güzel DÖF e-posta bildirimi gönderiliyor: DÖF #{dof_id}")
    
    try:
        # Kalite yöneticilerini ve departman yöneticisini bul
        from models import User, UserRole, Department
        from utils import send_email
        
        # Alıcıları topla
        recipients = []
        
        # DÖF oluşturan kişi
        if dof.created_by:
            creator = User.query.get(dof.created_by)
            if creator and creator.email:
                recipients.append(creator.email)
                current_app.logger.info(f"DÖF oluşturan kişinin e-postası eklendi: {creator.email}")
        else:
            current_app.logger.warning(f"DÖF #{dof_id} için oluşturan kullanıcı bilgisi bulunamadı")
        
        # Kalite yöneticileri
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        if quality_managers:
            qm_emails = [qm.email for qm in quality_managers if qm and qm.email]
            recipients.extend(qm_emails)
            current_app.logger.info(f"{len(qm_emails)} kalite yöneticisi e-postası eklendi")
        
        # Departman yöneticisi
        if dof.department_id:
            dept = Department.query.get(dof.department_id)
            if dept and dept.manager_id:
                dept_manager = User.query.get(dept.manager_id)
                if dept_manager and dept_manager.email:
                    recipients.append(dept_manager.email)
                    current_app.logger.info(f"Departman yöneticisi e-postası eklendi: {dept_manager.email}")
        
        # Tekrarı önle
        recipients = list(set(recipients))
        if not recipients:
            current_app.logger.warning("Gönderilecek e-posta adresi bulunamadı")
            return False
        
        # DÖF URL'si oluştur - şu anda LOCAL ortam için
        try:
            # request zaten en üstte import edildi
            host = request.host_url
            if not host.endswith('/'):
                host += '/'
            
            # Local ortam için URL oluştur
            dof_url = f"{host}dof/{dof_id}"
            current_app.logger.info(f"Oluşturulan DÖF URL'si: {dof_url}")
        except Exception as e:
            current_app.logger.error(f"URL oluşturma hatası: {str(e)}")
            # Fallback - varsayılan localhost URL'si
            dof_url = f"http://localhost:5000/dof/{dof_id}"
        
        # Güzel e-posta içeriği
        subject = f"DÖF Sistemi - Yeni DÖF: {dof_title}"
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                .footer {{ background-color: #f8f8f8; padding: 10px; border-top: 1px solid #ddd; margin-top: 20px; font-size: 12px; color: #777; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Yeni DÖF Bildirim</h2>
                </div>
                
                <p>Sayın Yetkili,</p>
                
                <p>{creator_name} tarafından <strong>"{dof_title}"</strong> başlıklı yeni bir DÖF oluşturuldu.</p>
                <p><b>Açıklama:</b> {dof_description[:200]}...</p>
                
                <p>
                    <a href="{dof_url}" class="button">DÖF Detaylarını Görüntüle</a>
                </p>
                
                <p>Tarih/Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"Yeni DÖF Bildirim\n\n{creator_name} tarafından \"{dof_title}\" başlıklı yeni bir DÖF oluşturuldu.\n\nAçıklama: {dof_description[:200]}...\n\nDÖF detaylarını görüntülemek için: {dof_url}\n\nBu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız."
        
        # Her alıcı için doğrudan e-posta gönder
        for recipient in recipients:
            try:
                current_app.logger.info(f"Güzel DÖF e-postası gönderiliyor: {recipient}")
                result = send_email(subject, [recipient], html_content, text_content)
                current_app.logger.info(f"Güzel DÖF e-postası gönderim sonucu: {result}")
            except Exception as e:
                current_app.logger.error(f"Alıcıya e-posta gönderim hatası: {recipient}, Hata: {str(e)}")
        
        return True
    except Exception as e:
        current_app.logger.error(f"Güzel DÖF e-posta gönderim hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False

# DÖF oluşturma işlemi tamamlandıktan sonra doğrudan kalite yöneticilerine bildirim gönder
def send_direct_notifications_to_quality_managers(dof_id, creator_name, dof_title):
    current_app.logger.info(f"Doğrudan bildirim sistemi çalışıyor (DÖF #{dof_id})")
    try:
        # DÖF kontrolü
        dof = DOF.query.get(dof_id)
        if not dof:
            current_app.logger.error(f"DÖF bulunamadı: {dof_id}")
            return False
            
        # Kalite yöneticilerini bul - UserRole.QUALITY_MANAGER kullanarak
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        current_app.logger.info(f"{len(quality_managers)} kalite yöneticisi bulundu")
        
        # Her kalite yöneticisine bildirim gönder
        notification_count = 0
        for qm in quality_managers:
            try:
                # Bildirim oluştur
                notification = Notification(
                    user_id=qm.id,
                    dof_id=dof_id,
                    message=f"{creator_name} tarafından '{dof_title}' (#{dof_id}) başlıklı yeni bir DÖF oluşturuldu.",
                    created_at=datetime.now(),
                    is_read=False
                )
                db.session.add(notification)
                current_app.logger.info(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
                notification_count += 1
            except Exception as e:
                current_app.logger.error(f"Bildirim oluşturma hatası ({qm.username}): {str(e)}")
        
        # Veritabanına kaydet
        if notification_count > 0:
            db.session.commit()
            current_app.logger.info(f"Toplam {notification_count} bildirim veritabanına kaydedildi")
            return True
        
        return False
    except Exception as e:
        current_app.logger.error(f"Bildirim sistemi genel hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False

dof_bp = Blueprint('dof', __name__)

# app ve db'yi blueprint tanımından sonra import et
from app import db

@dof_bp.route('/dof/<int:dof_id>/review', methods=['GET', 'POST'])
@login_required
def review_dof(dof_id):
    """
    DÖF'nin kalite yöneticisi tarafından değerlendirilmesi
    """
    # DÖF'yi getir
    dof = DOF.query.get_or_404(dof_id)
    
    # Yetki kontrolü: Sadece kalite yöneticileri ve adminler erişebilir
    if current_user.role not in [UserRole.QUALITY_MANAGER, UserRole.ADMIN]:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Değerlendirilebilecek DÖF durumlarını kontrol et
    if dof.status not in [DOFStatus.DRAFT, DOFStatus.SUBMITTED, DOFStatus.IN_REVIEW, DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.RESOLVED]:
        flash('Sadece TASLAK, GÖNDERİLDİ, İNCELEMEDE, ATANMIŞ, DEVAM EDİYOR, PLANLAMA veya ÇÖZÜLDÜ durumundaki DÖFler değerlendirilebilir.', 'warning')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Form hazırlığı
    form = QualityReviewForm()
    
    # Tüm aktif departmanları al
    all_departments = Department.query.filter_by(is_active=True).all()
    
    # DÖF durumuna göre departman seçeneklerini belirle
    is_department_change = dof.status in [DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS]
    
    # Tüm departmanları listeye ekle
    if is_department_change:
        # Departman değişikliği için TÜM departmanları göster
        form.department.choices = [(dept.id, dept.name) for dept in all_departments]
        current_app.logger.info(f"Departman değişikliği için tüm departmanlar listeleniyor: {form.department.choices}")
    else:
        # Normal inceleme için - kendi departmanı hariç tüm departmanlar
        source_dept_id = dof.creator.department_id if dof.creator and dof.creator.department_id else None
        form.department.choices = [(dept.id, dept.name) for dept in all_departments if dept.id != source_dept_id]
        current_app.logger.info(f"Normal inceleme için departmanlar (kendi departmanı hariç) listeleniyor: {form.department.choices}")
        
    # Seçili departman bilgisini logla
    current_app.logger.info(f"Mevcut DÖF departman ID: {dof.department_id}")
    
    # Buradaki departman önemli
    
    # Eğer DÖF'e atanmış bir departman varsa, o departmanı seçili getir
    if dof.department_id:
        form.department.data = dof.department_id
    
    # Form gönderildiğinde
    if request.method == 'POST':
        current_app.logger.info(f"DÖF inceleme formu gönderildi: {request.form}")
        
        # Form işleme - gerekli kontroller
        if 'submit_action' not in request.form:
            flash("Lütfen bir işlem seçin (Onayla ve Ata, Reddet veya Yeni DÖF Açılsın).", "danger")
            return render_template('dof/quality_review.html', form=form, dof=dof)
        
        # JavaScript validation geçemezse bile server-side doğrulamaları yap
        submit_action = request.form.get('submit_action', None)
        
        # Sadece departman değişikliği yapılıyorsa, kontrol kutucukları ve diğer form alanları gerekli değil
        is_department_change_only = dof.status in [DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS]
        
        # "Yeni DÖF açılsın" seçildiyse veya sadece departman değişikliği yapılıyorsa kontrol kutucukları gerekli değil
        if submit_action == 'new_dof' or is_department_change_only:
            # Bu durumda kutucukları kontrol etmeden devam et
            pass
        else:
            # Diğer seçenekler için gerekli checkbox'ların doldurulduğunu kontrol et
            required_checks = ['check_fields', 'check_department', 'check_type']
            missing_checks = [check for check in required_checks if check not in request.form]
            
            # Eğer eksik checkbox varsa, hata ver
            if missing_checks:
                flash("Lütfen tüm kontrol listesini doldurunuz.", "danger")
                return render_template('dof/quality_review.html', form=form, dof=dof)
        
        # Form doğrulaması (WTForms)
        if form.validate():
            # İşlem başlamadan önce kullanıcıya geri bildirim
            flash("İşlem yapılıyor...", "info")
            
            # Veritabanı işlemi
            try:
                # İşlem için değişkenler
                old_status = dof.status
                submit_action = request.form.get('submit_action', None)
                action_message = ""
                new_status = None
                success_message = ""
                log_action = ""
                log_details = ""
                
                # Departman kontrolü - sadece departman gerektiren işlemler için
                # "Gereksiz Kapat" seçeneğinde departman gerekli değil
                if submit_action != 'close_unnecessary':
                    department = Department.query.get(form.department.data)
                    if not department:
                        flash("Seçilen departman bulunamadı!", "danger")
                        return render_template('dof/quality_review.html', form=form, dof=dof)
                else:
                    # Gereksiz kapat için departman gerekli değil
                    department = None
                
                # Sadece departman değişikliği mi yapılıyor kontrol et
                is_department_change_only = dof.status in [DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS]
                
                # İşlem türüne göre işlem yap
                if submit_action == 'change_department':
                    # Sadece departman değişikliği yap - tüm eski kodları kaldırdık ve yeniden yazdık
                    
                    # Seçilen departmanı doğrudan veritabanından al
                    selected_dept_id = int(form.department.data)
                    selected_department = Department.query.get(selected_dept_id)
                    
                    if not selected_department:
                        flash(f"Seçilen departman (ID: {selected_dept_id}) bulunamadı!", "danger")
                        return render_template('dof/quality_review.html', form=form, dof=dof)
                    
                    # Eski departman bilgilerini kaydet
                    old_department_id = dof.department_id if dof.department_id else None
                    old_department = Department.query.get(old_department_id) if old_department_id else None
                    old_department_name = old_department.name if old_department else "Belirtilmemiş"
                    
                    # Detaylı log bilgileri
                    current_app.logger.info(f"SEÇİLEN YENİ DEPARTMAN: {selected_department.name} (ID: {selected_dept_id})")
                    current_app.logger.info(f"ESKİ DEPARTMAN: {old_department_name} (ID: {old_department_id})")
                    
                    # KRİTİK DEBUG: Tüm değişkenleri yazdır
                    current_app.logger.info(f"FORM'DAN GELEN DEPARTMAN ID: {form.department.data}, Tip: {type(form.department.data)}")
                    current_app.logger.info(f"DÖF DEPARTMAN ID: {dof.department_id}, Tip: {type(dof.department_id)}")
                    current_app.logger.info(f"SEÇİLEN DEPARTMAN ID: {selected_dept_id}, Tip: {type(selected_dept_id)}")
                    current_app.logger.info(f"ESKİ DEPARTMAN ID: {old_department_id}, Tip: {type(old_department_id)}")
                    
                    # KARŞILAŞTIRMAYI YAPMADAN ÖNCE BU ADIMDA DEPARTMANI DEĞİŞTİRELİM
                    # Departmanı doğrudan güncelle
                    dof.department_id = selected_dept_id
                    
                    # Sadece log amaçlı karşılaştırma (artık bloklama yok)
                    if old_department_id == selected_dept_id:
                        current_app.logger.warning(f"DİKKAT: Seçilen departman mevcut departmanla aynı ({old_department_name}), ama işleme devam ediliyor")
                    
                    # Her durumda devam et, artık aynı departman olsa bile uyarı verip durdurma yok
                    # Bu şekilde sistem her zaman değişiklik yapacak
                    
                    # Kayıt işlemini yap
                    try:
                        # Veritabanı durumunu kontrol et
                        if not db.session.is_active:
                            current_app.logger.warning("DB oturumu aktif değil, yeni oturum açılıyor")
                            db.session.begin()
                        
                        # Departman değişikliğini doğrula - flush ile veritabanına gönder ama commit etme
                        db.session.flush()
                        
                        # Kayıt doğrulama - departman ID'si beklenen değerle eşleşiyor mu?
                        if dof.department_id != selected_dept_id:
                            current_app.logger.error(f"HATALI ATAMA: Departman {selected_dept_id} olarak ayarlanamadı, hala {dof.department_id}")
                            flash("Departman değişikliği sırasında teknik bir hata oluştu.", "danger")
                            return render_template('dof/quality_review.html', form=form, dof=dof)
                        
                        # Başarılı değişiklik kaydı
                        current_app.logger.info(f"BAŞARILI GÜNCELLEME: {old_department_name} -> {selected_department.name}")
                        current_app.logger.info(f"SONUÇ DEPARTMAN ID: {dof.department_id}")
                    except Exception as e:
                        current_app.logger.error(f"KRİTİK HATA - Departman güncellemesi: {str(e)}")
                        flash(f"Departman güncellemesi sırasında hata: {str(e)}", "danger")
                        db.session.rollback()
                        return render_template('dof/quality_review.html', form=form, dof=dof)
                    
                    # Yorum varsa ekle
                    if form.comment.data:
                        action_message = f"Departman değiştirildi: {old_department_name} -> {selected_department.name}. {form.comment.data}"
                    else:
                        action_message = f"Departman değiştirildi: {old_department_name} -> {selected_department.name}"
                    
                    # Aksiyon kaydı ve log detayları
                    new_status = dof.status  # Durumu değiştirme
                    success_message = f"DÖF'e atanan departman {selected_department.name} olarak güncellendi."
                    log_action = "DÖF Departman Değişikliği"
                    log_details = f"DÖF #{dof.id} için departman değiştirildi: {old_department_name} -> {selected_department.name}"
                    
                    # Detaylı departman bilgilerini logla
                    current_app.logger.info(f"DEPARTMAN ATAMA - Seçilen departman ID: {selected_dept_id}, Adı: {selected_department.name}")
                    
                    # DEPARTMAN YÖNETİCİLERİNİ BUL - ÖNEMLİ
                    managers = User.query.filter_by(department_id=selected_dept_id, active=True).filter(User.role.in_([UserRole.DEPARTMENT_MANAGER, UserRole.FRANCHISE_DEPARTMENT_MANAGER])).all()
                    current_app.logger.info(f"Bulunan departman yöneticisi sayısı: {len(managers)}")
                    
                    if not managers:
                        current_app.logger.warning(f"DİKKAT: {selected_department.name} departmanı için aktif yönetici bulunamadı!")
                        flash(f"Dikkat: {selected_department.name} departmanı için aktif yönetici bulunamadı. Bildirim gönderilemeyecek.", "warning")
                    
                    # YENİ MERKEZİ BİLDİRİM SİSTEMİ KULLANIMI
                    # Tüm yöneticileri ve departman bilgilerini logla
                    if managers:
                        for manager in managers:
                            current_app.logger.info(f"Yönetici bilgileri: ID: {manager.id}, Ad: {manager.full_name}, E-posta: {manager.email}")
                    else:
                        current_app.logger.warning(f"Departman {selected_department.name} için yönetici bulunamadı!")
                    
                    # Merkezi bildirim sistemini kullan
                    from notification_system import notify_department_assignment
                    
                    # Bildirim göndermeyi başlat
                    current_app.logger.info(f"Departman atama bildirimi gönderiliyor: DÖF #{dof.id} -> {selected_department.name}")
                    notification_count = notify_department_assignment(dof.id, selected_dept_id, current_user.id)
                    
                    # Bildirim sonucunu göster
                    if notification_count > 0:
                        flash(f"DÖF #{dof.id} {selected_department.name} departmanına atandı. {notification_count} kişiye bildirim gönderildi.", "success")
                        current_app.logger.info(f"Toplam {notification_count} bildirim gönderildi.")
                    else:
                        flash(f"DÖF #{dof.id} {selected_department.name} departmanına atandı ancak bildirim gönderilemedi.", "warning")
                        current_app.logger.warning("Bildirim gönderilemedi!")
                                
                elif submit_action == 'approve':
                    # PLANNING durumundaki DÖF için ayrı işlem - kalite planı incelemesi
                    if dof.status == DOFStatus.PLANNING:
                        if 'approve_plan' in request.form:
                            # Kök neden ve aksiyon planı uygun bulundu, Uygulama aşamasına geç
                            dof.status = DOFStatus.IMPLEMENTATION
                            dof.review_comment = form.comment.data
                            flash("Kök neden ve aksiyon planı onaylanarak DÖF uygulama aşamasına geçti.", "success")
                            
                            # Bildirim gönder
                            notification = Notification(
                                user_id=dof.created_by,
                                dof_id=dof.id,
                                message=f"DÖF #{dof.id} kök neden ve aksiyon planı onaylanarak uygulama aşamasına geçti."
                            )
                            db.session.add(notification)
                            
                            # Aksiyon kaydı için bilgiler
                            action_message = f"Kök neden ve aksiyon planı onaylanarak uygulama aşamasına geçildi: {form.comment.data}"
                            new_status = DOFStatus.IMPLEMENTATION
                            success_message = "Kök neden ve aksiyon planı onaylanıp uygulama aşamasına geçildi."
                            log_action = "DÖF Plan Onayı"
                            log_details = f"DÖF #{dof.id} uygulama aşamasına geçti."
                        elif 'request_changes' in request.form:
                            # Düzeltme talep edildi
                            dof.status = DOFStatus.ASSIGNED
                            dof.review_comment = form.comment.data
                            flash("Kök neden ve aksiyon planı için düzeltme talep edildi.", "warning")
                            
                            # Bildirim gönder
                            notification = Notification(
                                user_id=dof.created_by,
                                dof_id=dof.id,
                                message=f"DÖF #{dof.id} için kök neden ve aksiyon planında düzenlemeler talep edildi."
                            )
                            db.session.add(notification)
                            
                            # Aksiyon kaydı için bilgiler 
                            action_message = f"Kök neden ve aksiyon planında düzenlemeler talep edildi: {form.comment.data}"
                            new_status = DOFStatus.ASSIGNED
                            success_message = "Kök neden ve aksiyon planında düzenlemeler talep edildi."
                            log_action = "DÖF Plan Düzeltme Talebi"
                            log_details = f"DÖF #{dof.id} için plan düzenleme talep edildi."
                    else:
                        # Sadece departman değişikliği yapılıyorsa
                        if is_department_change_only:
                            # Eski departman bilgisini tut
                            old_department = dof.department.name if dof.department else "Belirtilmemiş"
                            
                            # Departmanı güncelle
                            dof.department_id = department.id
                            
                            # Yorum varsa ekle
                            if form.comment.data:
                                action_message = f"Departman değiştirildi: {old_department} -> {department.name}. {form.comment.data}"
                            else:
                                action_message = f"Departman değiştirildi: {old_department} -> {department.name}"
                                
                            # Aksiyon kaydı ve log detayları
                            new_status = dof.status  # Durumu değiştirme
                            success_message = f"DÖF'e atanan departman {department.name} olarak güncellendi."
                            log_action = "DÖF Departman Değişikliği"
                            log_details = f"DÖF #{dof.id} için departman değiştirildi."
                            
                            # ESKİ BİLDİRİM SİSTEMİ KALDIRILDI - Merkezi bildirim sistemi kullanılıyor
                            # Bu bölümdeki eski Notification kayıtları kaldırıldı
                        else:
                            # Normal ilk inceleme işlemi - eski akış
                            # DÖF bilgilerini güncelle
                            dof.status = DOFStatus.ASSIGNED  # Departman Yanıtı Bekleniyor durumu
                            dof.department_id = department.id
                            dof.review_comment = form.comment.data
                            dof.assigned_to = None  # Atanan kişiyi temizle - artık departman bazlı çalışıyoruz
                            dof.assigned_date = datetime.now()
                            
                            # Yeni departmanın yöneticisine bildirim gönder
                            if department.manager:
                                notification = Notification(
                                    user_id=department.manager.id,
                                    dof_id=dof.id,
                                    message=f"DÖF #{dof.id} departmanınıza atandı."
                                )
                                db.session.add(notification)
                            
                            # DÖF sahibine bildirim gönder
                            notification = Notification(
                                user_id=dof.created_by,
                                dof_id=dof.id,
                                message=f"DÖF #{dof.id} {department.name} departmanına atandı."
                            )
                            db.session.add(notification)
                            
                            # Aksiyon kaydı için bilgiler
                            action_message = f"DÖF {department.name} departmanına atandı: {form.comment.data}"
                            new_status = DOFStatus.ASSIGNED
                            success_message = f"DÖF başarıyla {department.name} departmanına atandı."
                            log_action = "DÖF Departman Ataması"
                            log_details = f"DÖF #{dof.id} {department.name} departmanına atandı."
                
                # Reddetme işlemi
                elif submit_action == 'reject':
                    dof.status = DOFStatus.REJECTED
                    dof.review_comment = form.comment.data
                    
                    # Bildirim gönder
                    notification = Notification(
                        user_id=dof.created_by,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} değerlendirme sonucu reddedildi. Detaylar için DÖF detayını inceleyiniz."
                    )
                    db.session.add(notification)
                    
                    # Aksiyon kaydı için bilgiler
                    action_message = f"DÖF reddedildi: {form.comment.data}"
                    new_status = DOFStatus.REJECTED
                    success_message = "DÖF reddedildi ve ilgili kişilere bildirim gönderildi."
                    log_action = "DÖF Reddetme"
                    log_details = f"DÖF #{dof.id} reddedildi."
                
                # Yeni DÖF açma talebi
                elif submit_action == 'new_dof':
                    # Mevcut DÖF'e özel bir durum ekle ve kapat
                    dof.status = DOFStatus.CLOSED
                    dof.review_comment = form.comment.data + "\n\nYeni DÖF açılması talep edildi."
                    
                    # DÖF oluşturucuya bildirim gönder
                    notification = Notification(
                        user_id=dof.created_by,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} için yeni bir DÖF açılması talep edildi. Lütfen ilgili konular için yeni DÖF açınız."
                    )
                    db.session.add(notification)
                    
                    # OTOMATiK DÖF OLUŞTURMA YAPILMIYOR - Kullanıcının manuel olarak oluşturması bekleniyor
                    current_app.logger.info(f"DÖF #{dof.id} kapatıldı, ilişkili yeni DÖF ihtiyacı bildirildi (otomatik oluşturma devre dışı)")
                    
                    # Kaynak departmana bildirim gönder - manuel DÖF açmaları için
                    try:
                        # Departman yöneticilerini bul
                        dept_managers = User.query.filter(User.department_id == dof.department_id, 
                                                      User.role == UserRole.DEPARTMENT_MANAGER).all()
                        
                        for manager in dept_managers:
                            notification = Notification(
                                user_id=manager.id,
                                dof_id=dof.id,
                                message=f"Kalite yöneticisi {current_user.full_name}, #{dof.id} DÖF'e ilişkili yeni bir DÖF açmanızı tavsiye etmektedir."
                            )
                            db.session.add(notification)
                            
                        # Kalite yöneticilerine bildirim gönder
                        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
                        for qm in quality_managers:
                            if qm.id != current_user.id:  # Kendine bildirim gönderme
                                notification = Notification(
                                    user_id=qm.id,
                                    dof_id=dof.id,
                                    message=f"{current_user.full_name}, #{dof.id} DÖF için ilişkili yeni DÖF açılmasını tavsiye etti."
                                )
                                db.session.add(notification)
                                
                        success_message = "DÖF kapatıldı ve ilişkili yeni DÖF açılması tavsiye edildi. Departman yöneticisine bildirim gönderildi."
                    except Exception as e:
                        current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
                        success_message = "DÖF kapatıldı, ancak bildirim gönderilirken bir hata oluştu."
                        import traceback
                        current_app.logger.error(traceback.format_exc())
                    
                    # Aksiyon kaydı için bilgiler
                    action_message = f"Yeni DÖF açılması talep edildi: {form.comment.data}"
                    new_status = DOFStatus.CLOSED
                    success_message = "DÖF kapatıldı ve yeni DÖF açılması talep edildi."
                    log_action = "DÖF Kapatma"
                    log_details = f"DÖF #{dof.id} kapatıldı, yeni DÖF açılması talep edildi."
                
                # Gereksiz DÖF - Direk Kapatma
                elif submit_action == 'close_unnecessary':
                    # DÖF'ü gereksiz olarak doğrudan kapat
                    dof.status = DOFStatus.CLOSED
                    dof.review_comment = form.comment.data + "\n\nGereksiz DOF olarak değerlendirildi ve kapatıldı."
                    dof.closed_at = datetime.now()
                    
                    # DÖF oluşturucuya bildirim gönder
                    notification = Notification(
                        user_id=dof.created_by,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} kalite incelemesi sonucu gereksiz bulunarak kapatıldı."
                    )
                    db.session.add(notification)
                    
                    current_app.logger.info(f"DÖF #{dof.id} gereksiz olarak değerlendirilip kapatıldı")
                    
                    # Aksiyon kaydı için bilgiler
                    action_message = f"Gereksiz DÖF olarak değerlendirildi ve kapatıldı: {form.comment.data}"
                    new_status = DOFStatus.CLOSED
                    success_message = "DÖF gereksiz olarak değerlendirilip kapatıldı."
                    log_action = "DÖF Gereksiz Kapatma"
                    log_details = f"DÖF #{dof.id} gereksiz olarak kapatıldı."
                
                # Form dolduruldu ancak desteklenmeyen bir buton kullanıldı
                else:
                    flash("Desteklenmeyen işlem tipi. Lütfen doğru işlemi seçin.", "warning")
                    return render_template('dof/quality_review.html', form=form, dof=dof)
                
                # Tüm akşiyon tipleri için ortak işlemler
                try:
                    # Aksiyon kaydı
                    action = DOFAction(
                        dof_id=dof.id,
                        user_id=current_user.id,
                        action_type=2,  # 2: İnceleme
                        comment=action_message,
                        old_status=old_status,
                        new_status=new_status,
                        created_at=datetime.now()
                    )
                    db.session.add(action)
                    
                    # DÖF durumunu güncelle
                    dof.status = new_status
                    dof.updated_at = datetime.now()
                    
                    # Veritabanındaki departmanı tekrar kontrol et ve doğru olduğundan emin ol
                    if submit_action == 'change_department' and department:
                        current_app.logger.info(f"Son kontrol - değiştirilen departman ID = {dof.department_id}, departman = {department.name}")
                        # Departman değişikliğinde değişikliğin doğru olduğundan emin olmak için bir kez daha set et
                        dof.department_id = department.id
                    
                    # Kayıt işlemlerini tamamla
                    db.session.commit()
                    current_app.logger.info(f"Veritabanı değişiklikleri başarıyla kaydedildi. Son departman ID = {dof.department_id}")
                    
                    # Aktivite logu
                    log_activity(
                        user_id=current_user.id,
                        action=log_action,
                        details=log_details,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                    
                    # YENİ MERKEZİ BİLDİRİM SİSTEMİ İLE BİLDİRİM GÖNDER
                    try:
                        from notification_system import notify_for_dof_event
                        
                        # Durum değişikliğine göre bildirim tipi belirle
                        if new_status == DOFStatus.ASSIGNED and submit_action != 'change_department':
                            # Normal departman atama bildirimi (sadece ilk atama için)
                            from notification_system import notify_department_assignment
                            notify_department_assignment(dof.id, dof.department_id, current_user.id)
                            current_app.logger.info(f"DÖF #{dof.id} için departman atama bildirimi gönderildi")
                        elif submit_action == 'change_department':
                            # Departman değiştirme için özel bildirim (yukarıda zaten gönderildi)
                            current_app.logger.info(f"DÖF #{dof.id} departman değiştirme bildirimi zaten gönderildi")
                        elif new_status == DOFStatus.REJECTED:
                            # Reddetme bildirimi
                            notify_for_dof_event(dof.id, "reject", current_user.id)
                            current_app.logger.info(f"DÖF #{dof.id} için red bildirimi gönderildi")
                        elif new_status == DOFStatus.PLANNING:
                            # Aksiyon planı oluşturma bildirimi
                            notify_for_dof_event(dof.id, "plan", current_user.id)
                            current_app.logger.info(f"DÖF #{dof.id} için aksiyon planı bildirimi gönderildi")
                        elif new_status == DOFStatus.IMPLEMENTATION:
                            # Aksiyon planı onaylama bildirimi
                            notify_for_dof_event(dof.id, "approve_plan", current_user.id)
                            current_app.logger.info(f"DÖF #{dof.id} için aksiyon planı onay bildirimi gönderildi")
                        else:
                            # Genel durum değişikliği bildirimi
                            notify_for_dof_event(dof.id, "update", current_user.id)
                            current_app.logger.info(f"DÖF #{dof.id} için durum değişikliği bildirimi gönderildi")
                    except Exception as e:
                        current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
                        import traceback
                        current_app.logger.error(traceback.format_exc())
                    
                    # Başarılı işlem mesajı
                    flash(success_message, "success" if new_status == DOFStatus.ASSIGNED else "warning")
                    
                    # Başarılı işlem sonrası yönlendirme
                    return redirect(url_for('dof.detail', dof_id=dof.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"DÖF işlemi hatası: {str(e)}")
                    flash(f"DÖF işlemi sırasında bir hata oluştu: {str(e)}", "danger")
                    return render_template('dof/quality_review.html', form=form, dof=dof)
            
            except Exception as e:
                # Hata durumunda işlemi geri al ve hata mesajı göster
                db.session.rollback()
                current_app.logger.error(f"DÖF inceleme işleminde hata: {str(e)}")
                flash("DÖF çözümü reddedildi, ancak süreç geri dönmeyecek ve Kalite yöneticilerine yönlendirildi. Kalite değerlendirmesi sonucunda gerekirse yeni DÖF açılabilir.", "info")
                
                # Detaylı hata günlüğü
                import traceback
                current_app.logger.error(f"Hata ayrıntıları: {traceback.format_exc()}")
                
                return render_template('dof/quality_review.html', form=form, dof=dof)
        else:
            # Form doğrulanamadı, hata mesajları gösteriliyor
            flash("Form doğrulanmadı. Lütfen zorunlu alanları kontrol ediniz.", "danger")
    
    # GET isteği veya başarısız POST sonrası form gösterimi
    return render_template('dof/quality_review.html', form=form, dof=dof)

@dof_bp.route('/dashboard')
@dof_bp.route('/dashboard/<int:department_id>')
@login_required
def dashboard(department_id=None):
    # Kullanıcı aktivitelerini yükle
    
    # Kullanıcının departmanına ve rolüne göre DÖF durum sayılarını getir
    # get_dof_status_counts fonksiyonuna current_user parametresini gönderiyoruz
    # böylece kullanıcı yetkilerine göre doğru filtreleme yapılacak
    
    from auth_service import AuthService
    
    # Yetkiye göre DÖF sayılarını getir
    current_app.logger.info(f"Dashboard özet kutusu için DÖF sayıları getiriliyor: user={current_user.username}, role={current_user.role}")
    
    # İLGİLİ NOT: DÖF sayısı doğru gösterilmesi için ilişkili DÖF'ler haricinde tutulmalı
    # Yetki kontrollü DÖF sayıları (AuthService ile merkezi yetki kontrolü)
    # ilişkili DÖF'ler filtrelemesi ~DOF.title.like("[İlişkili #%") ile get_dof_status_counts içinde yapılıyor
    current_app.logger.info("DASHBOARD: Toplam DÖF sayısı için ilişkili DÖF'ler filtreleniyor")
    
    # Kullanıcı rolüne göre DÖF sayılarını getir
    # İlişkili DÖF'leri hariç tut (tüm kullanıcılar için ortak filtre)
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    
    # Rolüne göre DÖF sayısı hesaplama stratejisini belirle
    if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Yöneticiler - tüm DÖF'leri görebilir (sadece ilişkili olmayan)
        total_dof_count = DOF.query.filter(related_dof_filter).count()
        current_app.logger.info(f"DASHBOARD: Toplam DÖF sayısı (admin/kalite): {total_dof_count}")
    
    elif (current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and current_user.department_id:
        # Departman yöneticileri - sadece kendi departmanına atanan DÖF'leri say
        # "Şevket Mindür" ve "teşekkür" gibi tip/kategori bilgilerini filtrelemek için
        # Sadece departmana atanan ve oluşturulan DÖF'leri say
        dept_id = current_user.department_id
        
        # Departmana ait kullanıcıları bul
        dept_users = User.query.filter_by(department_id=dept_id).all()
        dept_user_ids = [user.id for user in dept_users]
        
        # Departmanın DÖF'lerini say: departmana atanan veya departman üyelerinin oluşturduğu
        total_dof_count = DOF.query.filter(
            related_dof_filter,
            or_(
                DOF.department_id == dept_id,
                DOF.created_by.in_(dept_user_ids) if dept_user_ids else False
            )
        ).count()
        current_app.logger.info(f"DASHBOARD: Toplam DÖF sayısı (departman yöneticisi): {total_dof_count}, departman={current_user.department_id}")
    
    else:
        # Normal kullanıcılar - filtrelenmiş DÖF'leri görebilir
        # get_dof_status_counts fonksiyonu ile elde edilen toplamı kullan
        total_dof_count = None  # get_dof_status_counts'tan gelecek
        current_app.logger.info(f"DASHBOARD: Normal kullanıcı DÖF toplamı")  
    
    # Filtrelenmiş sayılar için normal fonksiyonu kullan (herkes için detaylar gerekli)
    status_counts = get_dof_status_counts(current_user=current_user)
    
    # Eğer özel toplam sayı hesaplandıysa, toplamı güncelle
    if total_dof_count is not None:
        status_counts['total'] = total_dof_count
        
    # Loglama
    current_app.logger.info(f"DASHBOARD: Kullanıcı {current_user.username} için gösterilen toplam DÖF sayısı: {status_counts['total']}")


    
    # Bölge müdürü için çoklu departman filtresi kontrolü
    selected_departments = []
    selected_department = None # Geriye dönük uyumluluk için
    selected_department_names = []
    
    # Kullanıcının yönettiği tüm departmanları al
    managed_departments = current_user.get_managed_departments()
    managed_dept_ids = [dept.id for dept in managed_departments]
    
    # URL'den departmanlara göre filtreleme kontrolü
    departments_param = request.args.get('departments')
    
    if departments_param and current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
        # Çoklu departman filtreleme - departments=1,2,3 formatında
        try:
            # Virgülle ayrılmış ID'leri parse et
            department_ids = [int(d) for d in departments_param.split(',')]
            # Sadece kullanıcının yönettiği departmanlara izin ver
            selected_departments = [d_id for d_id in department_ids if d_id in managed_dept_ids]
            
            # Seçili departman isimlerini belleğe al
            for dept in managed_departments:
                if dept.id in selected_departments:
                    selected_department_names.append(dept.name)
                    
            current_app.logger.info(f"Bölge Müdürü {current_user.username}, {len(selected_departments)} departman filtresi uyguluyor: {selected_department_names}")
            
        except Exception as e:
            current_app.logger.error(f"Departman filtre parametresi hatası: {str(e)}")
            selected_departments = []
    
    # Eski format (tek departman ID'si) için geriye dönük uyumluluk
    elif department_id and current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
        if department_id in managed_dept_ids:
            selected_department = Department.query.get(department_id)
            selected_departments = [department_id]
            selected_department_names = [selected_department.name]
            current_app.logger.info(f"Bölge Müdürü {current_user.username}, {selected_department.name} departmanını görüntülüyor")
    
    # Kalite departmanı için özel sayaçlar
    # İnceleme bekleyen DÖF'ler hem SUBMITTED hem de IN_REVIEW durumundaki DÖF'leri içerir
    waiting_review_count = DOF.query.filter(DOF.status.in_([DOFStatus.SUBMITTED, DOFStatus.IN_REVIEW])).count()
    waiting_resolution_count = DOF.query.filter_by(status=DOFStatus.ASSIGNED).count()
    
    # Son eklenen 5 DÖF (genel kategorisi)
    recent_dofs = DOF.query.order_by(DOF.created_at.desc()).limit(5).all()
    
    # Kullanıcıya atanan DÖF'ler
    assigned_dofs = DOF.query.filter_by(assigned_to=current_user.id)\
                     .filter(DOF.status != DOFStatus.CLOSED)\
                     .order_by(DOF.created_at.desc()).limit(5).all()
    
    # Kullanıcının yönettiği departmanları belirle
    user_departments = []
    managed_dept_ids = []
    
    # Kullanıcının rolüne göre yönettiği departmanları getir
    if current_user.role == UserRole.ADMIN or current_user.role == UserRole.QUALITY_MANAGER:
        # Admin ve Kalite Yöneticisi tüm departmanları görebilir
        user_departments = Department.query.filter_by(is_active=True).all()
        managed_dept_ids = [dept.id for dept in user_departments]
        
    elif current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        # Departman yöneticisi veya franchise departman yöneticisi sadece kendi departmanını görür
        if current_user.department_id:
            dept = Department.query.get(current_user.department_id)
            user_departments = [dept]
            managed_dept_ids = [dept.id]
                
    elif current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
        # Çoklu departman yöneticisi, yönettiği tüm departmanları görür
        user_departments = current_user.get_managed_departments()
        managed_dept_ids = [dept.id for dept in user_departments]
        
    elif current_user.role == UserRole.DIRECTOR:
        # Direktör, altındaki bölge müdürlerinin yönettiği departmanları görür
        user_departments = current_user.get_managed_departments()
        managed_dept_ids = [dept.id for dept in user_departments]
        
    else:
        # Normal kullanıcı sadece kendi departmanını görür
        if current_user.department_id:
            dept = Department.query.get(current_user.department_id)
            if dept:
                user_departments = [dept]
                managed_dept_ids = [current_user.department_id]
    
    # Eğer çoklu departman yöneticisi ve seçilen departmanlar varsa, filtrelemeyi onlara göre yap
    if current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING] and selected_departments:
        # Seçilen departmanları al
        user_departments = [dept for dept in managed_departments if dept.id in selected_departments]
        managed_dept_ids = selected_departments
        
    print(f"Kullanıcı: {current_user.username}, Yönettiği departmanlar: {[dept.name for dept in user_departments]}")
    
    # Departmanların açtığı DÖF'ler
    dept_created_dofs = []
    if managed_dept_ids:
        dept_created_query = DOF.query.join(User, DOF.created_by == User.id)\
                                .filter(User.department_id.in_(managed_dept_ids))\
                                .filter(DOF.status != DOFStatus.CLOSED)\
                                .order_by(DOF.created_at.desc()).limit(5)
        dept_created_dofs = dept_created_query.all()
    
    # Departmanlara atanan DÖF'ler - AuthService kullanarak güvenli ve tutarlı filtreleme
    dept_assigned_dofs = []
    if managed_dept_ids:
        # Yeni merkezi auth service ile yönetilen
        from auth_service import AuthService
        
        # Temel sorguyu oluştur
        base_query = DOF.query.filter(DOF.department_id.in_(managed_dept_ids)).filter(DOF.status != DOFStatus.CLOSED)
        
        # AuthService ile kullanıcıya göre filtreleme uygula
        filtered_query = AuthService.filter_viewable_dofs(current_user, base_query)
        
        # Loglama
        current_app.logger.info(f"Kullanıcı {current_user.username}, rol={current_user.role}, departmanlarına atanan DÖF'ler yetki filtreli sorgusu")
        current_app.logger.info(f"Yönetilen departmanlar: {managed_dept_ids}")
        
        # Sonuçları getir - sıralama ve limit
        dept_assigned_dofs = filtered_query.order_by(DOF.created_at.desc()).limit(5).all()
        
        # Sonuç kontrolü ve loglama
        current_app.logger.debug(f"{current_user.username} kullanıcısı için departmanlara atanan DÖF sayısı: {len(dept_assigned_dofs)}")
        current_app.logger.debug(f"DÖF ID'leri: {[dof.id for dof in dept_assigned_dofs]}")
    else:
        current_app.logger.warning(f"Kullanıcı {current_user.username} için yönetilen departman bulunamadı!")
    
    # Eski yöntem - department_dofs
    department_dofs = []
    if (current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and current_user.department_id:
        department_dofs = DOF.query.filter_by(department_id=current_user.department_id).filter(DOF.status != DOFStatus.CLOSED).order_by(DOF.created_at.desc()).limit(5).all()
    
    # Okunmamış bildirimler
    unread_notifications = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Admin ve kalite yöneticileri için kullanıcı aktiviteleri
    user_activities = []
    system_logs = []
    
    if current_user.is_admin() or current_user.is_quality_manager():
        # User bilgisini de sorguya ekleyerek eager loading ile daha verimli bir sorgu yapılandırıyoruz
        from sqlalchemy.orm import joinedload
        user_activities = UserActivity.query.options(joinedload(UserActivity.user))\
                                      .order_by(UserActivity.created_at.desc())\
                                      .limit(10)\
                                      .all()
        
        # Aktivite olup olmadığını loglama
        if not user_activities:
            current_app.logger.warning(f"Dikkat: Kullanıcı {current_user.id} için aktivite bulunamadı! Bu bir soruna işaret edebilir.")
        else:
            current_app.logger.info(f"Bilgi: {len(user_activities)} aktivite bulundu ve dashboard'a yükleniyor.")
        
        # Sadece admin için sistem logları
        if current_user.is_admin():
            from models import SystemLog
            system_logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(5).all()
    
    # Tarihe göre terminleri ayırma
    # Yerel sistem saatini kullan
    current_date = datetime.now()
    future_date = current_date + timedelta(days=30)  # Önümüzdeki 30 gün
    
    # Departman filtresi için hazırlık
    user_dept_id = current_user.department_id if current_user.department_id else None
    
    # Departmanıma atanan yaklaşan terminler
    assigned_upcoming_deadlines = []
    if user_dept_id:
        assigned_upcoming_deadlines = DOF.query.filter(
            DOF.deadline.isnot(None),
            DOF.deadline > current_date,
            DOF.deadline <= future_date,
            DOF.department_id == user_dept_id,
            DOF.status.in_([DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION])
        ).order_by(DOF.deadline.asc()).limit(5).all()
    
    # Departmanımın açtığı yaklaşan terminler
    created_upcoming_deadlines = []
    if user_dept_id:
        # Departman üyelerini bul
        dept_user_ids = [user.id for user in User.query.filter_by(department_id=user_dept_id).all()]
        if dept_user_ids:
            created_upcoming_deadlines = DOF.query.filter(
                DOF.deadline.isnot(None),
                DOF.deadline > current_date,
                DOF.deadline <= future_date,
                DOF.created_by.in_(dept_user_ids),
                DOF.status.in_([DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION])
            ).order_by(DOF.deadline.asc()).limit(5).all()
    
    # Departmanıma atanan geçmiş terminler
    assigned_overdue_deadlines = []
    if user_dept_id:
        assigned_overdue_deadlines = DOF.query.filter(
            DOF.deadline.isnot(None),
            DOF.deadline <= current_date,
            DOF.department_id == user_dept_id,
            DOF.status.in_([DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION])
        ).order_by(DOF.deadline.desc()).limit(5).all()
    
    # Departmanımın açtığı geçmiş terminler
    created_overdue_deadlines = []
    if user_dept_id:
        # Departman üyelerini bul
        dept_user_ids = [user.id for user in User.query.filter_by(department_id=user_dept_id).all()]
        if dept_user_ids:
            created_overdue_deadlines = DOF.query.filter(
                DOF.deadline.isnot(None),
                DOF.deadline <= current_date,
                DOF.created_by.in_(dept_user_ids),
                DOF.status.in_([DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION])
            ).order_by(DOF.deadline.desc()).limit(5).all()
    
    # Geriye uyumluluk için eski değişkenler
    upcoming_deadlines = assigned_upcoming_deadlines + created_upcoming_deadlines
    past_deadlines = assigned_overdue_deadlines + created_overdue_deadlines
    
    # Çoklu departman yöneticisi için yönetilen departman listesini ve seçili departmanı şablona gönder
    managed_departments = []
    if current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
        managed_departments = current_user.get_managed_departments()
    # Eksik değişkenleri tamamlama
    notifications = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           status_counts=status_counts,
                           waiting_review_count=waiting_review_count,
                           waiting_resolution_count=waiting_resolution_count,
                           recent_dofs=recent_dofs,
                           assigned_dofs=assigned_dofs,
                           dept_created_dofs=dept_created_dofs,
                           dept_assigned_dofs=dept_assigned_dofs,
                           user_departments=user_departments,
                           selected_department=selected_department,  # Geriye dönük uyumluluk için
                           selected_departments=selected_departments,
                           selected_department_names=selected_department_names,
                           upcoming_deadlines=upcoming_deadlines,
                           past_deadlines=past_deadlines,
                           # Yeni departman bazlı termin değişkenleri
                           assigned_upcoming_deadlines=assigned_upcoming_deadlines,
                           created_upcoming_deadlines=created_upcoming_deadlines,
                           assigned_overdue_deadlines=assigned_overdue_deadlines,
                           created_overdue_deadlines=created_overdue_deadlines,
                           # Bölge müdürü için departman filtreleme desteği
                           managed_departments=managed_departments,
                           # Şablonda kullanılan tarih değişkenleri
                           current_date=current_date,
                           future_date=future_date,
                           # Diğer eksik değişkenler
                           notifications=notifications,
                           department_dofs=department_dofs,
                           user_activities=user_activities if 'user_activities' in locals() else [],
                           system_logs=system_logs if 'system_logs' in locals() else [])

@dof_bp.route('/dof/create', methods=['GET', 'POST'])
@login_required
@optimize_db_operations
def create_dof():
    # Başlama zamanı (performans ölçümü için)
    start_time = time.time()
    # Form tipini create olarak belirt ve mevcut kullanıcıyı gönder
    # Bölge Müdürü için yönetilen departmanların listelenmesini sağlar
    form = DOFForm(form_type='create', current_user=current_user)
    
    # İlişkili DÖF kontrolü - URL'den related_dof parametresi kontrolu
    related_dof_id = request.args.get('related_dof', None)
    related_dof = None
    
    if related_dof_id:
        try:
            related_dof = DOF.query.get(related_dof_id)
            if related_dof:
                # İlişkili DÖF bilgilerini forma ön yükle
                form.title.data = f"[İlişkili #{related_dof.id}] {related_dof.title}"
                form.description.data = f"Bu DÖF, #{related_dof.id} numaralı DÖF ile ilişkilidir.\n\n"
                form.dof_type.data = related_dof.dof_type
                form.dof_source.data = related_dof.dof_source
                # Priority field has been removed
                # form.priority.data = related_dof.priority
                form.department.data = related_dof.department_id if related_dof.department_id else 0
                
                flash(f"#{related_dof.id} numaralı DÖF ile ilişkili yeni DÖF oluşturuyorsunuz. Gerekli alanlar otomatik dolduruldu.", "info")
        except Exception as e:
            current_app.logger.error(f"İlişkili DÖF yükleme hatası: {str(e)}")
            flash("İlişkili DÖF bilgileri yüklenirken bir hata oluştu.", "warning")
    
    if form.validate_on_submit():
        # DOF kaynağını al
        dof_source = form.dof_source.data
        
        # Atanan departman ID'si - rol bazlı ata
        if current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING] and form.managed_departments.data:
            # Çoklu departman yöneticisi için yönetilen departmanlardan seçilen
            assigned_dept_id = form.managed_departments.data
            current_app.logger.info(f"Çoklu departman yöneticisi için yönetilen departman seçildi: {assigned_dept_id}")
        else:
            # Normal seçim yoluyla belirlenen departman
            assigned_dept_id = form.department.data if form.department.data != 0 else None
            
            # Eğer departman atanmamışsa ve kullanıcının departmanı varsa, kullanıcının departmanını ata
            if assigned_dept_id is None and current_user.department_id:
                assigned_dept_id = current_user.department_id
                current_app.logger.info(f"Kullanıcının departmanı otomatik atandı: {assigned_dept_id}")
        
        # Dinamik DOF kodu oluştur - yeni format: kaynak dept - atanan dept - tip - DOF kaynağı
        dof_code = generate_dof_code(form.dof_type.data, dof_source, assigned_dept_id, current_user.id)
        
        # Temel DÖF kaydı oluştur
        dof = DOF(
            code=dof_code,  # Dinamik oluşturulan kodu ekle
            title=form.title.data,
            description=form.description.data,
            dof_type=form.dof_type.data,
            dof_source=form.dof_source.data,
            # priority field has been removed
            
            department_id=assigned_dept_id,
            status=DOFStatus.IN_REVIEW,
            created_by=current_user.id,
            created_at=datetime.now(),
            # DÖF oluştururken termin tarihi belirtilmez
            due_date=None,
            # Müşteri şikayeti bilgileri
            channel=form.channel.data if form.dof_source.data == DOFSource.CUSTOMER_COMPLAINT else None,
            complaint_date=form.complaint_date.data if form.dof_source.data == DOFSource.CUSTOMER_COMPLAINT else None
        )
        
        # Tek seferde tüm dosyaları ve aksiyonları ekle
        db.session.add(dof)
        db.session.flush()  # ID oluşturmak için flush yap
        
        # Dosya eklerini işlemek için hazırlık
        attachments = []
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                file_data = save_file(file)
                
                attachment = Attachment(
                    dof_id=dof.id,
                    filename=file_data['filename'],
                    file_path=file_data['file_path'],
                    file_size=file_data['file_size'],
                    file_type=file_data['file_type'],
                    uploaded_by=current_user.id,
                    uploaded_at=datetime.now()
                )
                attachments.append(attachment)
        
        # DÖF oluşturma aksiyonu ekle
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=1,  # 1: Oluşturma
            comment="DÖF oluşturuldu",
            created_at=datetime.now()
        )
        
        # Tüm objeleri tek seferde veritabanına ekle
        if attachments:
            db.session.add_all(attachments)
        db.session.add(action)
        
        # Asenkron işlemler için gerekli bilgileri hazırla
        dof_id = dof.id
        dof_title = dof.title
        dof_description = dof.description
        creator_name = current_user.full_name
        dept_id = dof.department_id
        
        # SADECE UYGULAMA BİLDİRİMLERİNİ GÖNDEREN FONKSİYON
        def send_app_notifications_only():
            """Bu fonksiyon sadece uygulama içi bildirimleri gönderir, e-posta GÖNDERMEZ"""
            current_app.logger.info(f"DÖF #{dof.id} için uygulama bildirimleri gönderiliyor (E-POSTA YOK)")
            
            # 1. notification_helper üzerinden bildirim göndermeyi dene
            try:
                from notification_helper import notify_all_relevant_users
                message = f"{current_user.full_name} tarafından '{dof.title}' (#{dof.id}) başlıklı yeni bir DÖF oluşturuldu"
                notification_count = notify_all_relevant_users(dof, "create", current_user, message, send_email=False)
                current_app.logger.info(f"YENİ DÖF #{dof.id} için {notification_count} uygulama bildirimi gönderildi")
                return True
            except Exception as e:
                current_app.logger.error(f"notify_all_relevant_users hatası: {str(e)}")
            
            # 2. Başarısız olduysa, eski yöntemi dene (e-posta gönderimi olmadan)
            try:
                notify_for_dof(dof, "create", current_user, send_email=False)
                current_app.logger.info(f"YENİ DÖF #{dof.id} için eski yöntemle uygulama bildirimleri gönderildi")
                return True
            except Exception as e:
                current_app.logger.error(f"notify_for_dof hatası: {str(e)}")
            
            # 3. Son çare: Kalite yöneticilerine doğrudan bildirim gönder
            try:
                from models import User, UserRole
                from utils import create_notification
                
                quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
                if quality_managers:
                    current_app.logger.info(f"{len(quality_managers)} kalite yöneticisi bulundu - doğrudan bildirim gönderiliyor")
                    count = 0
                    for qm in quality_managers:
                        if qm and qm.id != current_user.id:
                            message = f"{current_user.full_name} tarafından '{dof.title}' (#{dof.id}) başlıklı yeni bir DÖF oluşturuldu."
                            create_notification(qm.id, message, dof.id)
                            count += 1
                    current_app.logger.info(f"DÖF #{dof.id} için {count} kalite yöneticisine doğrudan bildirim gönderildi")
                    return count > 0
                else:
                    current_app.logger.warning("Hiç kalite yöneticisi bulunamadı, bildirim gönderilemiyor")
            except Exception as e:
                current_app.logger.error(f"Kalite yöneticisi bildirim hatası: {str(e)}")
            
            return False

        # Veritabanı işlemini tamamla
        db.session.commit()
        current_app.logger.info(f"DÖF #{dof.id} veritabanına başarıyla kaydedildi")
        
        # Eğer departman hala atanmamışsa, otomatik atama fonksiyonunu çağır
        if dof.department_id is None:
            success = dof.auto_assign_department()
            if success:
                current_app.logger.info(f"DÖF #{dof.id} için departman otomatik olarak atandı: {dof.department_id}")
            else:
                current_app.logger.warning(f"DÖF #{dof.id} için departman otomatik atanamadı")
        
        # YENİ MERKEZİ BİLDİRİM SİSTEMİNİ KULLAN
        try:
            from notification_system import notify_for_dof_event
            
            # Tek bir merkezi fonksiyon ile tüm bildirimleri gönder
            current_app.logger.info(f"DÖF #{dof.id} için yeni bildirim sistemi kullanılıyor")
            notification_count = notify_for_dof_event(dof.id, "create", current_user.id)
            
            current_app.logger.info(f"YENİ DÖF #{dof.id} için {notification_count} bildirim gönderildi")
        except Exception as e:
            current_app.logger.error(f"Yeni bildirim sistemi hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            
            # Hata durumunda yedek olarak eski yöntemi dene
            try:
                current_app.logger.warning(f"DÖF #{dof.id} için yedek bildirim sistemi deneniyor")
                # Uygulama bildirimleri
                send_direct_notifications_to_quality_managers(dof.id, current_user.full_name, dof.title)
                # E-posta
                send_beautiful_dof_email(dof, dof.id, dof.title, dof.description, current_user.full_name)
                current_app.logger.info(f"DÖF #{dof.id} için yedek bildirim sistemi başarılı")
            except Exception as backup_error:
                current_app.logger.error(f"Yedek bildirim sistemi de başarısız: {str(backup_error)}")
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="DÖF Oluşturma",
            details=f"DÖF oluşturuldu: {dof.title}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        # İşlem süresini ölç
        end_time = time.time()
        process_time = round((end_time - start_time) * 1000)  # milisaniye cinsinden
        current_app.logger.info(f"DÖF oluşturma süresi: {process_time}ms")
        
        flash('DÖF başarıyla oluşturuldu.', 'success')
        return redirect(url_for('dof.detail', dof_id=dof.id))
    
    return render_template('dof/create.html', form=form)
    
    return render_template('dof/create.html', form=form)

# Kalite departmanının DÖF son değerlendirmesi ve kapatması
@dof_bp.route('/dof/<int:dof_id>/close', methods=['GET', 'POST'])
@login_required
def close_dof(dof_id):
    """DÖF'ün kalite yöneticisi tarafından son değerlendirilmesi ve kapatılması"""
    # Log girişi ekle
    current_app.logger.info(f"DÖF Kapatma sayfası açıldı: user={current_user.username}, dof_id={dof_id}, method={request.method}")
    
    # DÖF'yi getir
    try:
        dof = DOF.query.get_or_404(dof_id)
    except Exception as e:
        current_app.logger.error(f"DÖF bulunamadı - HATA: {str(e)}")
        flash('DÖF bulunamadı veya erişim sırasında hata oluştu.', 'danger')
        return redirect(url_for('dof.list_dofs'))
        
    current_app.logger.info(f"DÖF #{dof_id} bulundu, başlık: {dof.title}, durum: {dof.status}")
    
    # Yetki kontrolü: Sadece kalite yöneticileri ve adminler erişebilir
    if current_user.role not in [UserRole.QUALITY_MANAGER, UserRole.ADMIN]:
        current_app.logger.warning(f"Yetkisiz erişim: {current_user.username}, rol={current_user.role}")
        flash('DÖF kapatma işlemi için Kalite Yöneticisi rolü gerekiyor.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Sadece çözüldü durumundaki DÖF'ler değerlendirilebilir
    if dof.status != DOFStatus.RESOLVED:
        current_app.logger.warning(f"Uygun olmayan durum: {dof.status}, beklenen: {DOFStatus.RESOLVED}")
        flash('Sadece ÇÖZÜLDÜ durumundaki DÖFler değerlendirilebilir ve kapatılabilir.', 'warning')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Form oluştur
    form = QualityClosureForm()
    
    # POST request kontrolü
    if request.method == 'POST':
        current_app.logger.info(f"POST isteği alındı, form verileri: {dict(request.form)}")
        current_app.logger.info(f"Form hatalar: {form.errors}")
        
        # Form validasyonunu bypass edelim ve manuel kontrol yapalım
        comment_value = request.form.get('comment', '').strip()
        current_app.logger.info(f"Yorum değeri: '{comment_value}'")
        
        if not comment_value:
            flash('Lütfen bir değerlendirme yorumu yazınız.', 'danger')
            return render_template('dof/quality_closure.html', dof=dof, form=form)
        
        # Hangi butona basıldığını kontrol et
        close_clicked = 'close' in request.form
        new_dof_clicked = 'new_dof' in request.form
        
        current_app.logger.info(f"Close button clicked: {close_clicked}")
        current_app.logger.info(f"New DOF button clicked: {new_dof_clicked}")
        
        if close_clicked:
            # Checkbox kontrolleri
            required_checks = ['check_cause', 'check_action', 'check_completion', 'check_effectiveness']
            all_checked = all(check in request.form for check in required_checks)
            
            current_app.logger.info(f"Checkbox kontrolleri: {[check for check in required_checks if check in request.form]}")
            
            if not all_checked:
                flash('Lütfen tüm kontrol listesi maddelerini onaylayın!', 'danger')
                return render_template('dof/quality_closure.html', dof=dof, form=form)
        
        try:
            current_app.logger.info(f"İşlem başlıyor...")
            # Aksiyon kaydı oluştur
            action = DOFAction(
                dof_id=dof.id,
                user_id=current_user.id,
                action_type=2,  # Durum Değişikliği
                comment=comment_value,
                old_status=dof.status,
                created_at=datetime.now()
            )
            
            # DÖF'ü kapat
            dof.status = DOFStatus.CLOSED
            dof.updated_at = datetime.now()
            dof.closed_at = datetime.now()
            action.new_status = DOFStatus.CLOSED
            
            # Tüm ilgili kullanıcılara bildirim gönder
            # DÖF oluşturan kişiye bildirim
            if dof.created_by:
                creator = User.query.get(dof.created_by)
                if creator:
                    notification = Notification(
                        user_id=creator.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - '{dof.title}' kalite tarafından KAPATILDI.",
                        created_at=datetime.now()
                    )
                    db.session.add(notification)
            
            # Çözüm uygulayan departmana bildirim
            if dof.department_id:
                dept_managers = User.query.filter_by(
                    department_id=dof.department_id,
                    role=UserRole.DEPARTMENT_MANAGER
                ).all()
                
                for manager in dept_managers:
                    notification = Notification(
                        user_id=manager.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - '{dof.title}' başarıyla KAPATILDI.",
                        created_at=datetime.now()
                    )
                    db.session.add(notification)
            
            # Diğer kalite yöneticilerine bildirim
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
            for qm in quality_managers:
                if qm.id != current_user.id:  # Kendine bildirim gönderme
                    notification = Notification(
                        user_id=qm.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - '{dof.title}' kapatıldı.",
                        created_at=datetime.now()
                    )
                    db.session.add(notification)
            
            # Değişiklikleri kaydet
            db.session.add(action)
            db.session.commit()
            
            # YENİ MERKEZİ BİLDİRİM SİSTEMİ İLE E-POSTA VE BİLDİRİM GÖNDER
            try:
                from notification_system import notify_for_dof_event
                
                # Tek fonksiyon çağrısı ile tüm bildirimleri gönder (hem uygulama içi hem e-posta)
                notification_count = notify_for_dof_event(dof.id, "close", current_user.id)
                current_app.logger.info(f"DÖF #{dof.id} kapatma bildirimi: {notification_count} kişiye gönderildi")
                
                flash(f"DÖF başarıyla kapatıldı. {notification_count} kişiye bildirim ve e-posta gönderildi.", "success")
                
            except Exception as e:
                current_app.logger.error(f"Kapatma bildirim sistemi hatası: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                
                # Hata durumunda eski yöntemi kullan
                flash("DÖF başarıyla kapatıldı. İlgili tüm taraflara bildirim gönderildi.", "success")
            
            return redirect(url_for('dof.detail', dof_id=dof_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"DÖF kapatma hatası: {str(e)}")
            flash("DÖF kapatma işlemi sırasında bir hata oluştu.", "danger")
            
            # Hata günlüğü
            import traceback
            current_app.logger.error(traceback.format_exc())
    
    # GET isteği için formı göster
    current_app.logger.info(f"GET isteği - form template'i gösteriliyor")
    return render_template('dof/quality_closure.html', dof=dof, form=form)

# DÖF View ve API rotaları - routes/dof.py
from flask import current_app

@dof_bp.route('/widget/dept_created')
@login_required
def dept_created_dofs_widget():
    """Departmanımın Açtığı DÖF'ler widget için veri sağlar"""
    try:
        current_app.logger.debug(f"Widget: Departmanımın açtığı DÖF'ler yükleniyor, kullanıcı={current_user.username}, rol={current_user.role}")
        
        # Kullanıcının departmanındaki tüm kullanıcıların oluşturduğu DÖF'leri getir
        if current_user.department_id:
            # Departmandaki tüm kullanıcıları bul
            dept_users = User.query.filter_by(department_id=current_user.department_id).all()
            dept_user_ids = [user.id for user in dept_users]
            
            # Bu kullanıcıların oluşturduğu DÖF'leri getir
            query = DOF.query.filter(DOF.created_by.in_(dept_user_ids)).order_by(DOF.created_at.desc())
        else:
            # Departmanı yoksa sadece kendi DÖF'lerini göster
            query = DOF.query.filter_by(created_by=current_user.id).order_by(DOF.created_at.desc())
        
        # Sayfalama yap
        page = request.args.get('page', 1, type=int)
        per_page = 5  # Her widget 5 kayıt göstersin
        dofs = query.paginate(page=page, per_page=per_page, error_out=False)
        
        current_app.logger.debug(f"Widget: {current_user.username} için {dofs.total} adet DÖF bulundu")
        
        # Widget için özel şablonu kullan
        return render_template('dof/partials/dof_widget_table.html', 
                            dofs=dofs, 
                            status=DOFStatus,
                            department=Department)
            
    except Exception as e:
        current_app.logger.error(f"Widget hatası: Departmanımın açtığı DÖF'ler: {str(e)}")
        return render_template('dof/partials/dof_list_error.html', error=str(e))

# DÖF ile ilgili API route'lar
@dof_bp.route('/api/change_department', methods=['POST'])
@login_required
def change_department_api():
    """Departman değişikliği API"""
    try:
        # Parametreleri al
        dof_id = request.form.get('dof_id')
        department_id = request.form.get('department_id')
        
        # Validasyon
        if not dof_id or not department_id:
            return jsonify({"error": "Eksik parametreler"}), 400
        
        # DÖF'u bul
        dof = DOF.query.get_or_404(int(dof_id))
        
        # Yetki kontrolü
        if not can_user_edit_dof(current_user, dof):
            return jsonify({"error": "Bu işlem için yetkiniz yok"}), 403
        
        # Departman kontrolü
        department = Department.query.get(int(department_id))
        if not department:
            return jsonify({"error": "Departman bulunamadı"}), 404
            
        # Değişiklik yapmadan önce aynı departman mı kontrol et
        if dof.department_id == int(department_id):
            return jsonify({
                "success": True,
                "message": "Departman zaten aynı, değişiklik yapılmadı."
            })
            
        # Departman güncelleme
        old_department_id = dof.department_id
        old_department_name = dof.department.name if dof.department else "Belirsiz"
        
        dof.department_id = int(department_id)
        dof.updated_at = datetime.now()
        
        # Aksiyon kaydı oluştur
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=3,  # 3: Atama tipi
            comment=f"Departman değiştirildi: {old_department_name} -> {department.name}"
        )
        db.session.add(action)
        
        # Bildirim gönder
        # Yeni departmanın yöneticilerine bildirim
        managers = User.query.filter_by(department_id=department_id, role=UserRole.DEPARTMENT_MANAGER).all()
        for manager in managers:
            notification = Notification(
                user_id=manager.id,
                dof_id=dof.id,
                message=f"DÖF #{dof.id} departmanınıza atandı."
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # Başarılı cevap dön
        return jsonify({
            'success': True, 
            'message': f"DÖF departmanı {department.name} olarak güncellendi.",
            'department': {
                'id': department.id,
                'name': department.name
            }
        })
        
    except Exception as e:
        # Hata durumunda işlemleri geri al
        db.session.rollback()
        current_app.logger.error(f"API - Departman güncelleme hatası: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# DÖF Listesi Excel indirme
@dof_bp.route('/dof/export/excel', methods=['GET'])
@login_required
def export_dofs_excel():
    # URL parametrelerini al
    status = request.args.get('status', type=int, default=0)
    department = request.args.get('department', type=int, default=0)
    keyword = request.args.get('keyword', default='')
    date_from = request.args.get('date_from', default='')
    date_to = request.args.get('date_to', default='')
    dof_type = request.args.get('dof_type', type=int, default=0)
    
    # Log filtresi
    current_app.logger.info(f"Excel dışa aktarma başlatıldı: status={status}, dept={department}, keyword={keyword}")
    
    # Filtreleme parametrelerini session'a kaydet
    session['last_dof_filter'] = {
        'status': status,
        'department': department,
        'keyword': keyword,
        'date_from': date_from,
        'date_to': date_to,
        'dof_type': dof_type
    }
    
    # DOF sorgusu başlat
    query = DOF.query
    
    # İlişkili DÖF'leri filtreleme
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    query = query.filter(related_dof_filter)
    current_app.logger.info("İlişkili DÖF'ler filtrelendi")
    
    # Durum filtresi
    if status != 0:
        query = query.filter(DOF.status == status)
        current_app.logger.info(f"Durum filtresi uygulandı: {status}")
    
    # Departman filtresi
    if department != 0:
        query = query.filter(DOF.department_id == department)
        current_app.logger.info(f"Departman filtresi uygulandı: {department}")
    
    # Anahtar kelime filtresi
    if keyword:
        query = query.filter(DOF.title.like(f'%{keyword}%') | DOF.description.like(f'%{keyword}%'))
        current_app.logger.info(f"Anahtar kelime filtresi uygulandı: {keyword}")
    
    # Tarih aralığı filtresi
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(DOF.created_at >= from_date)
            current_app.logger.info(f"Başlangıç tarihi filtresi uygulandı: {from_date}")
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı', 'warning')
            current_app.logger.error(f"Geçersiz başlangıç tarihi: {date_from}")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)  # Günün sonuna ayarla
            query = query.filter(DOF.created_at <= to_date)
            current_app.logger.info(f"Bitiş tarihi filtresi uygulandı: {to_date}")
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı', 'warning')
            current_app.logger.error(f"Geçersiz bitiş tarihi: {date_to}")
    
    # DOF tipi filtresi
    if dof_type != 0:
        query = query.filter(DOF.dof_type == dof_type)
        current_app.logger.info(f"DOF tipi filtresi uygulandı: {dof_type}")
    
    # Kullanıcı yetkisine göre filtrele
    if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        # Departman yöneticisi için genişletilmiş DOF erişimi
        # 1. Kendi departmanına ait tüm DOF'lar
        # 2. Departman çalışanları tarafından oluşturulan DOF'lar
        # 3. Departman çalışanlarına atanan DOF'lar
        dept_users = User.query.filter_by(department_id=current_user.department_id).with_entities(User.id).all()
        dept_user_ids = [u.id for u in dept_users]
        
        query = query.filter(
            or_(
                DOF.department_id == current_user.department_id,  # 1. Departmana ait DOF'lar
                DOF.created_by.in_(dept_user_ids),                # 2. Departman çalışanları tarafından oluşturulan
                DOF.assigned_to.in_(dept_user_ids)                # 3. Departman çalışanlarına atanan
            )
        )
        current_app.logger.info(f"Genişletilmiş departman yöneticisi filtresi uygulandı: dept_id={current_user.department_id}, dept_users={len(dept_user_ids)} kullanıcı")
    elif current_user.role == UserRole.USER:
        # Normal kullanıcı sadece kendi oluşturduğu veya kendisine atanan DOF'ları görebilir
        query = query.filter((DOF.created_by == current_user.id) | (DOF.assigned_to == current_user.id))
        current_app.logger.info(f"Normal kullanıcı filtresi uygulandı: user_id={current_user.id}")
    
    # Son sıralama
    query = query.order_by(DOF.created_at.desc())
    
    try:
        # Tüm DOF'ları al
        dofs = query.all()
        current_app.logger.info(f"Sorgu sonucu: {len(dofs)} DOF kaydı bulundu")
        
        # DOF kaydı yoksa hata mesajı göster
        if len(dofs) == 0:
            current_app.logger.warning("Seçilen filtrelere göre gösterilecek DOF kaydı bulunamadı")
            flash("Seçilen filtrelere göre gösterilecek DOF kaydı bulunamadı", "warning")
            return redirect(url_for('dof.list_dofs'))
        
        # Excel dosyasını oluştur
        try:
            current_app.logger.info("Excel dosyası oluşturuluyor...")
            excel_io = export_dofs_to_excel(dofs)
            current_app.logger.info("Excel dosyası başarıyla oluşturuldu!")
            
            # Dosyayı kullanıcıya gönder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return send_file(
                excel_io,
                as_attachment=True,
                download_name=f'DOF_Listesi_{timestamp}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            current_app.logger.error(f"Excel oluşturma hatası: {str(e)}")
            flash(f"Excel dosyası oluşturulurken hata oluştu: {str(e)}", "danger")
            return redirect(url_for('dof.list_dofs'))
    except Exception as e:
        current_app.logger.error(f"DOF sorgu hatası: {str(e)}")
        flash(f"DOF kayıtları alınırken hata oluştu: {str(e)}", "danger")
        return redirect(url_for('dof.list_dofs'))


# DOF Listesi PDF indirme
@dof_bp.route('/dof/export/pdf', methods=['GET'])
@login_required
def export_dofs_pdf():
    # URL parametrelerini al
    status = request.args.get('status', type=int, default=0)
    department = request.args.get('department', type=int, default=0)
    keyword = request.args.get('keyword', default='')
    date_from = request.args.get('date_from', default='')
    date_to = request.args.get('date_to', default='')
    dof_type = request.args.get('dof_type', type=int, default=0)
    
    # Log filtresi
    current_app.logger.info(f"PDF dışa aktarma başlatıldı: status={status}, dept={department}, keyword={keyword}")
    
    # Filtreleme parametrelerini session'a kaydet
    session['last_dof_filter'] = {
        'status': status,
        'department': department,
        'keyword': keyword,
        'date_from': date_from,
        'date_to': date_to,
        'dof_type': dof_type
    }
    
    # DOF sorgusu başlat
    query = DOF.query
    
    # İlişkili DÖF'leri filtreleme
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    query = query.filter(related_dof_filter)
    current_app.logger.info("İlişkili DÖF'ler filtrelendi")
    
    # Durum filtresi
    if status != 0:
        query = query.filter(DOF.status == status)
        current_app.logger.info(f"Durum filtresi uygulandı: {status}")
    
    # Departman filtresi
    if department != 0:
        query = query.filter(DOF.department_id == department)
        current_app.logger.info(f"Departman filtresi uygulandı: {department}")
    
    # Anahtar kelime filtresi
    if keyword:
        query = query.filter(DOF.title.like(f'%{keyword}%') | DOF.description.like(f'%{keyword}%'))
        current_app.logger.info(f"Anahtar kelime filtresi uygulandı: {keyword}")
    
    # Tarih aralığı filtresi
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(DOF.created_at >= from_date)
            current_app.logger.info(f"Başlangıç tarihi filtresi uygulandı: {from_date}")
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı', 'warning')
            current_app.logger.error(f"Geçersiz başlangıç tarihi: {date_from}")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)  # Günün sonuna ayarla
            query = query.filter(DOF.created_at <= to_date)
            current_app.logger.info(f"Bitiş tarihi filtresi uygulandı: {to_date}")
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı', 'warning')
            current_app.logger.error(f"Geçersiz bitiş tarihi: {date_to}")
    
    # DOF tipi filtresi
    if dof_type != 0:
        query = query.filter(DOF.dof_type == dof_type)
        current_app.logger.info(f"DOF tipi filtresi uygulandı: {dof_type}")
    
    # Kullanıcı yetkisine göre filtrele
    if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        # Departman yöneticisi kendi departmanına atanan DOF'ları ve departmanındaki
        # kullanıcıların oluşturduğu DOF'ları görebilir
        dept_users = db.session.query(User.id).filter(User.department_id == current_user.department_id).all()
        dept_user_ids = [u.id for u in dept_users]
        
        query = query.filter(
            (DOF.department_id == current_user.department_id) | 
            (DOF.created_by.in_(dept_user_ids)) | 
            (DOF.assigned_to.in_(dept_user_ids))
        )
        current_app.logger.info(f"Genişletilmiş departman yöneticisi filtresi uygulandı: dept_id={current_user.department_id}, dept_users={dept_user_ids}")
    elif current_user.role == UserRole.USER:
        # Normal kullanıcı sadece kendi oluşturduğu veya kendisine atanan DOF'ları görebilir
        query = query.filter((DOF.created_by == current_user.id) | (DOF.assigned_to == current_user.id))
        current_app.logger.info(f"Normal kullanıcı filtresi uygulandı: user_id={current_user.id}")
    
    # Son sıralama
    query = query.order_by(DOF.created_at.desc())
    
    try:
        # Tüm DOF'ları al
        dofs = query.all()
        current_app.logger.info(f"Sorgu sonucu: {len(dofs)} DOF kaydı bulundu")
        
        # DOF kaydı yoksa hata mesajı göster
        if len(dofs) == 0:
            current_app.logger.warning("Seçilen filtrelere göre gösterilecek DOF kaydı bulunamadı")
            flash("Seçilen filtrelere göre gösterilecek DOF kaydı bulunamadı", "warning")
            return redirect(url_for('dof.list_dofs'))
        
        # PDF dosyasını oluştur
        try:
            current_app.logger.info("PDF dosyası oluşturuluyor...")
            pdf_io = export_dofs_to_pdf(dofs)
            current_app.logger.info("PDF dosyası başarıyla oluşturuldu!")
            
            # Dosyayı kullanıcıya gönder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return send_file(
                pdf_io,
                as_attachment=True,
                download_name=f'DOF_Listesi_{timestamp}.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            current_app.logger.error(f"PDF oluşturma hatası: {str(e)}")
            flash(f"PDF dosyası oluşturulurken hata oluştu: {str(e)}", "danger")
            return redirect(url_for('dof.list_dofs'))
    except Exception as e:
        current_app.logger.error(f"DOF sorgu hatası: {str(e)}")
        flash(f"DOF kayıtları alınırken hata oluştu: {str(e)}", "danger")
        return redirect(url_for('dof.list_dofs'))

# DÖF ile ilgili route'lar
@dof_bp.route('/dof/list')
@login_required
def list_dofs():
    # DÖF'leri listeleme sayfası
    # Performans ölçümü
    start_time = time.time()
    
    # AJAX isteği kontrolü
    is_ajax = request.args.get('ajax', type=int, default=0) == 1
    
    form = SearchForm(request.args)
    
    # Departman seçeneklerini al
    departments = Department.query.all()
    
    # Filtreleri uygula
    query = DOF.query
    status_param = request.args.get('status')
    dept_id = request.args.get('department', type=int)
    search_term = request.args.get('search_term', '')
    
    # Dashboard'dan gelen özel filtreler
    active_only = request.args.get('active_only', type=int)
    pending_approval = request.args.get('pending_approval', type=int)
    
    if search_term:
        query = query.filter(or_(DOF.title.like(search_term), DOF.description.like(search_term)))
    
    # Dashboard özel filtreleri
    if active_only == 1:
        # Devam eden DÖF'ler: Taslak hariç tüm açık durumlar
        active_statuses = [DOFStatus.SUBMITTED, DOFStatus.IN_REVIEW, DOFStatus.ASSIGNED, 
                          DOFStatus.IN_PROGRESS, DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION, 
                          DOFStatus.COMPLETED, DOFStatus.SOURCE_REVIEW]
        query = query.filter(DOF.status.in_(active_statuses))
    elif pending_approval == 1:
        # Çözülmeyi bekleyen: Onay bekleyen durumlar
        pending_statuses = [DOFStatus.SUBMITTED, DOFStatus.IN_REVIEW, DOFStatus.PLANNING, 
                           DOFStatus.COMPLETED, DOFStatus.SOURCE_REVIEW]
        query = query.filter(DOF.status.in_(pending_statuses))
    elif status_param:
        # Çoklu status desteği: "1,2" formatında gelebilir
        if ',' in status_param:
            try:
                status_list = [int(s.strip()) for s in status_param.split(',') if s.strip().isdigit()]
                if status_list:
                    query = query.filter(DOF.status.in_(status_list))
            except ValueError:
                pass  # Hatalı format durumunda filtreleme yapma
        elif status_param.isdigit() and int(status_param) != 0:
            query = query.filter_by(status=int(status_param))
    
    # Departman filtresi
    try:
        if request.args.get('department'):
            dept_param = request.args.get('department')
            # Eğer string olarak geldiyse ve sayı ise
            if isinstance(dept_param, str) and dept_param.isdigit() and int(dept_param) > 0:
                query = query.filter_by(department_id=int(dept_param))
            # Eğer doğrudan sayı olarak geldiyse
            elif isinstance(dept_param, int) and dept_param > 0:
                query = query.filter_by(department_id=dept_param)
    except Exception as e:
        current_app.logger.error(f"Departman filtreleme hatası: {str(e)}")
        
    # Oluşturan kişinin departmanına göre filtreleme
    try:
        if request.args.get('created_dept'):
            created_dept = request.args.get('created_dept')
            # Eğer string olarak geldiyse ve sayı ise
            if isinstance(created_dept, str) and created_dept.isdigit() and int(created_dept) > 0:
                dept_id = int(created_dept)
            # Eğer doğrudan sayı olarak geldiyse
            elif isinstance(created_dept, int) and created_dept > 0:
                dept_id = created_dept
            else:
                dept_id = None
                
            if dept_id:
                # Kullanıcıların departmanına göre filtreleme yapmak için
                # önce o departmana ait tüm kullanıcıları bul
                dept_users = User.query.filter_by(department_id=dept_id).all()
                dept_user_ids = [user.id for user in dept_users]
                
                # Departmandaki kullanıcıların oluşturduğu DÖF'leri filtrele
                if dept_user_ids:
                    query = query.filter(DOF.created_by.in_(dept_user_ids))
    except Exception as e:
        current_app.logger.error(f"Oluşturan departman filtreleme hatası: {str(e)}")
    
    # Tarih filtrelerini güvenli bir şekilde işle
    if request.args.get('date_from') and request.args.get('date_from').strip():
        try:
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
            query = query.filter(DOF.created_at >= date_from)
        except ValueError:
            flash('Başlangıç tarihi formatı hatalı. Lütfen geçerli bir tarih seçin.', 'warning')
    
    if request.args.get('date_to') and request.args.get('date_to').strip():
        try:
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
            # Bitiş tarihi için günün sonuna kadar tüm kayıtları dahil et
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(DOF.created_at <= date_to)
        except ValueError:
            flash('Bitiş tarihi formatı hatalı. Lütfen geçerli bir tarih seçin.', 'warning')
    
    # Yetkilendirme kontrolü - Merkezi AuthService ile kullanıcı yetki filtrelemesi uygula
    # Bu sayede tüm yetki kontrolleri tek merkezden ve tutarlı şekilde yapılır
    try:
        # AuthService'i içe aktar
        from auth_service import AuthService
        
        current_app.logger.info(f"DÖF listesi için AuthService filtrelemesi uygulanıyor: Kullanıcı={current_user.username}, Rol={current_user.role}")
        
        # Mevcut sorguyu AuthService ile filtrele
        query = AuthService.filter_viewable_dofs(current_user, query)
        
        # Departman seçilmişse, bu departmanı görüntüleme yetkisi kontrolü
        if dept_id and dept_id > 0 and current_user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            managed_departments = current_user.get_managed_departments()
            managed_dept_ids = [dept.id for dept in managed_departments]
            
            # Eğer seçilen departman yönetilen departmanlar listesinde değilse, kullanıcıyı bilgilendir
            if dept_id not in managed_dept_ids:
                flash('Bu departmanın DÖF\'lerini görüntüleme yetkiniz bulunmuyor.', 'warning')
                # AuthService ile filtrelenmiş sorguya devam edecek, zaten gereksiz DÖF'leri göstermeyecek
    except Exception as e:
        current_app.logger.error(f"DÖF listeleme yetkilendirme hatası: {str(e)}")
        # Hata durumunda güvenli tarafta kal - boş sorgu göster
        query = query.filter(DOF.id == -1)  # Hiçbir sonuç gösterme
    
    # Sıralama ve sayfalama
    page = request.args.get('page', 1, type=int)
    per_page = 5 if is_ajax else 10  # AJAX için daha az sayıda DÖF göster
    dofs = query.order_by(DOF.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Performans ölçümü bitiş
    end_time = time.time()
    process_time = round((end_time - start_time) * 1000)  # milisaniye cinsinden
    current_app.logger.info(f"DÖF listeleme süresi: {process_time}ms, AJAX: {is_ajax}")
    
    # AJAX isteği ise basitleştirilmiş şablon döndür
    if is_ajax:
        return render_template('dof/partials/dof_list_table.html', 
                              dofs=dofs,
                              status=DOFStatus,
                              department=Department)
    
    # Normal sayfa gösterimi
    return render_template('dof/list.html', 
                          dofs=dofs, 
                          form=form, 
                          status=DOFStatus, 
                          department=Department)

@dof_bp.route('/dof/<int:dof_id>')
@login_required
def detail(dof_id):
    dof = DOF.query.get_or_404(dof_id)
    
    # DÖF düzenleme yetkisi kontrol et
    can_edit = can_user_edit_dof(current_user, dof)
    
    # İş akışı durumunu kontrol et
    workflow_step = None
    
    # Kullanıcı rolüne DÖF durumuna göre sonraki adımı belirle
    if current_user.role == UserRole.ADMIN or current_user.role == UserRole.QUALITY_MANAGER:
        # Kalite yöneticisi ve Admin için her zaman workflow_step ayarla
        # tüm durumlarda kontrol için
        workflow_step = "quality_review"
    # Departman yöneticilerinin ve franchise departman yöneticilerinin atanan DÖF'ü çözme yetkisi - departman eşleşmesi yeterli
    elif current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        # Eğer DÖF'ün departman adı ile kullanıcının departman adı eşleşirse çözüm butonu göster
        if dof.department and current_user.department:
            if dof.department.name == current_user.department.name:
                workflow_step = "department_action"
                # Debug mesajı
                print(f"Departman eşleşmesi bulundu: {dof.department.name}, durum: {dof.status}")
    
    # Aksiyonları getir
    actions = DOFAction.query.filter_by(dof_id=dof_id).order_by(DOFAction.created_at.desc()).all()
    
    # DZ değişkeni - termin tarihi hesaplaması için
    now = datetime.now()
    
    # Tarih hesaplaması için timedelta'yı template'e aktar
    time_delta = timedelta
    
    # Dosya eklerini getir
    attachments = Attachment.query.filter_by(dof_id=dof_id).all()
    
    # Son güncelleme tarihi
    last_update = dof.updated_at
    if actions and actions[0].created_at > last_update:
        last_update = actions[0].created_at
    
    # Kaynak departman bilgisini al
    creator_dept = User.query.get(dof.created_by).department
    source_department = creator_dept.name if creator_dept else "Belirsiz"
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="DÖF Görüntüleme",
        details=f"DÖF görüntülendi: {dof.title}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    # Aksiyon formu oluştur
    form = DOFActionForm()
    
    return render_template('dof/detail.html', 
                           dof=dof, 
                           actions=actions,
                           attachments=attachments,
                           last_update=last_update,
                           can_edit=can_edit,
                           workflow_step=workflow_step,
                           source_department=source_department,
                           status=DOFStatus,
                           form=form,
                           now=datetime.now(),
                           timedelta=timedelta,
                           title="DÖF Detayı")

@dof_bp.route('/dof/<int:dof_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_dof(dof_id):
    dof = DOF.query.get_or_404(dof_id)
    
    # Kullanıcının düzenleme yetkisi kontrol
    if not can_user_edit_dof(current_user, dof):
        abort(403)
        
    # Form oluştur - form tipini 'edit' olarak belirt ve mevcut kullanıcıyı gönder
    form = DOFForm(form_type='edit', current_user=current_user)
    
    # GET request için form verilerini manuel olarak doldur
    if request.method == 'GET':
        form.title.data = dof.title
        form.description.data = dof.description
        form.dof_type.data = dof.dof_type
        form.dof_source.data = dof.dof_source
        form.department.data = dof.department_id if dof.department_id else 0
        form.due_date.data = dof.due_date
        # Müşteri şikayeti alanları
        form.channel.data = dof.channel if dof.channel else ''
        form.complaint_date.data = dof.complaint_date
    
    if form.validate_on_submit():
        # Değişen alanları izlemek için eski değerleri sakla
        old_values = {
            'title': dof.title,
            'description': dof.description,
            'department_id': dof.department_id,
            'due_date': dof.due_date,
            'dof_type': dof.dof_type,
            'dof_source': dof.dof_source,
            'channel': dof.channel,
            'complaint_date': dof.complaint_date
        }
        
        # Termin tarihini sakla - değiştirilmemesi lazım (edit sırasında değişmemeli)
        existing_due_date = dof.due_date
        
        # Formdaki değerleri güvenli şekilde DÖF nesnesine aktar
        dof.title = form.title.data
        dof.description = form.description.data
        dof.dof_type = form.dof_type.data
        dof.dof_source = form.dof_source.data
        
        # Departman güncelleme (sadece geçerli değerler için)
        if form.department.data and form.department.data != 0:
            dof.department_id = form.department.data
            
        # Müşteri şikayeti alanları
        if form.dof_source.data == 3:  # DOFSource.CUSTOMER_COMPLAINT
            dof.channel = form.channel.data if form.channel.data else None
            dof.complaint_date = form.complaint_date.data if form.complaint_date.data else None
        else:
            dof.channel = None
            dof.complaint_date = None
        
        # Termin tarihini geri yükle - edit sırasında değişmemeli
        dof.due_date = existing_due_date
        
        # Değişen alanları belirle
        changed_fields = []
        changes_details = []
        
        if old_values['title'] != dof.title:
            changed_fields.append('Başlık')
            changes_details.append(f"Başlık: '{old_values['title']}' -> '{dof.title}'")
            
        if old_values['description'] != dof.description:
            changed_fields.append('Açıklama')
            changes_details.append("Açıklama güncellendi")
            
        # Priority kontrolü kaldırıldı - öncelik alanı artık yok
        # if old_values['priority'] != dof.priority:
        #     changed_fields.append('Öncelik')
        #     old_priority = 'Düşük' if old_values['priority'] == 1 else 'Orta' if old_values['priority'] == 2 else 'Yüksek'
        #     new_priority = 'Düşük' if dof.priority == 1 else 'Orta' if dof.priority == 2 else 'Yüksek'
        #     changes_details.append(f"Öncelik: {old_priority} -> {new_priority}")
            
        if old_values['department_id'] != dof.department_id:
            changed_fields.append('Departman')
            try:
                old_dept = Department.query.get(old_values['department_id']).name if old_values['department_id'] else '-'
                new_dept = Department.query.get(dof.department_id).name if dof.department_id else '-'
                changes_details.append(f"Departman: {old_dept} -> {new_dept}")
                
                # Departman değiştiyse, eski departman yöneticisini bilgilendir
                if old_values['department_id'] and old_values['department_id'] != dof.department_id:
                    notify_for_dof(dof, "department_changed", current_user, {
                        'old_department_id': old_values['department_id'],
                        'new_department_id': dof.department_id
                    })
            except Exception as e:
                current_app.logger.error(f"Department update error: {str(e)}")
                changes_details.append("Departman bilgisi güncellenirken hata oluştu")
            
        # Due date edit sırasında değiştirilmemeli, bu kontrolü kaldırdık
        # if old_values['due_date'] != dof.due_date:
        #     changed_fields.append('Son Tarih')
        #     old_date = old_values['due_date'].strftime('%d.%m.%Y') if old_values['due_date'] else '-'
        #     new_date = dof.due_date.strftime('%d.%m.%Y') if dof.due_date else '-'
        #     changes_details.append(f"Son Tarih: {old_date} -> {new_date}")
            
        # Deadline ve solution_plan kontrolleri artık yok (old_values'da yok)
        # if old_values['deadline'] != dof.deadline:
        #     new_date = dof.deadline.strftime('%d.%m.%Y') if dof.deadline else '-'
        #     changes_details.append(f"Termin: {old_date} -> {new_date}")
            
        # if old_values['solution_plan'] != dof.solution_plan:
        #     changed_fields.append('Çözüm Planı')
        #     changes_details.append("Çözüm planı güncellendi")
        
        if old_values['dof_type'] != dof.dof_type:
            changed_fields.append('DÖF Türü')
            changes_details.append(f"DÖF Türü değiştirildi")
            
        if old_values['dof_source'] != dof.dof_source:
            changed_fields.append('DÖF Kaynağı')
            changes_details.append(f"DÖF Kaynağı değiştirildi")
            
        # Müşteri şikayeti alanları kontrolü
        if old_values['channel'] != dof.channel:
            changed_fields.append('Şikayet Kanalı')
            changes_details.append(f"Şikayet Kanalı güncellendi")
            
        if old_values['complaint_date'] != dof.complaint_date:
            changed_fields.append('Şikayet Tarihi')
            changes_details.append(f"Şikayet Tarihi güncellendi")
            
        # Güncelleme tarihini ayarla
        dof.updated_at = datetime.now()
        
        # Dosya eklerini işle
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                file_data = save_file(file)
                
                attachment = Attachment(
                    dof_id=dof.id,
                    filename=file_data['filename'],
                    file_path=file_data['file_path'],
                    file_size=file_data['file_size'],
                    file_type=file_data['file_type'],
                    uploaded_by=current_user.id,
                    uploaded_at=datetime.now()
                )
                
                db.session.add(attachment)
                changed_fields.append('Dosya Eki')
                changes_details.append(f"Yeni dosya eklendi: {file_data['filename']}")
        
        # Değişiklik olduysa aktivite kaydı oluştur
        if changed_fields:
            from models import UserActivity
            change_description = f"Güncellenen alanlar: {', '.join(changed_fields)}\n\n{' | '.join(changes_details)}"
            
            # Değişiklik aktivitesini kaydet
            activity = UserActivity(
                user_id=current_user.id,
                activity_type='update_dof',
                description=change_description,
                related_id=dof.id,
                created_at=datetime.now()
            )
            db.session.add(activity)
            
            # Bildirim gönder
            notify_for_dof(dof, "update", current_user)
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        flash('DÖF başarıyla güncellendi.', 'success')
        return redirect(url_for('dof.detail', dof_id=dof.id))
    
    # GET isteği veya validasyon hatası durumunda form göster
    return render_template('dof/edit.html', form=form, dof=dof)

@dof_bp.route('/dof/<int:dof_id>/action', methods=['POST'])
@login_required
def add_dof_action(dof_id):
    try:
        current_app.logger.info(f"DÖF Aksiyon Ekleme Başlatıldı - DÖF ID: {dof_id}, Kullanıcı: {current_user.full_name} (Rol: {current_user.role})")
        
        dof = DOF.query.get_or_404(dof_id)
        current_app.logger.info(f"DÖF bulundu: #{dof.id} - {dof.title} (Durum: {dof.status})")
        
        # Kullanıcının erişim yetkisi kontrol
        if not can_user_edit_dof(current_user, dof):
            current_app.logger.warning(f"Erişim reddedildi - Kullanıcı: {current_user.full_name}, DÖF: {dof_id}")
            abort(403)
            
        current_app.logger.info("Yetki kontrolü başarılı")
    except Exception as e:
        current_app.logger.error(f"DÖF Aksiyon Ekleme Başlangıç Hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Sistem hatası: {str(e)}", "danger")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Eğer DÖF kapatılmış veya reddedilmişse aksiyon eklenemez
    if dof.status in [DOFStatus.CLOSED, DOFStatus.REJECTED]:
        flash('Kapatılmış veya reddedilmiş DÖF\'e aksiyon eklenemez.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    try:
        current_app.logger.info("Form oluşturuluyor...")
        form = DOFActionForm(dof_status=dof.status)
        current_app.logger.info("Form oluşturuldu")
        
        current_app.logger.info(f"Form validation başlıyor - Form data: {request.form}")
        form_valid = form.validate_on_submit()
        current_app.logger.info(f"Form validation sonucu: {form_valid}")
        
        if not form_valid:
            current_app.logger.warning(f"Form validation hatası: {form.errors}")
    except Exception as e:
        current_app.logger.error(f"Form işleme hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Form hatası: {str(e)}", "danger")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    if form.validate_on_submit():
        # Durum değişikliği
        old_status = dof.status
        new_status = None
        
        # Kök neden ve aksiyon planı girişi kontrolü - ASSIGNED durumundan PLANNING durumuna geçiş
        if old_status == DOFStatus.ASSIGNED and form.comment.data and form.root_cause.data and form.resolution_plan.data:
            # Departman kök neden ve aksiyon planlarını giriyor
            dof.root_cause = form.root_cause.data
            dof.resolution_plan = form.resolution_plan.data
            
            # Plan kaydedildi, PLANNING durumuna geçiş
            new_status = DOFStatus.PLANNING
            dof.status = new_status
            flash('Kök neden ve aksiyon planı kaydedildi. Kalite incelemesi bekleniyor.', 'success')
        
        elif form.new_status.data:
            # Atanan departman yöneticileri - doğrudan aksiyon planı sonrası tamamlandı yapabilirler
            if form.new_status.data == 10 and dof.status in [8, 9] and current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER \
                    and current_user.department and dof.department \
                    and current_user.department.id == dof.department.id:
                new_status = 10  # COMPLETED - Tamamlandı
                dof.status = new_status
            # Kaynak departmanı için memnuniyet sorgusu - SADECE SOURCE_REVIEW durumunda kontrol et
            if dof.status == DOFStatus.SOURCE_REVIEW and form.new_status.data == DOFStatus.RESOLVED:
                # DöF status 11'den 5'e (RESOLVED) geçiyorsa kaynak memnuniyet kontrolü yap
                is_source_satisfied = (request.form.get('is_source_satisfied') == 'yes')
                                      
                current_app.logger.info(f"DÖF #{dof_id} için kaynak memnuniyet kontrolü: {is_source_satisfied}")
                
                if not is_source_satisfied:
                    # Yorum alanı boş ise hata dön
                    if not form.comment.data or form.comment.data.strip() == "":
                        flash('Memnun olmama sebebinizi açıklamanız zorunludur. Lütfen yorum ekleyin.', 'danger')
                        return redirect(url_for('dof.detail', dof_id=dof_id))
                        
                    # Kaynak departman memnun değil, özel durum işleyelim
                    new_status = DOFStatus.RESOLVED  # Çözüldü durumuna geç
                    dof.status = new_status
                    # Yoruma özel bir not ekleyelim
                    form.comment.data = f"[KAYNAK MEMNUN DEĞİL] {form.comment.data}"
                    flash('DÖF çözümünden memnun değilsiniz. Süreç Kalite departmanının değerlendirmesi için ilerleyecek.', 'warning')
                else:
                    # Kaynak departman memnun, normal durum değişikliği
                    new_status = form.new_status.data
                    dof.status = new_status
            # Normal durum değişiklik kontrolü (diğer tüm durumlar için)
            elif not can_user_change_status(current_user, dof, form.new_status.data):
                flash('Bu durum değişikliğini yapma yetkiniz yok.', 'danger')
                return redirect(url_for('dof.detail', dof_id=dof_id))
            else:
                new_status = form.new_status.data
                dof.status = new_status
            
            # Eğer kapatılıyorsa, kapatılma tarihini ayarla
            if new_status == DOFStatus.CLOSED:
                dof.closed_at = datetime.now()
        
        # Atama değişikliği
        if form.assigned_to.data and form.assigned_to.data != 0:
            dof.assigned_to = form.assigned_to.data
        
        dof.updated_at = datetime.now()
        
        # Aksiyonu kaydet
        try:
            current_app.logger.info("DOFAction oluşturuluyor...")
            action = DOFAction(
                dof_id=dof.id,
                user_id=current_user.id,
                action_type=3 if new_status else 1,  # 3: Durum Değişikliği, 1: Yorum
                comment=form.comment.data,
                old_status=old_status if new_status else None,
                new_status=new_status,
                created_at=datetime.now()
            )
            current_app.logger.info("DOFAction oluşturuldu")
            
            db.session.add(action)
            current_app.logger.info("DOFAction session'a eklendi")
            
            db.session.flush()  # Action ID'sini almak için flush
            current_app.logger.info(f"DOFAction flush yapıldı - Action ID: {action.id}")
        except Exception as e:
            current_app.logger.error(f"DOFAction oluşturma hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
            flash(f"Aksiyon kaydetme hatası: {str(e)}", "danger")
            return redirect(url_for('dof.detail', dof_id=dof_id))
        
        # DÖF'e eklenen dosyaları işle (eski sistem)
        try:
            files = request.files.getlist('files')
            if files:
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            file_data = save_file(file)
                            
                            attachment = Attachment(
                                dof_id=dof.id,
                                filename=file_data['filename'],
                                file_path=file_data['file_path'],
                                file_size=file_data['file_size'],
                                file_type=file_data['file_type'],
                                uploaded_by=current_user.id,
                                uploaded_at=datetime.now()
                            )
                            
                            db.session.add(attachment)
                            current_app.logger.info(f"DÖF attachment eklendi: {file_data['filename']}")
                            
                        except Exception as e:
                            current_app.logger.error(f"DÖF attachment kaydetme hatası: {str(e)}")
                            # Hata durumunda devam et, diğer dosyaları engelleme
        except Exception as e:
            current_app.logger.error(f"DÖF files işleme hatası: {str(e)}")
            # Dosya yükleme hatalarını yok sayıp yorum eklemeye devam et
                
        # Yorum eklerini işle (yeni sistem)
        try:
            action_files = request.files.getlist('action_files')
            if action_files:
                for file in action_files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            file_data = save_file(file)
                            
                            action_attachment = ActionAttachment(
                                action_id=action.id,
                                filename=file_data['filename'],
                                file_path=file_data['file_path'],
                                file_size=file_data['file_size'],
                                file_type=file_data['file_type'],
                                uploaded_by=current_user.id,
                                uploaded_at=datetime.now()
                            )
                            
                            db.session.add(action_attachment)
                            current_app.logger.info(f"Action attachment eklendi: {file_data['filename']}")
                            
                        except Exception as e:
                            current_app.logger.error(f"Action attachment kaydetme hatası: {str(e)}")
                            # Hata durumunda devam et, diğer dosyaları engelleme
        except Exception as e:
            current_app.logger.error(f"Action files işleme hatası: {str(e)}")
            # Dosya yükleme hatalarını yok sayıp yorum eklemeye devam et
        
        try:
            current_app.logger.info("Veritabanı commit işlemi başlıyor...")
            db.session.commit()
            current_app.logger.info("Veritabanı commit işlemi tamamlandı")
        except Exception as e:
            current_app.logger.error(f"Veritabanı commit hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
            flash(f"Veritabanı kaydetme hatası: {str(e)}", "danger")
            return redirect(url_for('dof.detail', dof_id=dof_id))
        
        # Aktivite kaydı ve bildirim oluştur
        from models import UserActivity
        activity_type = ''
        activity_description = ''
        notification_type = ''
        
        if new_status:
            # Durum değişikliği
            old_status_label = DOFStatus.get_label(old_status) if hasattr(DOFStatus, 'get_label') else str(old_status)
            new_status_label = DOFStatus.get_label(new_status) if hasattr(DOFStatus, 'get_label') else str(new_status)
            
            activity_type = 'status_change'
            activity_description = f"DÖF durumu değiştirildi: {old_status_label} -> {new_status_label}"
            
            if form.comment.data:
                activity_description += f"\n\nAçıklama: {form.comment.data}"
                
            notification_type = "status_change"
            
        elif form.assigned_to.data and form.assigned_to.data != 0:
            # Atama değişikliği
            assigned_user = User.query.get(form.assigned_to.data)
            activity_type = 'assign'
            activity_description = f"DÖF ataması yapıldı: {assigned_user.fullname if assigned_user else 'Bilinmeyen Kullanıcı'}"
            
            if form.comment.data:
                activity_description += f"\n\nAçıklama: {form.comment.data}"
                
            notification_type = "assign"
            
        else:
            # Yorum ekleme
            activity_type = 'comment'
            activity_description = f"DÖF'e yorum eklendi: {form.comment.data[:100]}{'...' if len(form.comment.data) > 100 else ''}"
            notification_type = "comment"
        
        # Aktivite kaydını oluştur
        activity = UserActivity(
            user_id=current_user.id,
            activity_type=activity_type,
            description=activity_description,
            related_id=dof.id,
            created_at=datetime.now()
        )
        db.session.add(activity)
        
        # Bildirim gönder
        notify_for_dof(dof, notification_type, current_user)
        
        # Log kaydı oluştur
        if new_status:
            # Durumların string karşılıklarını belirle
            old_status_name = "Bilinmiyor"
            new_status_name = "Bilinmiyor"
            
            # Eski durum adını belirle
            if old_status == DOFStatus.DRAFT:
                old_status_name = "Taslak"
            elif old_status == DOFStatus.SUBMITTED:
                old_status_name = "Gönderildi"
            elif old_status == DOFStatus.IN_REVIEW:
                old_status_name = "İncelemede"
            elif old_status == DOFStatus.ASSIGNED:
                old_status_name = "Atandı"
            elif old_status == DOFStatus.IN_PROGRESS:
                old_status_name = "Devam Ediyor"
            elif old_status == DOFStatus.RESOLVED:
                old_status_name = "Çözüldü"
            elif old_status == DOFStatus.CLOSED:
                old_status_name = "Kapatıldı"
            elif old_status == DOFStatus.REJECTED:
                old_status_name = "Reddedildi"
            
            # Yeni durum adını belirle
            if new_status == DOFStatus.DRAFT:
                new_status_name = "Taslak"
            elif new_status == DOFStatus.SUBMITTED:
                new_status_name = "Gönderildi"
            elif new_status == DOFStatus.IN_REVIEW:
                new_status_name = "İncelemede"
            elif new_status == DOFStatus.ASSIGNED:
                new_status_name = "Atandı"
            elif new_status == DOFStatus.IN_PROGRESS:
                new_status_name = "Devam Ediyor"
            elif new_status == DOFStatus.RESOLVED:
                new_status_name = "Çözüldü"
            elif new_status == DOFStatus.CLOSED:
                new_status_name = "Kapatıldı"
            elif new_status == DOFStatus.REJECTED:
                new_status_name = "Reddedildi"
            
            log_activity(
                user_id=current_user.id,
                action="DÖF Durum Değişikliği",
                details=f"DÖF durumu değiştirildi: {dof.title} - {old_status_name} -> {new_status_name}",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
        else:
            log_activity(
                user_id=current_user.id,
                action="DÖF Aksiyon Ekleme",
                details=f"DÖF'e aksiyon eklendi: {dof.title}",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
        
        flash('Aksiyon başarıyla eklendi.', 'success')
        return redirect(url_for('dof.detail', dof_id=dof.id))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('dof.detail', dof_id=dof_id))

@dof_bp.route('/dof/<int:dof_id>/resolve', methods=['GET', 'POST'])
@login_required
@optimize_db_operations
def resolve_dof(dof_id):
    # DÖF çözüm planı ve kök neden analizi ekleme sayfası
    start_time = time.time()  # Performans ölçümü başlat
    dof = DOF.query.get_or_404(dof_id)
    
    # Kullanıcı yetkisini kontrol et - sadece departman yöneticileri ve adminler
    if current_user.role not in [UserRole.DEPARTMENT_MANAGER, UserRole.ADMIN]:
        flash('Sadece departman yöneticileri veya admin kullanıcılar DÖF çözüm planı girebilir.', 'warning')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Debug bilgisi
    print(f"Kullanıcı rolü: {current_user.role}, DÖF ID: {dof_id}, DÖF durumu: {dof.status}")
    
    # DÖF durumu ne olursa olsun, form ekranına yönlendirilir ve güncelleme form gönderildiğinde yapılır
    # 'ATANDI' durumundaki döfler için kural yok, herhangi bir departman yöneticisi işlem yapabilir
    
    # Çözüm formu
    form = DOFResolveForm()
    
    # GET isteğinde mevcut değerlerle formu doldur
    if request.method == 'GET':
        # Mevcut değerler varsa formu doldur
        if dof.root_cause1:
            form.root_cause1.data = dof.root_cause1
        if dof.root_cause2:
            form.root_cause2.data = dof.root_cause2
        if dof.root_cause3:
            form.root_cause3.data = dof.root_cause3
        if dof.root_cause4:
            form.root_cause4.data = dof.root_cause4
        if dof.root_cause5:
            form.root_cause5.data = dof.root_cause5
        if dof.deadline:
            form.deadline.data = dof.deadline
        if dof.action_plan:
            form.action_plan.data = dof.action_plan
    
    # POST isteği ve form doğrulama işlemi
    if request.method == 'POST':
        print(f"POST isteği alındı - form onay: {form.validate()}")
        # Form hatalarını göster
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", 'danger')
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            return render_template('dof/resolve.html', 
                           dof=dof,
                           form=form,
                           status=DOFStatus,
                           title="DÖF Çözüm Planı",
                           today_date=today)
        
    # Form doğrulandı
    if form.validate_on_submit():
        # Kök neden analizlerini kaydet
        dof.root_cause1 = form.root_cause1.data
        dof.root_cause2 = form.root_cause2.data
        dof.root_cause3 = form.root_cause3.data
        dof.root_cause4 = form.root_cause4.data
        dof.root_cause5 = form.root_cause5.data
        
        # Termin tarihi ve aksiyon planını kaydet
        dof.deadline = form.deadline.data
        dof.action_plan = form.action_plan.data
        
        # Değişken tanımlamaları
        status_change = False
        old_status = dof.status
        
        # Durum kontrolü ve geçişler
        if dof.status == DOFStatus.ASSIGNED:
            # Yeni akış: Atandı -> Planlama aşaması
            dof.status = DOFStatus.PLANNING 
            status_change = True
            old_status = DOFStatus.ASSIGNED
            
            # Kök neden ve aksiyon planı girildikten sonra kalite departmanına bildirim gönder
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
            for manager in quality_managers:
                notification = Notification(
                    user_id=manager.id,
                    dof_id=dof.id,
                    message=f"DÖF #{dof.id} için kök neden analizi ve aksiyon planı hazırlandı. İncelemeniz gerekiyor."
                )
                db.session.add(notification)
                
            flash("DÖF kök neden analizi ve aksiyon planı kaydedildi. Kalite departmanı incelemesi bekleniyor.", "success")
            
        elif dof.status == DOFStatus.PLANNING:
            # PLANNING durumundan revize sonrası tekrar PLANNING'e geçiş
            # Bu durumda DÖF zaten PLANNING durumunda olduğu için durum değişikliği yok ama bildirim gönder
            status_change = False  # Durum aynı kalıyor
            old_status = DOFStatus.PLANNING
            
            # Kök neden ve aksiyon planı revize edildikten sonra kalite departmanına tekrar bildirim gönder
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
            for manager in quality_managers:
                notification = Notification(
                    user_id=manager.id,
                    dof_id=dof.id,
                    message=f"DÖF #{dof.id} için kök neden analizi ve aksiyon planı revize edildi. Tekrar incelemeniz gerekiyor."
                )
                db.session.add(notification)
                
            flash("DÖF kök neden analizi ve aksiyon planı revize edildi. Kalite departmanı incelemesi bekleniyor.", "success")
            
        elif dof.status == DOFStatus.IMPLEMENTATION:
            # Uygulama aşamasından Tamamlandı aşamasına geçiş
            action_value = request.form.get('action', '')
            if action_value == 'complete':
                dof.status = DOFStatus.COMPLETED
                status_change = True
                old_status = DOFStatus.IMPLEMENTATION
                
                # Kaynak departmana bildirim gönder (DÖF oluşturan kişinin departmanı)
                if dof.creator and dof.creator.department_id:
                    managers = User.query.filter_by(department_id=dof.creator.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
                    for manager in managers:
                        notification = Notification(
                            user_id=manager.id,
                            dof_id=dof.id,
                            message=f"DÖF #{dof.id} için yapılan aksiyonlar tamamlandı. İncelemeniz ve onaylamanız gerekiyor."
                        )
                        db.session.add(notification)
                        
                flash("DÖF aksiyonları tamamlandı olarak işaretlendi. Kaynak departmanın onayı bekleniyor.", "success")
        else:
            # Diğer durumlar için durum değişikliği yok, sadece güncelleme
            status_change = False
            flash("DÖF kök neden analizi ve aksiyon planı güncellendi.", "success")
        
        dof.updated_at = datetime.now()
        
        # Aksiyonu kaydet
        # PLANNING durumunda revizyon için özel yorum oluştur
        if dof.status == DOFStatus.PLANNING and old_status == DOFStatus.PLANNING:
            comment_text = "Kök neden analizi ve aksiyon planı revize edildi. " + (form.comment.data or "")
        else:
            comment_text = form.comment.data
            
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=2 if status_change else 1,  # 2: Durum Değişikliği, 1: Yorum/Güncelleme
            comment=comment_text,
            old_status=old_status if status_change else None,
            new_status=dof.status if status_change else None,
            created_at=datetime.now()
        )
        
        db.session.add(action)
        db.session.commit()
        
        # DÖF oluşturma işleminde Kalite Yöneticisi tarafından oluşturulan DÖF'ler için aksiyon kaydı ekleyelim
        # created_by_role yerine created_by alanını kullanıp kullanıcının rolünü kontrol edelim
        creator = User.query.get(dof.created_by)
        if creator and creator.role == UserRole.QUALITY_MANAGER:
            dof_action = DOFAction(
                dof_id=dof.id,
                user_id=current_user.id,
                action_type=DOFActionType.NEW_DOF,
                comment=f"Yeni DÖF oluşturuldu: {dof.title}"
            )
            db.session.add(dof_action)
            db.session.commit()
        
        # Performans ölçümü
        commit_time = time.time()
        commit_duration = round((commit_time - start_time) * 1000)  # milisaniye cinsinden
        current_app.logger.info(f"DÖF çözüm planı veritabanı işlem süresi: {commit_duration}ms")
        
        # Bildirim sistemi - direkt işlem (daha güvenli)
        try:
            # Merkezi bildirim sistemi kullan
            from notification_system import notify_for_dof_event
            
            if status_change:
                if dof.status == DOFStatus.PLANNING:
                    # Kök neden ve aksiyon planı hazırlandı/revize edildi
                    notify_for_dof_event(dof.id, "plan", current_user.id)
                    current_app.logger.info(f"DÖF #{dof.id} plan bildirimi gönderildi")
                elif dof.status == DOFStatus.COMPLETED:
                    # Aksiyonlar tamamlandı
                    notify_for_dof_event(dof.id, "complete", current_user.id)
                    current_app.logger.info(f"DÖF #{dof.id} tamamlama bildirimi gönderildi")
                else:
                    # Genel durum değişikliği
                    notify_for_dof_event(dof.id, "update", current_user.id)
                    current_app.logger.info(f"DÖF #{dof.id} durum değişikliği bildirimi gönderildi")
        except Exception as e:
            current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
        
        # Log kaydı oluştur
        action_text = "DÖF çözüm planı eklendi"
        if status_change:
            # DOFStatus string temsillerini elde etme
            old_status_name = "Bilinmiyor"
            new_status_name = "Bilinmiyor"
            
            # Eski durum
            if old_status == DOFStatus.DRAFT:
                old_status_name = "Taslak"
            elif old_status == DOFStatus.SUBMITTED:
                old_status_name = "Gönderildi"
            elif old_status == DOFStatus.IN_REVIEW:
                old_status_name = "İncelemede"
            elif old_status == DOFStatus.ASSIGNED:
                old_status_name = "Atandı"
            elif old_status == DOFStatus.IN_PROGRESS:
                old_status_name = "Devam Ediyor"
            elif old_status == DOFStatus.RESOLVED:
                old_status_name = "Çözüldü"
            elif old_status == DOFStatus.CLOSED:
                old_status_name = "Kapatıldı"
            elif old_status == DOFStatus.REJECTED:
                old_status_name = "Reddedildi"
            
            # Yeni durum
            if dof.status == DOFStatus.DRAFT:
                new_status_name = "Taslak"
            elif dof.status == DOFStatus.SUBMITTED:
                new_status_name = "Gönderildi"
            elif dof.status == DOFStatus.IN_REVIEW:
                new_status_name = "İncelemede"
            elif dof.status == DOFStatus.ASSIGNED:
                new_status_name = "Atandı"
            elif dof.status == DOFStatus.IN_PROGRESS:
                new_status_name = "Devam Ediyor"
            elif dof.status == DOFStatus.RESOLVED:
                new_status_name = "Çözüldü"
            elif dof.status == DOFStatus.CLOSED:
                new_status_name = "Kapatıldı"
            elif dof.status == DOFStatus.REJECTED:
                new_status_name = "Reddedildi"
                
            action_text = f"DÖF durumu değiştirildi: {dof.title} - {old_status_name} -> {new_status_name}"
        
        log_activity(
            user_id=current_user.id,
            action="DÖF Çözüm İşlemi",
            details=action_text,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash('DÖF çözüm planı başarıyla kaydedildi.', 'success')
        return redirect(url_for('dof.detail', dof_id=dof.id))
    
    # Form hataları varsa göster
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')
            
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    return render_template('dof/resolve.html', 
                           dof=dof,
                           form=form,
                           status=DOFStatus,
                           title="DÖF Çözüm Planı",
                           today_date=today)

@dof_bp.route('/dof/<int:dof_id>/download/<int:attachment_id>')
@login_required
def download_attachment(dof_id, attachment_id):
    dof = DOF.query.get_or_404(dof_id)
    attachment = Attachment.query.get_or_404(attachment_id)
    
    # Kullanıcının erişim yetkisi kontrol
    if current_user.role == UserRole.USER and dof.created_by != current_user.id and dof.assigned_to != current_user.id:
        abort(403)
    
    if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER and dof.created_by != current_user.id and dof.assigned_to != current_user.id and dof.department_id != current_user.department_id:
        abort(403)
    
    # Dosya yolunu kontrol et
    # attachment.file_path zaten göreceli bir yol, static/uploads/ altında olmalı
    file_path = os.path.join(os.getcwd(), 'static', os.path.basename(attachment.file_path))
    if not os.path.exists(file_path):
        # Alternatif yolu deneyelim
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(attachment.file_path))
        if not os.path.exists(file_path):
            flash('Dosya bulunamadı.', 'danger')
            return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Dosya İndirme",
        details=f"Dosya indirildi: {attachment.filename}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return send_file(file_path, as_attachment=True, download_name=attachment.filename)


@dof_bp.route('/dof/<int:dof_id>/preview/<int:attachment_id>')
@login_required
def preview_attachment(dof_id, attachment_id):
    dof = DOF.query.get_or_404(dof_id)
    attachment = Attachment.query.get_or_404(attachment_id)
    
    # Kullanıcının erişim yetkisi kontrol
    if current_user.role == UserRole.USER and dof.created_by != current_user.id and dof.assigned_to != current_user.id:
        abort(403)
    
    if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER and dof.created_by != current_user.id and dof.assigned_to != current_user.id and dof.department_id != current_user.department_id:
        abort(403)
    
    # Dosya yolunu kontrol et
    file_path = os.path.join(os.getcwd(), 'static', os.path.basename(attachment.file_path))
    if not os.path.exists(file_path):
        # Alternatif yolu deneyelim
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(attachment.file_path))
        if not os.path.exists(file_path):
            flash('Dosya bulunamadı.', 'danger')
            return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Dosya Önizleme",
        details=f"Dosya önizleme yapıldı: {attachment.filename}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    # Önizleme için as_attachment False olmalı
    return send_file(file_path, as_attachment=False)


@dof_bp.route('/dof/<int:dof_id>/action/<int:action_id>/download/<int:attachment_id>')
@login_required
def download_action_attachment(dof_id, action_id, attachment_id):
    """Yorum eklerini indirme endpoint'i"""
    dof = DOF.query.get_or_404(dof_id)
    action = DOFAction.query.get_or_404(action_id)
    attachment = ActionAttachment.query.get_or_404(attachment_id)
    
    # Kullanıcının erişim yetkisi kontrol
    if current_user.role == UserRole.USER and dof.created_by != current_user.id and dof.assigned_to != current_user.id:
        abort(403)
    
    if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER and dof.created_by != current_user.id and dof.assigned_to != current_user.id and dof.department_id != current_user.department_id:
        abort(403)
    
    # Action'ın doğru DÖF'e ait olduğunu kontrol et
    if action.dof_id != dof_id:
        abort(404)
        
    # Attachment'ın doğru action'a ait olduğunu kontrol et
    if attachment.action_id != action_id:
        abort(404)
    
    # Dosya yolunu kontrol et
    file_path = os.path.join(os.getcwd(), 'static', os.path.basename(attachment.file_path))
    if not os.path.exists(file_path):
        # Alternatif yolu deneyelim
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(attachment.file_path))
        if not os.path.exists(file_path):
            flash('Dosya bulunamadı.', 'danger')
            return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Yorum Eki İndirme",
        details=f"Yorum eki indirildi: {attachment.filename}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return send_file(file_path, as_attachment=True, download_name=attachment.filename)


@dof_bp.route("/dof/<int:dof_id>/mark_as_completed", methods=["GET", "POST"])
@login_required
def mark_as_completed(dof_id):
    # Rol kontrolü: Sadece admin, departman yöneticileri ve franchise departman yöneticileri girebilir
    if current_user.role not in [UserRole.DEPARTMENT_MANAGER, UserRole.FRANCHISE_DEPARTMENT_MANAGER, UserRole.ADMIN]:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
        
    dof = DOF.query.get_or_404(dof_id)
    
    # Yalnızca atanan departmanın yöneticileri bu işlemi yapabilir
    if current_user.department_id != dof.department_id and not current_user.is_admin():
        flash("Bu işlem için yetkiniz bulunmuyor.", "danger")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # DOF durumu PLANNING (8) veya IMPLEMENTATION (9) değilse işlemi yapma
    if dof.status not in [DOFStatus.PLANNING, DOFStatus.IMPLEMENTATION]:
        flash("Bu DOF henüz aksiyon planı onayı almamış veya uygulama aşamasında değil.", "warning")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    form = DOFActionForm()
    
    if request.method == "POST" and form.validate_on_submit():
        # Tamamlama detay açıklamasını al
        completion_details = form.comment.data if form.comment.data else "Aksiyon planı tamamlandı."
        
        # Departman tarafından tamamlandı olarak işaretle
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=2,  # Durum Değişikliği
            comment=completion_details,
            old_status=dof.status,
            new_status=DOFStatus.COMPLETED,
            created_at=datetime.now()
        )
        db.session.add(action)
        db.session.flush()  # ID'yi almak için flush
        
        # Dosya yükleme işlemi
        uploaded_files = []
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    try:
                        # Dosyayı kaydet - utils.py'deki yeni format
                        file_data = save_file(file)
                        
                        # ActionAttachment kaydı oluştur
                        attachment = ActionAttachment(
                            action_id=action.id,
                            filename=file_data['filename'],
                            file_path=file_data['file_path'],
                            uploaded_by=current_user.id,
                            file_size=file_data['file_size'],
                            file_type=file_data['file_type']
                        )
                        db.session.add(attachment)
                        uploaded_files.append(file_data['filename'])
                        
                    except Exception as e:
                        current_app.logger.error(f"Dosya yükleme hatası: {str(e)}")
                        flash(f"Dosya yükleme hatası: {file.filename}", "warning")
        
        # DOF durumunu SOURCE_REVIEW olarak güncelle (doğrudan kaynak değerlendirmesine geç)
        old_status = dof.status
        dof.status = DOFStatus.SOURCE_REVIEW  # Direkt kaynak değerlendirmesi aşamasına geç
        dof.updated_at = datetime.now()
        
        # Action'daki new_status'u da güncelle
        action.new_status = DOFStatus.SOURCE_REVIEW
        
        # Aktivite kaydı
        log_activity(
            user_id=current_user.id,
            action="DÖF Tamamlama",
            details=f"DÖF #{dof.id} için tüm aksiyonlar tamamlandı ve kaynak departman onayına gönderildi. {len(uploaded_files)} dosya eklendi.",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        # Veritabanı değişikliklerini kaydet
        db.session.commit()
        
        # YENİ MERKEZİ BİLDİRİM SİSTEMİNİ KULLAN
        try:
            from notification_system import notify_for_dof_event
            
            # Tek fonksiyon çağrısı ile tüm bildirimleri gönder
            notification_count = notify_for_dof_event(dof.id, "complete", current_user.id)
            current_app.logger.info(f"DÖF #{dof.id} tamamlama bildirimi: {notification_count} kişiye gönderildi")
            
        except Exception as e:
            current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            
            # Hata durumunda eski yöntemi kullan
            try:
                # Kaynak departmana bildirim gönder (DÖF'u oluşturan kişinin departmanı)
                if dof.creator and dof.creator.department_id:
                    managers = User.query.filter_by(department_id=dof.creator.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
                    for manager in managers:
                        notification = Notification(
                            user_id=manager.id,
                            dof_id=dof.id,
                            message=f"DÖF #{dof.id} aksiyonları tamamlandı. Lütfen inceleyiniz."
                        )
                        db.session.add(notification)
                
                # Kalite yöneticilerine bildirim gönder
                quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
                for manager in quality_managers:
                    notification = Notification(
                        user_id=manager.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} için aksiyonlar tamamlandı. Kaynak departman incelemesi bekliyor."
                    )
                    db.session.add(notification)
                
                db.session.commit()
                current_app.logger.info(f"DÖF #{dof.id} için eski yöntemle bildirimler gönderildi")
            except Exception as backup_error:
                current_app.logger.error(f"Yedek bildirim sistemi hatası: {str(backup_error)}")
                db.session.rollback()
        
        success_message = f"DÖF aksiyonları tamamlandı olarak işaretlendi ve kaynak departman onayına gönderildi."
        if uploaded_files:
            success_message += f" {len(uploaded_files)} dosya eklendi."
        
        flash(success_message, "success")
        return redirect(url_for('dof.detail', dof_id=dof.id))
    
    return render_template('dof/complete_actions.html', dof=dof, form=form)

@dof_bp.route("/dof/<int:dof_id>/review_action_plan", methods=["GET", "POST"])
@login_required
def review_action_plan(dof_id):
    # Rol kontrolü: Sadece admin ve kalite yöneticileri girebilir
    if current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
        
    dof = DOF.query.get_or_404(dof_id)
    
    # DOF durumu PLANNING (8) değilse erişim izni verme
    if dof.status != 8: # PLANNING
        flash("Bu DÖF henüz aksiyon planı inceleme aşamasında değil.", "warning")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    form = DOFActionForm()
    
    if request.method == "POST" and form.validate_on_submit():
        # İnceleme işlemi sonucu kaydı
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=2,  # Durum Değişikliği
            comment=(form.comment.data if form.comment.data.strip() else "Aksiyon planı onaylandı"),
            old_status=dof.status,
            created_at=datetime.now()
        )
        db.session.add(action)
        
        if 'approve' in request.form:  # Planı Onayla
            old_status = dof.status
            dof.status = 9  # IMPLEMENTATION - Uygulama Aşaması
            action.new_status = 9  # IMPLEMENTATION - Uygulama Aşaması
            dof.updated_at = datetime.now()
            
            # Atanan departmana bildirim gönder
            if dof.department_id:
                managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
                for manager in managers:
                    notification = Notification(
                        user_id=manager.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} için hazırlamış olduğunuz aksiyon planı kalite departmanı tarafından onaylandı. Lütfen aksiyonları uygulamaya başlayın."
                    )
                    db.session.add(notification)
            
            flash("Aksiyon planı onaylandı ve ilgili departmana bildirildi.", "success")
        
        db.session.commit()
        
        # E-posta bildirimi gönder
        if 'approve' in request.form and dof.department_id:
            try:
                # E-posta yardımcı fonksiyonunu import et
                from utils.email_helpers import get_app_url
                
                # E-posta alıcılarını belirle
                recipients = []
                managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER, active=True).all()
                for manager in managers:
                    if manager.email and manager.email.strip():
                        recipients.append(manager.email)
                
                if recipients:
                    # E-posta içeriği
                    subject = f"DÖF #{dof.id} - Aksiyon Planı Onaylandı"
                    dept_name = dof.department.name if dof.department else "İlgili Departman"
                    
                    # HTML içeriği
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
                            .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #dee2e6; }}
                            .content {{ padding: 20px 0; }}
                            .footer {{ font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 10px; }}
                            .highlight {{ font-weight: bold; color: #007bff; }}
                            .success {{ color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2>DÖF Aksiyon Planı Onaylandı</h2>
                            </div>
                            <div class="content">
                                <p>DÖF <span class="highlight">#{dof.id}</span> - {dof.title} için hazırlamış olduğunuz aksiyon planı kalite departmanı tarafından onaylandı.</p>
                                <p>Lütfen planladığınız aksiyonları uygulamaya başlayın.</p>
                                <p>Açıklama: {form.comment.data if form.comment.data.strip() else "Aksiyon planı onaylandı"}</p>
                                <div class="success">Aksiyonları tamamladığınızda DÖF detay sayfasından "Aksiyonları Tamamlandı" butonunu kullanarak kalite departmanına bildirebilirsiniz.</div>
                                <p>DÖF detaylarını görüntülemek için <a href="{url_for('dof.detail', dof_id=dof.id, _external=True)}">tıklayınız</a>.</p>
                            </div>
                            <div class="footer">
                                <p>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Düz metin içeriği
                    text_content = f"""
                    DÖF AKSİYON PLANI ONAYLANDI
                    
                    DÖF #{dof.id} - {dof.title} için hazırlamış olduğunuz aksiyon planı kalite departmanı tarafından onaylandı.
                    
                    Lütfen planladığınız aksiyonları uygulamaya başlayın.
                    
                    Açıklama: {form.comment.data if form.comment.data.strip() else "Aksiyon planı onaylandı"}
                    
                    Aksiyonları tamamladığınızda DÖF detay sayfasından "Aksiyonları Tamamlandı" butonunu kullanarak kalite departmanına bildirebilirsiniz.
                    
                    Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.
                    """
                    
                    # E-posta gönder
                    for recipient in recipients:
                        send_email_async(subject, [recipient], html_content, text_content)
                        current_app.logger.info(f"Aksiyon planı onayı e-postası gönderildi: {recipient}")
            except Exception as e:
                current_app.logger.error(f"Aksiyon planı onayı e-posta gönderimi hatası: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
        
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    return render_template('dof/review_action_plan.html', dof=dof, form=form, title="Aksiyon Planı İnceleme")

@dof_bp.route("/dof/<int:dof_id>/request_plan_revision", methods=["GET", "POST"])
@login_required
def request_plan_revision(dof_id):
    # Rol kontrolü: Sadece admin ve kalite yöneticileri girebilir
    if current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
        
    dof = DOF.query.get_or_404(dof_id)
    
    # DOF durumu PLANNING (8) değilse erişim izni verme
    if dof.status != 8: # PLANNING
        flash("Bu DÖF henüz aksiyon planı inceleme aşamasında değil.", "warning")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    form = DOFActionForm()
    
    if request.method == "POST" and form.validate_on_submit():
        # Değişiklik talebi kaydı
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=2,  # Durum Değişikliği
            comment=form.comment.data,
            old_status=dof.status,
            new_status=4,  # IN_PROGRESS - Revizyon gerekiyor
            created_at=datetime.now()
        )
        db.session.add(action)
        
        # DÖF durumunu IN_PROGRESS (4) olarak güncelle (revizyon için)
        old_status = dof.status
        dof.status = 4  # IN_PROGRESS - Devam Ediyor (Revizyon gerekiyor)
        dof.updated_at = datetime.now()
        
        # Atanan departmana bildirim gönder
        if dof.department_id:
            managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
            for manager in managers:
                notification = Notification(
                    user_id=manager.id,
                    dof_id=dof.id,
                    message=f"DÖF #{dof.id} için hazırladığınız aksiyon planında değişiklik talep edildi. Lütfen açıklamaları gözden geçirip planları güncelleyin."
                )
                db.session.add(notification)
        
        # Aktivite kaydı
        log_activity(
            user_id=current_user.id,
            action="Aksiyon Planı Revizyon Talebi",
            details=f"DÖF #{dof.id} aksiyon planında revizyon talep edildi.",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        db.session.commit()
        
        # E-posta bildirimi gönder
        if dof.department_id:
            try:
                # E-posta alıcılarını belirle
                recipients = []
                managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER, active=True).all()
                for manager in managers:
                    if manager.email and manager.email.strip():
                        recipients.append(manager.email)
                
                if recipients:
                    # E-posta içeriği
                    subject = f"DÖF #{dof.id} - Aksiyon Planı Revizyon Talebi"
                    dept_name = dof.department.name if dof.department else "İlgili Departman"
                    
                    # HTML içeriği
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
                            .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #dee2e6; }}
                            .content {{ padding: 20px 0; }}
                            .footer {{ font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 10px; }}
                            .highlight {{ font-weight: bold; color: #007bff; }}
                            .alert {{ color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2>DÖF Aksiyon Planı Revizyon Talebi</h2>
                            </div>
                            <div class="content">
                                <p>DÖF <span class="highlight">#{dof.id}</span> - {dof.title} için hazırladığınız aksiyon planında değişiklik talep edildi.</p>
                                <p>Lütfen açıklamaları gözden geçirip planları güncelleyin.</p>
                                <div class="alert">Revizyon Açıklaması: {form.comment.data}</div>
                                <p>DÖF detaylarını görüntülemek için <a href="{url_for('dof.detail', dof_id=dof.id, _external=True)}">tıklayınız</a>.</p>
                            </div>
                            <div class="footer">
                                <p>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Düz metin içeriği
                    text_content = f"""
                    DÖF AKSİYON PLANI REVİZYON TALEBİ
                    
                    DÖF #{dof.id} - {dof.title} için hazırladığınız aksiyon planında değişiklik talep edildi.
                    
                    Lütfen açıklamaları gözden geçirip planları güncelleyin.
                    
                    Revizyon Açıklaması: {form.comment.data}
                    
                    Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.
                    """
                    
                    # E-posta gönder
                    for recipient in recipients:
                        send_email_async(subject, [recipient], html_content, text_content)
                        current_app.logger.info(f"Aksiyon planı revizyon talebi e-postası gönderildi: {recipient}")
            except Exception as e:
                current_app.logger.error(f"Aksiyon planı revizyon talebi e-posta gönderimi hatası: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
        
        flash("Aksiyon planı için değişiklik talebi gönderildi ve ilgili departmana bildirildi.", "success")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    return render_template('dof/request_plan_revision.html', dof=dof, form=form, title="Aksiyon Planı Değişiklik Talebi")


@dof_bp.route("/dof/<int:dof_id>/review_source", methods=["GET", "POST"])
@login_required
def review_source(dof_id):
    # DÖF'yi getir
    dof = DOF.query.get_or_404(dof_id)
    
    # Rol kontrolü: Sadece admin ve departman yöneticileri girebilir
    if current_user.role not in [UserRole.DEPARTMENT_MANAGER, UserRole.FRANCHISE_DEPARTMENT_MANAGER, UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Departman kontrollerini bazı roller için atlayabilir, böylece her departman inceleme yapabilir
    if current_user.role == UserRole.ADMIN or current_user.role == UserRole.QUALITY_MANAGER:
        # Yöneticiler ve kalite yöneticileri tüm DÖF'lere erişebilir
        pass
    elif current_user.department_id != (dof.creator.department_id if dof.creator else None):
        flash("Bu işlem için yetkiniz bulunmuyor.", "danger")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # DOF durumu COMPLETED değilse erişim izni verme
    if dof.status != DOFStatus.COMPLETED:
        flash("Bu DOF henüz tamamlanma aşamasında değil.", "warning")
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    form = DOFActionForm()
    status_change = False
    approved = False
    rejected = False
    
    if form.validate_on_submit():
        # Kaynak incelemesi sonucu işlemleri
        action = DOFAction(
            dof_id=dof.id,
            user_id=current_user.id,
            action_type=2,  # Durum Değişikliği
            comment=form.comment.data,
            old_status=dof.status,
            created_at=datetime.now()
        )
        db.session.add(action)
        
        if 'approve' in request.form:  # Çözümü Onayla
            dof.status = DOFStatus.SOURCE_REVIEW
            dof.updated_at = datetime.now()
            action.new_status = DOFStatus.SOURCE_REVIEW  # Durum değişikliği action kaydına eklendi
            status_change = True
            approved = True
            
            # Atanan departmana bildirim gönder
            if dof.department_id:
                managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
                for manager in managers:
                    notification = Notification(
                        user_id=manager.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} çözümünüz kaynak departman tarafından onaylandı."
                    )
                    db.session.add(notification)
            
            # Kalite yöneticilerine bildirim gönder
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
            for manager in quality_managers:
                notification = Notification(
                    user_id=manager.id,
                    dof_id=dof.id,
                    message=f"UYARI: DÖF #{dof.id} kaynak departman tarafından değerlendirildi. Son kapatma işlemi için değerlendirme yapmanız gerekiyor.",
                    is_read=False,
                    created_at=datetime.now()
                )
                db.session.add(notification)
            
            flash("DÖF çözümü değerlendirildi ve kalite departmanına bildirim gönderildi. Kalite yöneticileri son değerlendirmeyi yapacaktır.", "success")
        
        elif 'reject' in request.form:  # Çözümü Reddet - Ancak yine de ileriye gidecek (Kalite'ye)
            # Kesinlikle geriye döndürmeyecek, bunun yerine SOURCE_REVIEW durumuna geçecek
            dof.status = DOFStatus.SOURCE_REVIEW  # DÖF'u kaynak değerlendirmesi durumuna geçir, Kalite'nin değerlendirmesi için
            dof.updated_at = datetime.now()
            action.new_status = DOFStatus.SOURCE_REVIEW  # Durum değişikliği
            action.comment = f"[KAYNAK MEMNUN DEĞİL] Ancak işlem kalite değerlendirmesine yönlendirildi: {action.comment}"
            status_change = True
            rejected = True
            
            # Kalite yöneticilerine özel bildirim gönder
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
            for manager in quality_managers:
                notification = Notification(
                    user_id=manager.id,
                    dof_id=dof.id,
                    message=f"ACİL: DÖF #{dof.id} kaynak departman tarafından ONAYLANMADI! Kalite değerlendirmesi gerekiyor. Lütfen inceleyip ya kapatma ya da yeni DÖF açma kararı verin.",
                    is_read=False,
                    created_at=datetime.now()
                )
                db.session.add(notification)
            
            # Atanan departmana da bildir
            if dof.department_id:
                managers = User.query.filter_by(department_id=dof.department_id, role=UserRole.DEPARTMENT_MANAGER).all()
                for manager in managers:
                    notification = Notification(
                        user_id=manager.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - Kaynak departman çözümünüzden memnun değil, ancak süreç geri dönmeyecek ve işlem kalite değerlendirmesine yönlendirildi. Bu aşamada ek bir aksiyon almanız gerekmiyor."
                    )
                    db.session.add(notification)
            
            # DÖF oluşturucusuna bildirim gönder
            if dof.created_by:
                creator = User.query.get(dof.created_by)
                if creator and creator.id != current_user.id:
                    notification = Notification(
                        user_id=creator.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - Kaynak departman çözümden memnun değil, Kalite'nin değerlendirmesi için yönlendirildi.",
                        created_at=datetime.now(),
                        is_read=False
                    )
                    db.session.add(notification)
                    
            # Tüm işlemleri kaydet
            db.session.commit()
            current_app.logger.info(f"DÖF #{dof.id} - Kaynak memnun değil ama Kalite'ye yönlendirildi")
            
            flash("Memnuniyetsizliğiniz kaydedildi. Süreç geri dönmeyecek ve DÖF kapanma aşaması için Kalite departmanına yönlendirildi. Kalite değerlendirmesi sonucunda gerekirse yeni DÖF açılabilir.", "warning")
            
            # Ana sayfaya yönlendirme yapılıyor (döngüleri önlemek için)
            return redirect(url_for('dof.detail', dof_id=dof.id))
            
        # Burada devam eden kodlar - notification_system kullanımı vb.
        # YENİ MERKEZİ BİLDİRİM SİSTEMİNİ KULLAN
        try:
            from notification_system import notify_for_dof_event
            
            # Tek fonksiyon çağrısı ile tüm bildirimleri gönder
            notification_count = notify_for_dof_event(dof.id, "complete", current_user.id)
            current_app.logger.info(f"DÖF #{dof.id} tamamlama bildirimi: {notification_count} kişiye gönderildi")
            
        except Exception as e:
            current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            
            # Hata durumunda eski yöntemi kullan
            try:
                # Kalite sorumlusuna bildirim gönder
                quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
                for qm in quality_managers:
                    notification = Notification(
                        user_id=qm.id,
                        dof_id=dof.id,
                        message=f"DÖF #{dof.id} - '{dof.title}' tamamlandı olarak işaretlendi.",
                        created_at=datetime.now(),
                        is_read=False
                    )
                    db.session.add(notification)
                
                # DÖF oluşturucusuna bildirim gönder
                if dof.created_by:
                    creator = User.query.get(dof.created_by)
                    if creator:
                        notification = Notification(
                            user_id=creator.id,
                            dof_id=dof.id,
                            message=f"DÖF #{dof.id} - '{dof.title}' hakkındaki çözümünüz değerlendirme için tamamlandı olarak işaretlendi.",
                            created_at=datetime.now(),
                            is_read=False
                        )
                        db.session.add(notification)
                    
                db.session.commit()
                current_app.logger.info(f"DÖF #{dof.id} için eski yöntemle bildirimler gönderildi")
            except Exception as backup_error:
                current_app.logger.error(f"Yedek bildirim sistemi hatası: {str(backup_error)}")
                db.session.rollback()
                flash("DÖF işlemi sırasında bir hata oluştu, ancak işlem devam ediyor.", "warning")
        
        db.session.commit()
        
        # Asenkron e-posta gönderimi
        if status_change:
            from threading import Thread
            thread = Thread(target=send_notifications_async)
            thread.daemon = True
            thread.start()
            current_app.logger.info(f"Asenkron bildirim gönderimi başlatıldı - DÖF #{dof.id}")
        
        return redirect(url_for('dof.detail', dof_id=dof_id))
    
    # Asenkron e-posta bildirim gönderimi için iç fonksiyon
    def send_notifications_async():
        try:
            # E-posta bilgilerini hazırla
            dof_id = dof.id
            dof_title = dof.title
            dept_id = dof.department_id
            source_dept_id = dof.creator.department_id if dof.creator else None
            quality_dept_message = ""
            dept_message = ""
            recipients = []
            
            # Kalite yöneticilerine e-posta gönderimi hazırlığı (her iki durumda da)
            quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
            for manager in quality_managers:
                if manager.email and manager.email.strip():
                    recipients.append(manager.email)
                    
            if approved:
                quality_dept_message = f"DÖF #{dof_id} kaynak departman tarafından ÇÖZÜLDÜ olarak onaylandı. Son kapatma işlemi için değerlendirme yapmanız gerekiyor."
            elif rejected:
                quality_dept_message = f"DÖF #{dof_id} kaynak departman tarafından reddedildi. Süreç hakkında bilginize."
            
            # Atanan departman yöneticilerine e-posta gönderimi hazırlığı
            if dept_id:
                dept_managers = User.query.filter_by(department_id=dept_id, role=UserRole.DEPARTMENT_MANAGER, active=True).all()
                for manager in dept_managers:
                    if manager.email and manager.email.strip() and manager.email not in recipients:
                        recipients.append(manager.email)
                
                if approved:
                    dept_message = f"DÖF #{dof_id} çözümünüz kaynak departman tarafından ONAYLANDI."
                elif rejected:
                    dept_message = f"DÖF #{dof_id} çözümünüz kaynak departman tarafından REDDEDİLDİ, ancak süreç geri dönmeyecek ve kalite departmanı final değerlendirme yapacaktır. Bu aşamada ek bir aksiyon almanız gerekmiyor."
            
            # Kaynak departman adını al
            source_dept_name = "Belirsiz Departman"
            if source_dept_id:
                source_dept = Department.query.get(source_dept_id)
                if source_dept:
                    source_dept_name = source_dept.name
            
            # Eğer alıcı yoksa işlemi sonlandır
            if not recipients:
                current_app.logger.warning(f"DÖF #{dof_id} için e-posta alıcısı bulunamadı")
                return
            
            # E-posta içeriği hazırlama
            if approved:
                subject = f"DÖF #{dof_id} - Kaynak Departman Çözümü Onayladı"
                action_text = f"{source_dept_name} departmanı, DÖF çözümünü ONAYLADI."
            elif rejected:
                subject = f"DÖF #{dof_id} - Kaynak Departman Çözümü Reddetti"
                action_text = f"{source_dept_name} departmanı, DÖF çözümünü REDDETTİ."
            else:
                return  # Başka bir durum varsa gönderim yapma
            
            # HTML içeriği
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #dee2e6; }}
                    .content {{ padding: 20px 0; }}
                    .footer {{ font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 10px; }}
                    .highlight {{ font-weight: bold; color: #007bff; }}
                    .alert {{ color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                    .success {{ color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>DÖF Durum Değişikliği</h2>
                    </div>
                    <div class="content">
                        <p>DÖF <span class="highlight">#{dof_id}</span> - {dof_title} için durum değişikliği bilgisi:</p>
                        <p>{action_text}</p>
                        <p>Açıklama: {form.comment.data}</p>
                        
                        {f'<div class="alert"><strong>Atanan departman için:</strong> {dept_message}</div>' if dept_message else ''}
                        {f'<div class="alert"><strong>Kalite departmanı için:</strong> {quality_dept_message}</div>' if quality_dept_message else ''}
                        
                        <p>DÖF detaylarını görüntülemek için <a href="{url_for('dof.detail', dof_id=dof_id, _external=True)}">tıklayınız</a>.</p>
                    </div>
                    <div class="footer">
                        <p>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Düz metin içeriği
            text_content = f"""
            DÖF DURUM DEĞİŞİKLİĞİ
            
            DÖF #{dof_id} - {dof_title} için durum değişikliği bilgisi:
            
            {action_text}
            
            Açıklama: {form.comment.data}
            
            {f'Atanan departman için: {dept_message}' if dept_message else ''}
            {f'Kalite departmanı için: {quality_dept_message}' if quality_dept_message else ''}
            
            Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayınız.
            """
            
            # Her alıcıya e-posta gönder
            for recipient in recipients:
                current_app.logger.info(f"KAYNAK İNCELEMESİ bildirim e-postası gönderiliyor: {recipient}")
                send_email_async(subject, [recipient], html_content, text_content)
                
        except Exception as e:
            current_app.logger.error(f"Asenkron bildirim hatası: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
    
    return render_template('dof/review_source.html', dof=dof, form=form)

# DÖF Raporları - Herkesin erişebileceği kişisel DÖF raporları
@dof_bp.route('/dof/reports')
@login_required
def reports():
    """Herkesin erişebileceği DÖF raporları"""
    from utils import get_dof_status_counts
    from sqlalchemy import func, and_, or_
    from datetime import datetime, timedelta
    
    # Tarih aralıkları
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    this_year = today.replace(month=1, day=1)
    
    # Kullanıcının rolüne göre veri filtreleme
    base_query = DOF.query
    
    # Normal kullanıcılar sadece kendi DÖF'lerini görebilir
    if current_user.role == UserRole.USER:
        base_query = base_query.filter(
            or_(
                DOF.created_by == current_user.id,
                DOF.assigned_to == current_user.id
            )
        )
    # Departman yöneticileri kendi departmanlarını görebilir
    elif current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        if current_user.department_id:
            dept_users = User.query.filter_by(department_id=current_user.department_id).all()
            dept_user_ids = [user.id for user in dept_users]
            base_query = base_query.filter(
                or_(
                    DOF.created_by.in_(dept_user_ids),
                    DOF.department_id == current_user.department_id,
                    DOF.assigned_to == current_user.id
                )
            )
    # Admin ve kalite yöneticileri tüm DÖF'leri görebilir
    elif current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Kalite yöneticisi ve admin için kısıtlama yok - tüm DÖF'leri görebilir
        pass
    
    # URL parametrelerinden filtreleri al
    department_filter = request.args.get('department_id', type=int)
    month_filter = request.args.get('month')
    status_filter = request.args.get('status', type=int)
    
    # Departman filtreleme (kalite yöneticisi için)
    if department_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.department_id == department_filter)
    
    # Ay filtreleme (kalite yöneticisi için)
    if month_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # YYYY-MM formatından datetime aralığına çevir
        try:
            year, month = map(int, month_filter.split('-'))
            from datetime import datetime, timedelta
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
            base_query = base_query.filter(DOF.created_at.between(month_start, month_end))
        except (ValueError, TypeError):
            pass  # Geçersiz tarih formatı, filtreleme yapma
    
    # Durum filtreleme (kalite yöneticisi için)
    if status_filter is not None and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.status == status_filter)
    
    # Filtrelenmiş DÖF'leri al
    filtered_dofs = base_query.all()
    accessible_dof_ids = [dof.id for dof in filtered_dofs]
    
    # Genel istatistikler (filtrelenmiş veriye göre)
    # Manuel olarak filtered_dofs üzerinden hesapla
    stats = {
        'total_dofs': len(filtered_dofs),
        'this_month': len([dof for dof in filtered_dofs if dof.created_at >= today.replace(day=1)]),
        'this_week': len([dof for dof in filtered_dofs if dof.created_at >= seven_days_ago]),
        'today': len([dof for dof in filtered_dofs if dof.created_at >= today]),
    }
    
    # Kullanıcının oluşturduğu DÖF'ler (filtrelenmiş veriye göre)
    if current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Normal kullanıcılar için kendi DÖF'lerini filtrele
        user_created_dofs = [dof for dof in filtered_dofs if dof.created_by == current_user.id]
        stats['created_total'] = len(user_created_dofs)
        stats['created_active'] = len([dof for dof in user_created_dofs if dof.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
        stats['created_closed'] = len([dof for dof in user_created_dofs if dof.status == DOFStatus.CLOSED])
        
        # Kullanıcıya atanan DÖF'ler (filtrelenmiş veriye göre)
        user_assigned_dofs = [dof for dof in filtered_dofs if dof.assigned_to == current_user.id]
        stats['assigned_total'] = len(user_assigned_dofs)
        stats['assigned_active'] = len([dof for dof in user_assigned_dofs if dof.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
        stats['assigned_closed'] = len([dof for dof in user_assigned_dofs if dof.status == DOFStatus.CLOSED])
        
        # Departman yöneticisi için ek istatistikler (filtrelenmiş veriye göre)
        if current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER and current_user.department_id:
            dept_dofs = [dof for dof in filtered_dofs if dof.department_id == current_user.department_id]
            stats['dept_total'] = len(dept_dofs)
            stats['dept_active'] = len([dof for dof in dept_dofs if dof.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
            stats['dept_closed'] = len([dof for dof in dept_dofs if dof.status == DOFStatus.CLOSED])
    else:
        # Admin ve kalite yöneticileri için filtrelenmiş sistemin tamamını göster
        stats['created_total'] = len(filtered_dofs)
        stats['created_active'] = len([dof for dof in filtered_dofs if dof.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
        stats['created_closed'] = len([dof for dof in filtered_dofs if dof.status == DOFStatus.CLOSED])
        stats['assigned_total'] = len(filtered_dofs)
        stats['assigned_active'] = len([dof for dof in filtered_dofs if dof.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
        stats['assigned_closed'] = len([dof for dof in filtered_dofs if dof.status == DOFStatus.CLOSED])
    

    
    # Durum dağılımı (filtrelenmiş veriye göre)
    status_counts = []
    if accessible_dof_ids:
        # Direkt dictionary kullanarak sayımları yap
        from collections import Counter
        status_counter = Counter()
        for dof in filtered_dofs:
            if dof.status is not None:
                status_counter[int(dof.status)] += 1
        status_counts = list(status_counter.items())
    
    # DÖF tipi dağılımı (filtrelenmiş veriye göre)
    type_counts = []
    if accessible_dof_ids:
        type_counter = Counter()
        for dof in filtered_dofs:
            if dof.dof_type is not None:
                type_counter[int(dof.dof_type)] += 1
        type_counts = list(type_counter.items())
    
    # DÖF kaynağı dağılımı (filtrelenmiş veriye göre)
    source_counts = []
    if accessible_dof_ids:
        source_counter = Counter()
        for dof in filtered_dofs:
            if dof.dof_source is not None:
                source_counter[int(dof.dof_source)] += 1
        source_counts = list(source_counter.items())
    
    # Aylık trend (son 6 ay) - filtrelenmiş veriye göre
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Filtrelenmiş DÖF'ler arasından aylık sayım yap
        month_count = len([dof for dof in filtered_dofs if month_start <= dof.created_at <= month_end])
        
        monthly_data.append({
            'month': month_start.strftime('%B %Y'),
            'count': month_count
        })
    
    # Yaklaşan terminler (filtrelenmiş veriye göre)
    future_date = today + timedelta(days=30)
    upcoming_deadlines_query = base_query.filter(
        DOF.deadline.isnot(None),
        DOF.deadline.between(today, future_date),
        ~DOF.status.in_([DOFStatus.CLOSED, DOFStatus.REJECTED])
    ).order_by(DOF.deadline.asc()).limit(10)
    upcoming_deadlines = upcoming_deadlines_query.all()
    
    # Geçmiş terminler (filtrelenmiş veriye göre)
    overdue_dofs_query = base_query.filter(
        DOF.deadline.isnot(None),
        DOF.deadline < today,
        ~DOF.status.in_([DOFStatus.CLOSED, DOFStatus.REJECTED])
    ).order_by(DOF.deadline.desc()).limit(10)
    overdue_dofs = overdue_dofs_query.all()
    
    # Son oluşturulan DÖF'ler (filtrelenmiş veriye göre)
    if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Kalite yöneticisi için filtrelenmiş veriden son DÖF'ler
        recent_created = base_query.order_by(DOF.created_at.desc()).limit(5).all()
    else:
        # Diğer kullanıcılar için kendi oluşturdukları
        recent_created = DOF.query.filter_by(created_by=current_user.id).order_by(DOF.created_at.desc()).limit(5).all()
    
    # Son atanan DÖF'ler
    recent_assigned = DOF.query.filter_by(assigned_to=current_user.id).order_by(DOF.created_at.desc()).limit(5).all()
    
    return render_template('dof/reports.html',
                          stats=stats,
                          status_counts=status_counts,
                          type_counts=type_counts,
                          source_counts=source_counts,
                          monthly_data=monthly_data,
                          upcoming_deadlines=upcoming_deadlines,
                          overdue_dofs=overdue_dofs,
                          recent_created=recent_created,
                          recent_assigned=recent_assigned,
                          filtered_dofs=filtered_dofs,
                          DOFStatus=DOFStatus,
                          DOFType=DOFType,
                          DOFSource=DOFSource,
                          UserRole=UserRole)

# Reports sayfası Excel export (filtrelenmiş)
@dof_bp.route('/dof/reports/export/excel', methods=['GET'])
@login_required
def export_reports_excel():
    """Reports sayfasından filtrelenmiş verileri Excel olarak dışa aktar"""
    # Reports route'undan aynı filtreleme mantığını kullan
    from sqlalchemy import func, and_, or_
    from datetime import datetime, timedelta
    
    # Tarih aralıkları
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Kullanıcının rolüne göre veri filtreleme
    base_query = DOF.query
    
    # Normal kullanıcılar sadece kendi DÖF'lerini görebilir
    if current_user.role == UserRole.USER:
        base_query = base_query.filter(
            or_(
                DOF.created_by == current_user.id,
                DOF.assigned_to == current_user.id
            )
        )
    # Departman yöneticileri kendi departmanlarını görebilir
    elif current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        if current_user.department_id:
            dept_users = User.query.filter_by(department_id=current_user.department_id).all()
            dept_user_ids = [user.id for user in dept_users]
            base_query = base_query.filter(
                or_(
                    DOF.created_by.in_(dept_user_ids),
                    DOF.department_id == current_user.department_id,
                    DOF.assigned_to == current_user.id
                )
            )
    # Admin ve kalite yöneticileri tüm DÖF'leri görebilir
    elif current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Kalite yöneticisi ve admin için kısıtlama yok - tüm DÖF'leri görebilir
        pass
    
    # URL parametrelerinden filtreleri al
    department_filter = request.args.get('department_id', type=int)
    month_filter = request.args.get('month')
    status_filter = request.args.get('status', type=int)
    
    # Departman filtreleme (kalite yöneticisi için)
    if department_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.department_id == department_filter)
    
    # Ay filtreleme (kalite yöneticisi için)
    if month_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # YYYY-MM formatından datetime aralığına çevir
        try:
            year, month = map(int, month_filter.split('-'))
            from datetime import datetime, timedelta
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
            base_query = base_query.filter(DOF.created_at.between(month_start, month_end))
        except (ValueError, TypeError):
            pass  # Geçersiz tarih formatı, filtreleme yapma
    
    # Durum filtreleme (kalite yöneticisi için)
    if status_filter is not None and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.status == status_filter)
    
    # Filtrelenmiş DÖF'leri al
    dofs = base_query.order_by(DOF.created_at.desc()).all()
    
    # Excel dosyasını oluştur
    try:
        current_app.logger.info(f"Reports Excel dosyası oluşturuluyor: {len(dofs)} DÖF")
        excel_io = export_dofs_to_excel(dofs)
        
        # Dosyayı kullanıcıya gönder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            excel_io,
            as_attachment=True,
            download_name=f'DOF_Raporu_{timestamp}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"Reports Excel oluşturma hatası: {str(e)}")
        flash(f"Excel dosyası oluşturulurken hata oluştu: {str(e)}", "danger")
        return redirect(url_for('dof.reports'))

# Reports sayfası PDF export (filtrelenmiş)
@dof_bp.route('/dof/reports/export/pdf', methods=['GET'])
@login_required
def export_reports_pdf():
    """Reports sayfasından filtrelenmiş verileri PDF olarak dışa aktar"""
    # Reports route'undan aynı filtreleme mantığını kullan
    from sqlalchemy import func, and_, or_
    from datetime import datetime, timedelta
    
    # Tarih aralıkları
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Kullanıcının rolüne göre veri filtreleme
    base_query = DOF.query
    
    # Normal kullanıcılar sadece kendi DÖF'lerini görebilir
    if current_user.role == UserRole.USER:
        base_query = base_query.filter(
            or_(
                DOF.created_by == current_user.id,
                DOF.assigned_to == current_user.id
            )
        )
    # Departman yöneticileri kendi departmanlarını görebilir
    elif current_user.role == UserRole.DEPARTMENT_MANAGER or current_user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        if current_user.department_id:
            dept_users = User.query.filter_by(department_id=current_user.department_id).all()
            dept_user_ids = [user.id for user in dept_users]
            base_query = base_query.filter(
                or_(
                    DOF.created_by.in_(dept_user_ids),
                    DOF.department_id == current_user.department_id,
                    DOF.assigned_to == current_user.id
                )
            )
    # Admin ve kalite yöneticileri tüm DÖF'leri görebilir
    elif current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Kalite yöneticisi ve admin için kısıtlama yok - tüm DÖF'leri görebilir
        pass
    
    # URL parametrelerinden filtreleri al
    department_filter = request.args.get('department_id', type=int)
    month_filter = request.args.get('month')
    status_filter = request.args.get('status', type=int)
    
    # Departman filtreleme (kalite yöneticisi için)
    if department_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.department_id == department_filter)
    
    # Ay filtreleme (kalite yöneticisi için)
    if month_filter and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # YYYY-MM formatından datetime aralığına çevir
        try:
            year, month = map(int, month_filter.split('-'))
            from datetime import datetime, timedelta
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
            base_query = base_query.filter(DOF.created_at.between(month_start, month_end))
        except (ValueError, TypeError):
            pass  # Geçersiz tarih formatı, filtreleme yapma
    
    # Durum filtreleme (kalite yöneticisi için)
    if status_filter is not None and current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        base_query = base_query.filter(DOF.status == status_filter)
    
    # Filtrelenmiş DÖF'leri al
    dofs = base_query.order_by(DOF.created_at.desc()).all()
    
    # PDF dosyasını oluştur
    try:
        current_app.logger.info(f"Reports PDF dosyası oluşturuluyor: {len(dofs)} DÖF")
        pdf_io = export_dofs_to_pdf(dofs)
        
        # Dosyayı kullanıcıya gönder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            pdf_io,
            as_attachment=True,
            download_name=f'DOF_Raporu_{timestamp}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f"Reports PDF oluşturma hatası: {str(e)}")
        flash(f"PDF dosyası oluşturulurken hata oluştu: {str(e)}", "danger")
        return redirect(url_for('dof.reports'))

# DÖF Detayı PDF Export
@dof_bp.route('/dof/<int:dof_id>/export/pdf')
@login_required
def export_dof_detail_pdf(dof_id):
    """DÖF detayını PDF olarak dışa aktar"""
    dof = DOF.query.get_or_404(dof_id)
    
    # Yetki kontrolü (detay sayfasını görebilen herkes PDF'i de indirebilir)
    if not can_view_dof(dof, current_user):
        flash('Bu DÖF\'e erişim yetkiniz bulunmuyor.', 'danger')
        return redirect(url_for('dof.list_dofs'))
    
    try:
        from export_utils import create_dof_detail_pdf
        
        # PDF oluştur
        pdf_content = create_dof_detail_pdf(dof)
        
        # Response oluştur
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="DOF_{dof_id}_Detay.pdf"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"PDF export hatası: {str(e)}")
        flash('PDF oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))

# DÖF Detayı Excel Export
@dof_bp.route('/dof/<int:dof_id>/export/excel')
@login_required
def export_dof_detail_excel(dof_id):
    """DÖF detayını Excel olarak dışa aktar"""
    dof = DOF.query.get_or_404(dof_id)
    
    # Yetki kontrolü
    if not can_view_dof(dof, current_user):
        flash('Bu DÖF\'e erişim yetkiniz bulunmuyor.', 'danger')
        return redirect(url_for('dof.list_dofs'))
    
    try:
        from export_utils import create_dof_detail_excel
        
        # Excel oluştur
        excel_content = create_dof_detail_excel(dof)
        
        # Response oluştur
        response = make_response(excel_content)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="DOF_{dof_id}_Detay.xlsx"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Excel export hatası: {str(e)}")
        flash('Excel oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('dof.detail', dof_id=dof_id))

# Yetki kontrolü fonksiyonu
def can_view_dof(dof, user):
    """Kullanıcının DÖF'ü görüntüleme yetkisi var mı kontrol et"""
    if user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        return True
    
    if user.role == UserRole.DEPARTMENT_MANAGER or user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        if user.department_id:
            # Kendi departmanına ait DÖF'leri görebilir
            if dof.department_id == user.department_id:
                return True
            # Kendi departmanı çalışanları tarafından oluşturulan DÖF'leri görebilir
            if dof.creator and dof.creator.department_id == user.department_id:
                return True
            # Kendisine atanan DÖF'leri görebilir
            if dof.assigned_to == user.id:
                return True
    
    if user.role == UserRole.USER:
        # Kendi oluşturduğu veya kendisine atanan DÖF'leri görebilir
        if dof.created_by == user.id or dof.assigned_to == user.id:
            return True
    
    return False


@dof_bp.route('/dof/<int:dof_id>/delete', methods=['POST'])
@login_required
def delete_dof(dof_id):
    """DÖF silme işlemi"""
    from app import db
    
    dof = DOF.query.get_or_404(dof_id)
    
    # Silme yetkisi kontrolü
    if not dof.can_be_deleted_by(current_user):
        flash('Bu DÖF\'ü silme yetkiniz yok.', 'error')
        return redirect(url_for('dof.view_dof', dof_id=dof_id))
    
    try:
        # DÖF'ün bilgilerini log için sakla
        dof_title = dof.title
        dof_code = dof.code or f"DÖF #{dof.id}"
        
        # İlişkili verileri sil
        # DÖF aksiyonlarını sil
        DOFAction.query.filter_by(dof_id=dof_id).delete()
        
        # DÖF eklerini sil
        attachments = Attachment.query.filter_by(dof_id=dof_id).all()
        for attachment in attachments:
            # Dosyayı diskten sil
            if attachment.file_path and os.path.exists(attachment.file_path):
                try:
                    os.remove(attachment.file_path)
                except OSError:
                    pass  # Dosya silinmese de devam et
            db.session.delete(attachment)
        
        # Bildirimleri sil
        Notification.query.filter_by(dof_id=dof_id).delete()
        
        # Aktivite loglarını sil
        UserActivity.query.filter_by(dof_id=dof_id).delete()
        
        # DÖF'ü sil
        db.session.delete(dof)
        db.session.commit()
        
        # Aktivite logu ekle
        log_activity(
            user_id=current_user.id,
            action='DÖF_SILINDI',
            description=f'{dof_code} - {dof_title} DÖF\'ü silindi.',
            dof_id=None  # DÖF silindiği için None
        )
        
        flash(f'{dof_code} başarıyla silindi.', 'success')
        current_app.logger.info(f"DÖF silindi: {dof_code} - Silen: {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash('DÖF silinirken bir hata oluştu.', 'error')
        current_app.logger.error(f"DÖF silme hatası: {str(e)}")
        return redirect(url_for('dof.view_dof', dof_id=dof_id))
    
    return redirect(url_for('dof.list_dofs'))
