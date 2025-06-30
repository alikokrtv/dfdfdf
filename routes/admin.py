from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_required, current_user
from app import db, mail
from models import User, Department, SystemLog, DOF, DOFAction, WorkflowDefinition, WorkflowStep, UserRole, DOFStatus, UserDepartmentMapping, DirectorManagerMapping, EmailTrack
from forms import RegisterForm, DepartmentForm, WorkflowDefinitionForm, WorkflowStepForm, EmailSettingsForm
from utils import log_activity, get_department_stats
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin yetkisi gerektiren işlemler için decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dof.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@admin_bp.route('/users')
@admin_required
def users():
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/update_department_roles', methods=['POST'])
@admin_required
def update_department_roles():
    """
    Departmanı olan tüm kullanıcıların rollerini 'Departman Yöneticisi' olarak günceller
    """
    # Departmanı olan ama rolü 'Kullanıcı' (5) olan tüm kullanıcıları bul
    users = User.query.filter(
        User.department_id != None,
        User.role == 5  # UserRole.USER = 5
    ).all()
    
    count = 0
    for user in users:
        user.role = 4  # UserRole.DEPARTMENT_MANAGER = 4
        count += 1
    
    db.session.commit()
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Toplu Rol Güncelleme",
        details=f"{count} kullanıcının rolü 'Departman Yöneticisi' olarak güncellendi",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    flash(f'{count} kullanıcının rolü başarıyla güncellendi.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Admin rolü sadece admin tarafından verilebilir
    if current_user.role != UserRole.ADMIN and user.role == UserRole.ADMIN:
        flash('Admin kullanıcısını düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('admin.users'))
    
    form = RegisterForm(obj=user, user_id=user.id)
    
    # Şifre alanlarını kaldır
    del form.password
    del form.confirm_password
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.role = form.role.data
        
        # Role göre departman ilişkilerini ayarla
        if user.role == UserRole.DEPARTMENT_MANAGER or user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
            user.department_id = form.department.data if form.department.data != 0 else None
            # Bölge müdürü rolünden departman yöneticisine geçişte, çoklu departman ilişkilerini temizle
            for mapping in user.managed_department_mappings:
                db.session.delete(mapping)
            
            # Direktör rolünden departman yöneticisine geçişte, direktör-bölge müdürü ilişkilerini temizle
            for mapping in user.managed_managers_links:
                db.session.delete(mapping)
        elif user.role == UserRole.GROUP_MANAGER:
            user.department_id = None  # Grup yöneticisi doğrudan bir departmana bağlı değil
            
            try:
                # Önce mevcut departman ilişkilerini temizle
                for mapping in user.managed_department_mappings:
                    db.session.delete(mapping)
                
                # Direktör rolünden bölge müdürü rolüne geçişte, direktör-bölge müdürü ilişkilerini temizle
                for mapping in user.managed_managers_links:
                    db.session.delete(mapping)
                
                # Yeni seçilen departmanları ekle
                if form.managed_departments.data:
                    current_app.logger.info(f"Bölge Müdürü için departman güncelleme: {form.managed_departments.data}")
                    for dept_id in form.managed_departments.data:
                        # Departman ID'nin integer olduğundan emin ol
                        dept_id = int(dept_id) if not isinstance(dept_id, int) else dept_id
                        
                        # Departmanın varlığını kontrol et
                        dept = Department.query.get(dept_id)
                        if dept:
                            mapping = UserDepartmentMapping(user_id=user.id, department_id=dept_id)
                            db.session.add(mapping)
                        else:
                            current_app.logger.error(f"Departman bulunamadı ID: {dept_id}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Bölge müdürü departman güncelleme hatası: {str(e)}")
                flash(f'Kullanıcı bilgileri güncellendi ancak departman atama işlemi sırasında hata: {str(e)}', 'warning')
                return redirect(url_for('admin.users'))
        elif user.role == UserRole.DIRECTOR:
            user.department_id = None  # Direktör doğrudan bir departmana bağlı değil
            
            try:
                # Önce mevcut departman ilişkilerini temizle
                for mapping in user.managed_department_mappings:
                    db.session.delete(mapping)
                
                # Önce mevcut bölge müdürü ilişkilerini temizle
                for mapping in user.managed_managers_links:
                    db.session.delete(mapping)
                
                # Direktör için çoklu departman ilişkisi ekle
                if form.managed_departments.data:
                    current_app.logger.info(f"Direktör için departman güncelleme: {form.managed_departments.data}")
                    for dept_id in form.managed_departments.data:
                        dept_id = int(dept_id) if not isinstance(dept_id, int) else dept_id
                        dept = Department.query.get(dept_id)
                        if dept:
                            mapping = UserDepartmentMapping(user_id=user.id, department_id=dept_id)
                            db.session.add(mapping)
                        else:
                            current_app.logger.error(f"Departman bulunamadı ID: {dept_id}")
                
                # Direktör için bölge müdürü ilişkilerini kaydet
                if form.managed_managers.data:
                    current_app.logger.info(f"Direktör için bölge müdürü güncelleme: {form.managed_managers.data}")
                    for manager_id in form.managed_managers.data:
                        manager_id = int(manager_id) if not isinstance(manager_id, int) else manager_id
                        manager = User.query.get(manager_id)
                        if manager and manager.role == UserRole.GROUP_MANAGER:
                            mapping = DirectorManagerMapping(director_id=user.id, manager_id=manager_id)
                            db.session.add(mapping)
                            current_app.logger.info(f"Direktör-Bölge Müdürü ilişkisi güncellendi: Direktör={user.id}, Bölge Müdürü={manager_id}")
                        else:
                            current_app.logger.error(f"Bölge müdürü bulunamadı veya rolü uygun değil ID: {manager_id}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Direktör ilişkileri güncelleme hatası: {str(e)}")
                flash(f'Kullanıcı bilgileri güncellendi ancak ilişkilerde hata: {str(e)}', 'warning')
                return redirect(url_for('admin.users'))
        else:
            # Admin ve Kalite Yöneticisi için departman ilişkisi gerekmez
            user.department_id = None
            # Varsa çoklu departman ilişkilerini temizle
            for mapping in user.managed_department_mappings:
                db.session.delete(mapping)
            # Varsa direktör-bölge müdürü ilişkilerini temizle
            for mapping in user.managed_managers_links:
                db.session.delete(mapping)
        
        user.updated_at = datetime.now()
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Kullanıcı Güncelleme",
            details=f"Kullanıcı güncellendi: {user.username}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'Kullanıcı {user.username} başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.users'))
    
    # Form alanlarını doldur
    if user.department_id:
        form.department.data = user.department_id
    
    # Grup yöneticisi ise yönetilen departmanları doldur
    if user.role == UserRole.GROUP_MANAGER:
        managed_dept_ids = [mapping.department_id for mapping in user.managed_department_mappings]
        form.managed_departments.data = managed_dept_ids
    
    # Direktör ise yönetilen departmanları ve bölge müdürlerini doldur
    elif user.role == UserRole.DIRECTOR:
        # Yönetilen departmanlar
        managed_dept_ids = [mapping.department_id for mapping in user.managed_department_mappings]
        form.managed_departments.data = managed_dept_ids
        
        # Yönetilen bölge müdürleri
        managed_manager_ids = [mapping.manager_id for mapping in user.managed_managers_links]
        form.managed_managers.data = managed_manager_ids
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Admin kullanıcısını silmeyi engelle
    if user.role == 1:  # UserRole.ADMIN = 1
        flash('Admin kullanıcısını silemezsiniz.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Kullanıcı adını ve e-postasını kaydet
    username = user.username
    
    # Kullanıcıyı sil
    db.session.delete(user)
    db.session.commit()
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Kullanıcı Silme",
        details=f"Kullanıcı silindi: {username}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    flash(f'Kullanıcı {username} başarıyla silindi.', 'success')
    return redirect(url_for('admin.users'))
    
    # Admin kullanıcısının durumu değiştirilemez
    if user.role == UserRole.ADMIN and current_user.id != user.id:
        flash('Admin kullanıcısının durumunu değiştirme yetkiniz yok.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Kullanıcı kendi hesabını pasif yapamaz
    if current_user.id == user.id:
        flash('Kendi hesabınızı pasif yapamazsınız.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status_text = "aktif" if user.is_active else "pasif"
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Kullanıcı Durum Değiştirme",
        details=f"Kullanıcı durumu değiştirildi: {user.username} - {status_text}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    flash(f'Kullanıcı {user.username} {status_text} duruma getirildi.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset_password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Yeni şifre oluştur
    new_password = "dof123"  # Basit bir şifre, gerçek uygulamada rastgele oluşturulmalı
    user.set_password(new_password)
    db.session.commit()
    
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Kullanıcı Şifre Sıfırlama",
        details=f"Kullanıcı şifresi sıfırlandı: {user.username}",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    flash(f'Kullanıcı {user.username} şifresi sıfırlandı. Yeni şifre: {new_password}', 'success')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/send_credentials', methods=['POST'])
@admin_required
def send_user_credentials(user_id):
    user = User.query.get_or_404(user_id)
    
    # Yeni şifre oluştur
    new_password = "dof123"  # Basit bir şifre, gerçek uygulamada rastgele oluşturulmalı
    user.set_password(new_password)
    db.session.commit()
    
    # Kullanıcıya e-posta gönderme işlemi (yeni merkezi mail servisi ile)
    try:
        from mail_service import MailService
        from flask import render_template
        
        subject = f"DÖF Bildirim Sistemi - Kullanıcı Bilgileriniz"
        
        # HTML içerikli e-posta oluştur
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                .content {{ padding: 15px; }}
                .info {{ background-color: #f0f8ff; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>DÖF Bildirim Sistemi - Kullanıcı Bilgileriniz</h2>
                </div>
                <div class="content">
                    <p>Sayın {user.first_name} {user.last_name},</p>
                    <p>DÖF Bildirim Sistemi'ne hoş geldiniz. Kullanıcı bilgileriniz aşağıda yer almaktadır:</p>
                    
                    <div class="info">
                        <p><strong>Kullanıcı Adı:</strong> {user.username}</p>
                        <p><strong>Şifre:</strong> {new_password}</p>
                    </div>
                    
                    <p>Sisteme giriş yaptıktan sonra güvenliğiniz için lütfen şifrenizi değiştirmeyi unutmayın.</p>
                    <p>Sisteme giriş yapmak için: <a href="{url_for('auth.login', _external=True)}">Buraya tıklayın</a></p>
                </div>
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayın.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # E-posta gönderim işlemi
        current_app.logger.info(f"Kullanıcı bilgileri e-posta gönderiliyor: {user.email}")
        try:
            result = MailService.send_email(
                subject=subject,
                recipients=[user.email],
                html_body=html_content
            )
            
            if result:
                current_app.logger.info(f"E-posta başarıyla gönderildi: {user.email}")
            else:
                current_app.logger.error(f"E-posta gönderilemedi: {user.email}")
                flash(f'{user.username} kişisine giriş bilgileri gönderilemedi! Mail sunucusu hatası.', 'danger')
                return redirect(url_for('admin.users'))
        except Exception as e:
            current_app.logger.error(f"E-posta gönderme hatası: {str(e)}")
            flash(f'{user.username} kişisine giriş bilgileri gönderilemedi! Hata: {str(e)}', 'danger')
            return redirect(url_for('admin.users'))
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Kullanıcı Bilgileri E-posta",
            details=f"Kullanıcı bilgileri e-posta ile gönderildi: {user.username}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'{user.username} kullanıcısına giriş bilgileri e-posta ile gönderildi.', 'success')
    except Exception as e:
        current_app.logger.error(f"Kullanıcı bilgileri e-postası gönderilemedi: {e}")
        flash(f'{user.username} kullanıcısına giriş bilgileri gönderilemedi! Hata: {e}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/departments')
@admin_required
def departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments/create', methods=['GET', 'POST'])
@admin_required
def create_department():
    form = DepartmentForm()
    
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            description=form.description.data,
            manager_id=form.manager.data if form.manager.data != 0 else None,
            is_active=form.is_active.data,
            created_at=datetime.now()
        )
        
        db.session.add(department)
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Departman Oluşturma",
            details=f"Departman oluşturuldu: {department.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'Departman {department.name} başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.departments'))
    
    return render_template('admin/create_department.html', form=form)

@admin_bp.route('/departments/<int:department_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    form = DepartmentForm(obj=department)
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.description = form.description.data
        department.manager_id = form.manager.data if form.manager.data != 0 else None
        department.is_active = form.is_active.data
        department.updated_at = datetime.now()
        
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Departman Güncelleme",
            details=f"Departman güncellendi: {department.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'Departman {department.name} başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.departments'))
    
    # Form alanlarını doldur
    if department.manager_id:
        form.manager.data = department.manager_id
    
    return render_template('admin/edit_department.html', form=form, department=department)

@admin_bp.route('/workflow')
@admin_required
def workflow():
    workflows = WorkflowDefinition.query.all()
    return render_template('admin/workflow.html', workflows=workflows)

@admin_bp.route('/workflow/create', methods=['GET', 'POST'])
@admin_required
def create_workflow():
    form = WorkflowDefinitionForm()
    
    if form.validate_on_submit():
        workflow = WorkflowDefinition(
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_at=datetime.now()
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="İş Akışı Oluşturma",
            details=f"İş akışı oluşturuldu: {workflow.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'İş akışı {workflow.name} başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.workflow'))
    
    return render_template('admin/create_workflow.html', form=form)

@admin_bp.route('/workflow/<int:workflow_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_workflow(workflow_id):
    workflow = WorkflowDefinition.query.get_or_404(workflow_id)
    form = WorkflowDefinitionForm(obj=workflow)
    
    if form.validate_on_submit():
        workflow.name = form.name.data
        workflow.description = form.description.data
        workflow.is_active = form.is_active.data
        workflow.updated_at = datetime.now()
        
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="İş Akışı Güncelleme",
            details=f"İş akışı güncellendi: {workflow.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'İş akışı {workflow.name} başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.workflow'))
    
    return render_template('admin/edit_workflow.html', form=form, workflow=workflow)

@admin_bp.route('/workflow/<int:workflow_id>/steps')
@admin_required
def workflow_steps(workflow_id):
    workflow = WorkflowDefinition.query.get_or_404(workflow_id)
    steps = WorkflowStep.query.filter_by(workflow_id=workflow_id).order_by(WorkflowStep.step_order).all()
    
    return render_template('admin/workflow_steps.html', workflow=workflow, steps=steps)

@admin_bp.route('/workflow/<int:workflow_id>/steps/create', methods=['GET', 'POST'])
@admin_required
def create_workflow_step(workflow_id):
    workflow = WorkflowDefinition.query.get_or_404(workflow_id)
    form = WorkflowStepForm()
    form.workflow_id.data = workflow_id
    
    if form.validate_on_submit():
        step = WorkflowStep(
            workflow_id=workflow_id,
            name=form.name.data,
            description=form.description.data,
            step_order=form.step_order.data,
            required_role=form.required_role.data,
            from_status=form.from_status.data,
            to_status=form.to_status.data,
            is_active=form.is_active.data
        )
        
        db.session.add(step)
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="İş Akışı Adımı Oluşturma",
            details=f"İş akışı adımı oluşturuldu: {step.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'İş akışı adımı {step.name} başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.workflow_steps', workflow_id=workflow_id))
    
    return render_template('admin/create_workflow_step.html', form=form, workflow=workflow)

@admin_bp.route('/workflow/<int:workflow_id>/steps/<int:step_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_workflow_step(workflow_id, step_id):
    workflow = WorkflowDefinition.query.get_or_404(workflow_id)
    step = WorkflowStep.query.get_or_404(step_id)
    
    if step.workflow_id != workflow_id:
        abort(404)
    
    form = WorkflowStepForm(obj=step)
    form.workflow_id.data = workflow_id
    
    if form.validate_on_submit():
        step.name = form.name.data
        step.description = form.description.data
        step.step_order = form.step_order.data
        step.required_role = form.required_role.data
        step.from_status = form.from_status.data
        step.to_status = form.to_status.data
        step.is_active = form.is_active.data
        
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="İş Akışı Adımı Güncelleme",
            details=f"İş akışı adımı güncellendi: {step.name}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash(f'İş akışı adımı {step.name} başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.workflow_steps', workflow_id=workflow_id))
    
    return render_template('admin/edit_workflow_step.html', form=form, workflow=workflow, step=step)

@admin_bp.route('/reports')
@admin_required
def reports():
    # DÖF sayıları - İlişkili DÖF'leri filtreleme
    # İlişkili DÖF'ler başlığında "[İlişkili #" prefix'i içerir
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    dof_counts = db.session.query(DOF.status, func.count(DOF.id)).filter(related_dof_filter).group_by(DOF.status).all()
    
    # Departman istatistikleri
    department_stats = get_department_stats()
    
    # DÖF Tipleri (Düzeltici/Önleyici) - İlişkili DÖF'leri filtrele
    dof_types = db.session.query(DOF.dof_type, func.count(DOF.id)).filter(related_dof_filter).group_by(DOF.dof_type).all()
    corrective_count = 0
    preventive_count = 0
    
    for dof_type, count in dof_types:
        if dof_type == 'corrective':
            corrective_count = count
        elif dof_type == 'preventive':
            preventive_count = count
    
    # Bugün ve bu hafta açılan DÖF'ler - İlişkili DÖF'leri filtrele
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    todays_count = DOF.query.filter(DOF.created_at.between(today, tomorrow), related_dof_filter).count()
    
    week_start = (today - timedelta(days=today.weekday()))
    weekly_count = DOF.query.filter(DOF.created_at >= week_start, related_dof_filter).count()
    
    # Acil işlem gerektiren DÖF'ler (öncelik alanı kaldırıldı) - İlişkili DÖF'leri filtrele
    # Bunun yerine son tarihi yaklaşan aktif DÖF'leri sayıyoruz
    next_week = today + timedelta(days=7)
    urgent_count = DOF.query.filter(
        DOF.due_date.between(today, next_week),
        DOF.status.notin_([5, 6, 7]),
        related_dof_filter
    ).count()
    
    # Geciken DÖF'ler (Son tarihi geçmiş ancak tamamlanmamış) - İlişkili DÖF'leri filtrele
    overdue_count = DOF.query.filter(
        DOF.due_date < today, 
        DOF.status.notin_([5, 6, 7]),
        related_dof_filter
    ).count()
    
    # Kalite onay süresi (Çözüldü durumundan Kapatıldı durumuna geçiş süresi)
    quality_subquery = db.session.query(
        DOFAction.dof_id,
        func.min(DOFAction.created_at).label('solved_date')
    ).filter(
        DOFAction.action_type == 2,  # 2: Durum Değişikliği
        DOFAction.new_status == 5    # 5: Çözüldü
    ).group_by(DOFAction.dof_id).subquery('quality_subquery')
    
    closed_subquery = db.session.query(
        DOFAction.dof_id,
        func.min(DOFAction.created_at).label('closed_date')
    ).filter(
        DOFAction.action_type == 2,  # 2: Durum Değişikliği
        DOFAction.new_status == 6    # 6: Kapatıldı
    ).group_by(DOFAction.dof_id).subquery('closed_subquery')
    
    quality_approval_time_result = db.session.query(
        func.avg(closed_subquery.c.closed_date - quality_subquery.c.solved_date)
    ).join(
        quality_subquery,
        closed_subquery.c.dof_id == quality_subquery.c.dof_id
    ).scalar()
    
    if quality_approval_time_result is not None:
        # Decimal nesnesini float'a çevirip saniye cinsinden gün sayısına dönüştür
        try:
            # Eğer timedelta nesnesi ise
            if hasattr(quality_approval_time_result, 'total_seconds'):
                quality_approval_time = quality_approval_time_result.total_seconds() / (24 * 3600)
            else:
                # Decimal nesnesini doğrudan float'a çevirip gün cinsine dönüştür (saniye varsayımı)
                quality_approval_time = float(quality_approval_time_result) / (24 * 3600)
        except (AttributeError, TypeError):
            # Hata durumunda varsayılan değer
            quality_approval_time = 0
    else:
        quality_approval_time = 0
    
    # Son 6 ayın DÖF sayıları - İlişkili DÖF'leri filtrele
    months = []
    monthly_counts = []
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        month_name = date.strftime('%B %Y')
        months.append(month_name)
        
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            end_date = (date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            end_date = datetime.now()
            
        count = DOF.query.filter(DOF.created_at.between(start_date, end_date), related_dof_filter).count()
        monthly_counts.append(count)
    
    # Ortalama çözüm süresi - İlişkili DÖF'leri filtrele
    avg_resolution_time = db.session.query(
        func.avg(DOFAction.created_at - DOF.created_at)
    ).join(DOF).filter(
        DOFAction.action_type == 2,     # 2: Durum Değişikliği
        DOFAction.new_status == 6,      # 6: Kapatıldı
        related_dof_filter              # İlişkili DÖF'leri filtrele
    ).scalar()
    
    if avg_resolution_time is not None:
        # Decimal nesnesini doğrudan float'a çevirip gün cinsine dönüştür
        avg_resolution_time = float(avg_resolution_time) / (24 * 3600)  # Gün cinsinden
    else:
        avg_resolution_time = 0
    
    # En aktif kullanıcılar
    active_users = db.session.query(User.username, func.count(DOFAction.id).label('action_count'))\
    .join(DOFAction, DOFAction.user_id == User.id)\
    .group_by(User.username)\
    .order_by(desc('action_count'))\
    .limit(5).all()
    
    return render_template('admin/reports.html',
                          dof_counts=dof_counts,
                          department_stats=department_stats,
                          months=months,
                          monthly_counts=monthly_counts,
                          avg_resolution_time=avg_resolution_time,
                          active_users=active_users,
                          corrective_count=corrective_count,
                          DOFStatus=DOFStatus,
                          preventive_count=preventive_count,
                          todays_count=todays_count,
                          weekly_count=weekly_count,
                          high_priority_count=urgent_count,  # Template uyumlulugu icin eski ad korundu
                          overdue_count=overdue_count,
                          quality_approval_time=quality_approval_time)

@admin_bp.route('/reports/export')
@admin_required
def export_reports():
    # Raporlar sayfasındaki aynı veriyi al
    format_type = request.args.get('format', 'excel')
    
    # İlişkili DÖF'leri filtreleme (başlığında "[İlişkili #" içerenler)
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    
    # DOF sayıları - ilişkili DÖF'leri filtrele
    dof_counts = db.session.query(DOF.status, func.count(DOF.id))\
        .filter(related_dof_filter)\
        .group_by(DOF.status).all()
    
    # Departman istatistikleri
    department_stats = get_department_stats()
    
    # DÖF Tipleri (Düzeltici/Önleyici) - ilişkili DÖF'leri filtrele
    dof_types = db.session.query(DOF.dof_type, func.count(DOF.id))\
        .filter(related_dof_filter)\
        .group_by(DOF.dof_type).all()
    corrective_count = 0
    preventive_count = 0
    
    for dof_type, count in dof_types:
        if dof_type == 'corrective':
            corrective_count = count
        elif dof_type == 'preventive':
            preventive_count = count
    
    # Bugün ve bu hafta açılan DÖF'ler - ilişkili DÖF'leri filtrele
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    todays_count = DOF.query.filter(DOF.created_at.between(today, tomorrow))\
        .filter(related_dof_filter).count()
    
    week_start = (today - timedelta(days=today.weekday()))
    weekly_count = DOF.query.filter(DOF.created_at >= week_start)\
        .filter(related_dof_filter).count()
    
    # Excel formatında dışa aktarma
    if format_type == 'excel':
        import pandas as pd
        from io import BytesIO
        
        # Excel dosyası oluştur
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        # DÖF Durumları
        status_data = []
        for status_code, count in dof_counts:
            status_data.append({
                'Durum Kodu': status_code,
                'Durum': DOFStatus.get_label(status_code),
                'DÖF Sayısı': count
            })
        
        status_df = pd.DataFrame(status_data)
        status_df.to_excel(writer, sheet_name='DOF_Durumları', index=False)
        
        # Departman İstatistikleri
        dept_data = []
        for stat in department_stats:
            dept_data.append({
                'Departman': stat['department'],
                'Toplam DÖF': stat['total'],
                'Açık DÖF': stat['open'],
                'Kapalı DÖF': stat['closed'],
                'Son 30 Gün DÖF': stat['recent'],
                'Ortalama Çözüm Süresi (Gün)': stat['avg_resolution_time'] if 'avg_resolution_time' in stat else 0
            })
        
        dept_df = pd.DataFrame(dept_data)
        dept_df.to_excel(writer, sheet_name='Departman_İstatistikleri', index=False)
        
        # Özet Bilgiler
        summary_data = [
            {'Metrik': 'Toplam DÖF', 'Değer': sum([count for _, count in dof_counts])},
            {'Metrik': 'Düzeltici Faaliyet', 'Değer': corrective_count},
            {'Metrik': 'Önleyici Faaliyet', 'Değer': preventive_count},
            {'Metrik': 'Bugün Açılan', 'Değer': todays_count},
            {'Metrik': 'Bu Hafta Açılan', 'Değer': weekly_count},
        ]
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        # Excel dosyasını kaydet
        writer.close()
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"DOF_Rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    # PDF formatında dışa aktarma
    elif format_type == 'pdf':
        from fpdf import FPDF
        import tempfile
        import os
        
        # PDF oluştur
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Başlık ekle
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "DÖF Sistem Raporu", ln=True, align="C")
        pdf.cell(0, 5, f"Oluşturma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        
        # Özet bilgiler
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Özet Bilgiler", ln=True)
        pdf.ln(2)
        
        # Tablo formatında özet bilgiler
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(100, 8, "Metrik", 1, 0, "C", True)
        pdf.cell(80, 8, "Değer", 1, 1, "C", True)
        
        pdf.set_font("helvetica", "", 10)
        total_dofs = sum([count for _, count in dof_counts])
        pdf.cell(100, 8, "Toplam DÖF", 1, 0, "L")
        pdf.cell(80, 8, str(total_dofs), 1, 1, "C")
        
        pdf.cell(100, 8, "Düzeltici Faaliyet", 1, 0, "L")
        pdf.cell(80, 8, str(corrective_count), 1, 1, "C")
        
        pdf.cell(100, 8, "Önleyici Faaliyet", 1, 0, "L")
        pdf.cell(80, 8, str(preventive_count), 1, 1, "C")
        
        pdf.cell(100, 8, "Bugün Açılan DÖF", 1, 0, "L")
        pdf.cell(80, 8, str(todays_count), 1, 1, "C")
        
        pdf.cell(100, 8, "Bu Hafta Açılan DÖF", 1, 0, "L")
        pdf.cell(80, 8, str(weekly_count), 1, 1, "C")
        
        pdf.ln(15)
        
        # DÖF Durumları tablosu
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "DÖF Durumları", ln=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(20, 8, "Kod", 1, 0, "C", True)
        pdf.cell(100, 8, "Durum", 1, 0, "C", True)
        pdf.cell(60, 8, "DÖF Sayısı", 1, 1, "C", True)
        
        pdf.set_font("helvetica", "", 10)
        for status_code, count in dof_counts:
            pdf.cell(20, 8, str(status_code), 1, 0, "C")
            pdf.cell(100, 8, DOFStatus.get_label(status_code), 1, 0, "L")
            pdf.cell(60, 8, str(count), 1, 1, "C")
        
        # PDF dosyasını kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name
        
        return_value = send_file(
            tmp_path,
            as_attachment=True,
            download_name=f"DOF_Rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        
        # Geçici dosyayı sil
        os.unlink(tmp_path)
        
        return return_value
    
    # Geçersiz format
    else:
        flash('Geçersiz rapor formatı.', 'danger')
        return redirect(url_for('admin.reports'))

@admin_bp.route('/logs')
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = SystemLog.query.order_by(SystemLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/logs.html', logs=logs)


@admin_bp.route('/email-settings', methods=['GET', 'POST'])
@admin_required
def email_settings():
    # Sadece admin rolüne sahip kullanıcılar bu sayfaya erişebilir
    if current_user.role != UserRole.ADMIN:
        flash('Bu sayfaya sadece admin erişebilir.', 'danger')
        return redirect(url_for('dof.dashboard'))
    
    from models import EmailSettings
    form = EmailSettingsForm()
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # Mevcut e-posta ayarlarını veritabanından al
    settings = EmailSettings.query.first()
    if not settings:
        # İlk kez ayarları oluştururken Gmail bilgilerini doğrudan ayarla
        settings = EmailSettings(
            mail_service="gmail",
            smtp_host="smtp.gmail.com",
            smtp_port=465,
            smtp_use_tls=False,
            smtp_use_ssl=True,
            smtp_user="alikokrtv@gmail.com",
            smtp_pass="iczu jvha gavw rnlh",
            default_sender="alikokrtv@gmail.com"
        )
        db.session.add(settings)
        db.session.commit()
    
    if form.validate_on_submit():
        # Form verileri doğrulandı
        if form.mail_service.data == 'smtp':
            settings.mail_service = 'smtp'
            settings.smtp_host = form.smtp_host.data
            settings.smtp_port = form.smtp_port.data
            settings.smtp_use_tls = form.smtp_use_tls.data
            settings.smtp_use_ssl = form.smtp_use_ssl.data
            settings.smtp_user = form.smtp_user.data
            # Yeni şifre girilmişse güncelle, boşsa eski şifreyi sakla
            if form.smtp_pass.data:
                settings.smtp_pass = form.smtp_pass.data
            settings.default_sender = form.default_sender.data
        else:  # Gmail
            settings.mail_service = 'gmail'
            settings.smtp_host = 'smtp.gmail.com'
            settings.smtp_port = 465 if form.smtp_use_ssl.data else 587
            settings.smtp_use_tls = not form.smtp_use_ssl.data
            settings.smtp_use_ssl = form.smtp_use_ssl.data
            settings.smtp_user = form.smtp_user.data
            # Yeni şifre girilmişse güncelle, boşsa eski şifreyi sakla
            if form.smtp_pass.data:
                settings.smtp_pass = form.smtp_pass.data
            settings.default_sender = form.default_sender.data
        
        # Güncelleyen kullanıcıyı ayarla
        settings.updated_by = current_user.id
        
        # Veritabanına kaydet
        db.session.commit()
        
        # .env dosyasına da kaydet (geriye uyumluluk için)
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
                        
        # Ayarları env_vars'a ekle
        env_vars['MAIL_SERVER'] = settings.smtp_host
        env_vars['MAIL_PORT'] = str(settings.smtp_port)
        env_vars['MAIL_USE_TLS'] = str(settings.smtp_use_tls)
        env_vars['MAIL_USE_SSL'] = str(settings.smtp_use_ssl)
        env_vars['MAIL_USERNAME'] = settings.smtp_user
        env_vars['MAIL_PASSWORD'] = settings.smtp_pass
        env_vars['MAIL_DEFAULT_SENDER'] = settings.default_sender
        
        # .env dosyasına kaydet
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Uygulama yapılandırmasını güncelle
        current_app.config['MAIL_SERVER'] = settings.smtp_host
        current_app.config['MAIL_PORT'] = settings.smtp_port
        current_app.config['MAIL_USE_TLS'] = settings.smtp_use_tls
        current_app.config['MAIL_USE_SSL'] = settings.smtp_use_ssl
        current_app.config['MAIL_USERNAME'] = settings.smtp_user
        current_app.config['MAIL_PASSWORD'] = settings.smtp_pass
        current_app.config['MAIL_DEFAULT_SENDER'] = settings.default_sender
        
        # Ayarların kaydedildiğini doğrula
        current_app.logger.info(f"E-posta ayarları güncellendi: {settings.smtp_user}")
        current_app.logger.info(f"SMTP Ayarları: {settings.smtp_host}:{settings.smtp_port}")
        
        # Diğer modüllerin yapılandırmaya erişebilmesi için os.environ'a da ekleyelim
        os.environ['MAIL_SERVER'] = settings.smtp_host
        os.environ['MAIL_PORT'] = str(settings.smtp_port)
        os.environ['MAIL_USE_TLS'] = str(settings.smtp_use_tls)
        os.environ['MAIL_USE_SSL'] = str(settings.smtp_use_ssl)
        os.environ['MAIL_USERNAME'] = settings.smtp_user
        os.environ['MAIL_PASSWORD'] = settings.smtp_pass
        os.environ['MAIL_DEFAULT_SENDER'] = settings.default_sender
        
        # Mail nesnesini yeniden yapılandır
        mail.init_app(current_app)
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="E-posta Ayarları Güncelleme",
            details=f"E-posta ayarları güncellendi. Servis: {form.mail_service.data}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash('E-posta ayarları başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.email_settings'))
    
    # Form alanlarını veritabanındaki ayarlarla doldur
    if request.method == 'GET':
        # Veritabanından ayarları al
        from models import EmailSettings
        settings = EmailSettings.query.first()
        
        if settings:
            # Veritabanından gelen değerlerle formu doldur
            form.mail_service.data = settings.mail_service
            form.smtp_host.data = settings.smtp_host
            form.smtp_port.data = settings.smtp_port
            form.smtp_use_tls.data = settings.smtp_use_tls
            form.smtp_use_ssl.data = settings.smtp_use_ssl
            form.smtp_user.data = settings.smtp_user
            # Şifre alanını da veritabanından al
            form.smtp_pass.data = settings.smtp_pass
            form.default_sender.data = settings.default_sender
        else:
            # Ayarlar yoksa varsayılan değerleri kullan
            form.mail_service.data = 'smtp'
            form.smtp_host.data = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            form.smtp_port.data = current_app.config.get('MAIL_PORT', 587)
            form.smtp_use_tls.data = current_app.config.get('MAIL_USE_TLS', True)
            form.smtp_use_ssl.data = current_app.config.get('MAIL_USE_SSL', False)
            form.smtp_user.data = current_app.config.get('MAIL_USERNAME', '')
            form.default_sender.data = current_app.config.get('MAIL_DEFAULT_SENDER', '')
    
    return render_template('admin/email_settings.html', form=form)

@admin_bp.route('/test-email')
@admin_required
def test_email():
    # Sadece admin rolüne sahip kullanıcılar erişebilir
    if current_user.role != UserRole.ADMIN:
        flash('Bu sayfaya sadece admin erişebilir.', 'danger')
        return redirect(url_for('dof.dashboard'))
    
    try:
        # Ayarları kontrol et
        from models import EmailSettings
        settings = EmailSettings.query.first()
        
        if not settings or not settings.smtp_user or not settings.smtp_pass:
            flash('E-posta ayarları eksik veya tamamlanmamış. Lütfen ayarları tamamlayın.', 'danger')
            return redirect(url_for('admin.email_settings'))
            
        # Google hesabı için 'Uygulama Şifresi' kontrolü
        # Gmail ayarlarını otomatik olarak düzelt
        if 'gmail.com' in settings.smtp_user.lower():
            # Gmail için her zaman bu ayarları kullan
            settings.smtp_host = 'smtp.gmail.com'
            settings.smtp_port = 465
            settings.smtp_use_ssl = True
            settings.smtp_use_tls = False
            
            # Mail nesnesini yeniden yapılandır
            current_app.config['MAIL_SERVER'] = 'smtp.gmail.com'
            current_app.config['MAIL_PORT'] = 465
            current_app.config['MAIL_USE_SSL'] = True
            current_app.config['MAIL_USE_TLS'] = False
            current_app.config['MAIL_USERNAME'] = settings.smtp_user
            current_app.config['MAIL_PASSWORD'] = settings.smtp_pass
            mail.init_app(current_app)
            
            # Debug için logla
            current_app.logger.info(f"Gmail için ayarlar otomatik düzeltildi: SSL=True, Port=465")
            
            # Ve veritabanına kaydet
            db.session.commit()
            
            # Eğer şifre 16 karakterden kısaysa
            if settings.smtp_pass and len(settings.smtp_pass) < 16:
                flash('Gmail hesabı için normal şifre yerine "Uygulama Şifresi" kullanmanız gerekebilir. Gmail güvenlik ayarlarınızdan uygulama şifresi oluşturun.', 'warning')
            
        # Test e-postası için ayarları yeniden yükle
        recipient = current_user.email
        subject = "DÖF Sistemi - Test E-postası ({})".format(datetime.now().strftime('%H:%M:%S'))
        
        # Gmail için doğru ayarları mail config'e zorla (uygulama yeniden başlamadan yapılandırmayı güncellemek için)
        current_app.config['MAIL_SERVER'] = settings.smtp_host
        current_app.config['MAIL_PORT'] = settings.smtp_port
        current_app.config['MAIL_USE_SSL'] = settings.smtp_use_ssl
        current_app.config['MAIL_USE_TLS'] = settings.smtp_use_tls
        current_app.config['MAIL_USERNAME'] = settings.smtp_user
        current_app.config['MAIL_PASSWORD'] = settings.smtp_pass
        # Varsayılan göndereni formdan al
        if settings.default_sender and '@' in settings.default_sender:
            current_app.config['MAIL_DEFAULT_SENDER'] = settings.default_sender
        else:
            # Eğer geçerli değilse smtp_user'i kullan
            current_app.config['MAIL_DEFAULT_SENDER'] = settings.smtp_user
        
        # Mail servisi yeniden yükle
        mail.init_app(current_app)
        
        # Şimdi e-posta gönder
        current_app.logger.info(f"Test E-posta gönderme denemesi: {settings.smtp_host}:{settings.smtp_port}")
        current_app.logger.info(f"Kullanıcı: {settings.smtp_user}, TLS: {settings.smtp_use_tls}, SSL: {settings.smtp_use_ssl}")
        current_app.logger.info(f"Şifre Uzunluğu: {len(settings.smtp_pass)}")
        
        # Debug için Flask-Mail ayarlarını kontrol et
        for key in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_SSL', 'MAIL_USE_TLS', 'MAIL_USERNAME', 'MAIL_DEFAULT_SENDER']:
            current_app.logger.info(f"Flask-Mail ayarı: {key}={current_app.config.get(key)}")
        current_app.logger.info(f"MAIL_PASSWORD uzunluğu: {len(current_app.config.get('MAIL_PASSWORD', ''))}")
        
        body_html = """
        <html>
            <body>
                <h2>DÖF Sistemi - Test E-postası</h2>
                <p>Bu bir test e-postasıdır.</p>
                <p>E-posta ayarlarınız başarıyla yapılandırılmıştır.</p>
                <p>Tarih/Saat: {}</p>
                <p>Sunucu: {} (Port: {})</p>
                <p>TLS/SSL: {}/{}</p>
                <p>Kullanıcı: {}</p>
            </body>
        </html>
        """.format(
            datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_use_tls,
            settings.smtp_use_ssl,
            settings.smtp_user
        )

        from utils import send_email
        # E-posta takip sistemi ile gönder
        result = send_email(subject, [recipient], body_html)
        current_app.logger.info(f"Test e-postası takip sistemi ile gönderildi")

        if result:
            # Log kaydı oluştur
            log_activity(
                user_id=current_user.id,
                action="Test E-postası Gönderimi",
                details=f"Test e-postası gönderildi: {recipient}",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            flash('Test e-postası başarıyla gönderildi. Lütfen gelen kutunuzu kontrol edin.', 'success')
        else:
            # Gmail için özel kontroller
            if 'gmail.com' in settings.smtp_user.lower():
                flash('Gmail hesabı için: (1) "Daha az güvenli uygulama erişimi" ayarınızı açık olduğundan emin olun, veya (2) Google hesabınızdan 16 haneli bir Uygulama Şifresi oluşturun.', 'warning')
            flash('Test e-postası gönderilirken bir hata oluştu. Lütfen sistem loglarını kontrol edin ve e-posta ayarlarınızı gözden geçirin.', 'danger')
    
    except Exception as e:
        current_app.logger.error(f"Test e-postası hatası: {str(e)}")
        flash(f'Test e-postası gönderilirken bir hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('admin.email_settings'))

@admin_bp.route('/workflow/setup_default', methods=['POST'])
@admin_required
def setup_default_workflow():
    """Varsayılan DÖF iş akışını oluşturur"""
    try:
        # Önce mevcut varsayılan akış var mı kontrol et
        existing_workflow = WorkflowDefinition.query.filter_by(name='Varsayılan DÖF İş Akışı').first()
        if existing_workflow:
            flash('Varsayılan iş akışı zaten mevcut!', 'warning')
            return redirect(url_for('admin.workflow'))
        
        # Yeni iş akışı oluştur
        workflow = WorkflowDefinition(
            name='Varsayılan DÖF İş Akışı',
            description='Standart DÖF sürecini tanımlayan varsayılan iş akışı',
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(workflow)
        db.session.flush()  # ID oluşturmak için
        
        # İş akışı adımlarını oluştur
        steps = [
            {
                'name': 'DÖF Oluşturma',
                'description': 'Kullanıcı tarafından DÖF oluşturulması',
                'step_order': 1,
                'required_role': UserRole.USER,
                'from_status': DOFStatus.DRAFT,
                'to_status': DOFStatus.SUBMITTED
            },
            {
                'name': 'Kalite İncelemesi',
                'description': 'Kalite yöneticisi tarafından DÖF incelemesi',
                'step_order': 2,
                'required_role': UserRole.QUALITY_MANAGER,
                'from_status': DOFStatus.SUBMITTED,
                'to_status': DOFStatus.IN_REVIEW
            },
            {
                'name': 'Departman Ataması',
                'description': 'Kalite yöneticisi tarafından departmana atama',
                'step_order': 3,
                'required_role': UserRole.QUALITY_MANAGER,
                'from_status': DOFStatus.IN_REVIEW,
                'to_status': DOFStatus.ASSIGNED
            },
            {
                'name': 'Kök Neden ve Aksiyon Planı',
                'description': 'Departman yöneticisi tarafından kök neden analizi ve aksiyon planı hazırlanması',
                'step_order': 4,
                'required_role': UserRole.DEPARTMENT_MANAGER,
                'from_status': DOFStatus.ASSIGNED,
                'to_status': DOFStatus.PLANNING
            },
            {
                'name': 'Plan Onayı',
                'description': 'Kalite yöneticisi tarafından aksiyon planı onayı',
                'step_order': 5,
                'required_role': UserRole.QUALITY_MANAGER,
                'from_status': DOFStatus.PLANNING,
                'to_status': DOFStatus.IMPLEMENTATION
            },
            {
                'name': 'Aksiyon Uygulama',
                'description': 'Departman tarafından aksiyonların uygulanması',
                'step_order': 6,
                'required_role': UserRole.DEPARTMENT_MANAGER,
                'from_status': DOFStatus.IMPLEMENTATION,
                'to_status': DOFStatus.COMPLETED
            },
            {
                'name': 'Kaynak Onayı',
                'description': 'DÖF oluşturan departman tarafından çözümün onaylanması',
                'step_order': 7,
                'required_role': UserRole.DEPARTMENT_MANAGER,
                'from_status': DOFStatus.COMPLETED,
                'to_status': DOFStatus.RESOLVED
            },
            {
                'name': 'Final Kapatma',
                'description': 'Kalite yöneticisi tarafından DÖF\'ün kapatılması',
                'step_order': 8,
                'required_role': UserRole.QUALITY_MANAGER,
                'from_status': DOFStatus.RESOLVED,
                'to_status': DOFStatus.CLOSED
            }
        ]
        
        for step_data in steps:
            step = WorkflowStep(
                workflow_id=workflow.id,
                **step_data,
                is_active=True
            )
            db.session.add(step)
        
        db.session.commit()
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Varsayılan İş Akışı Oluşturma",
            details="Varsayılan DÖF iş akışı oluşturuldu",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash('Varsayılan DÖF iş akışı başarıyla oluşturuldu!', 'success')
        return redirect(url_for('admin.workflow_steps', workflow_id=workflow.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Varsayılan iş akışı oluşturma hatası: {str(e)}")
        flash(f'İş akışı oluşturulurken hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('admin.workflow'))

@admin_bp.route('/test_notification')
@admin_required
def test_notification():
    """Test bildirimi gönder"""
    try:
        from notification_system import send_notification
        
        # Mevcut kullanıcıya test bildirimi gönder
        notification = send_notification(
            user_id=current_user.id,
            message=f"Test bildirimi - {datetime.now().strftime('%H:%M:%S')}",
            dof_id=None,
            send_email=True
        )
        
        if notification:
            flash("Test bildirimi başarıyla gönderildi! Bildirimlerinizi ve e-postanızı kontrol edin.", "success")
        else:
            flash("Test bildirimi gönderilemedi.", "danger")
            
    except Exception as e:
        flash(f"Test bildirimi hatası: {str(e)}", "danger")
        current_app.logger.error(f"Test bildirimi hatası: {str(e)}")
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/email_tracking')
@admin_required
def email_tracking():
    """E-posta takip sayfası"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtreleme parametreleri
    status_filter = request.args.get('status', 'all')
    date_from = request.args.get('date_from', type=str)
    date_to = request.args.get('date_to', type=str)
    
    # Sorgu oluştur
    query = EmailTrack.query
    
    # Status filtresi
    if status_filter != 'all':
        query = query.filter(EmailTrack.status == status_filter)
    
    # Tarih filtreleri
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(EmailTrack.created_at >= date_from_obj)
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı', 'warning')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(EmailTrack.created_at <= date_to_obj)
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı', 'warning')
    
    # Sonuçları sırala ve sayfalandır
    emails = query.order_by(desc(EmailTrack.created_at)).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # İstatistikler
    total_emails = EmailTrack.query.count()
    sent_emails = EmailTrack.query.filter_by(status='sent').count()
    failed_emails = EmailTrack.query.filter_by(status='failed').count()
    queued_emails = EmailTrack.query.filter_by(status='queued').count()
    
    stats = {
        'total': total_emails,
        'sent': sent_emails,
        'failed': failed_emails,
        'queued': queued_emails,
        'success_rate': round((sent_emails / total_emails * 100) if total_emails > 0 else 0, 1)
    }
    
    return render_template('admin/email_tracking.html', 
                          emails=emails,
                          stats=stats,
                          selected_status=status_filter,
                          selected_date_from=date_from,
                          selected_date_to=date_to)

@admin_bp.route('/email_scheduler', methods=['GET', 'POST'])
@admin_required
def email_scheduler():
    """E-posta zamanlayıcısı yönetimi"""
    from daily_email_scheduler import get_scheduler_status, test_daily_report, init_scheduler, stop_scheduler
    from flask import request, flash, redirect, url_for, render_template
    
    if request.method == 'POST':
        action = request.form.get('action')
        print(f"DEBUG: Received action = {action}")  # Debug için
        
        if action == 'start':
            try:
                scheduler = init_scheduler()
                if scheduler:
                    flash('✅ E-posta zamanlayıcısı başlatıldı', 'success')
                else:
                    flash('❌ E-posta zamanlayıcısı başlatılamadı', 'danger')
            except Exception as e:
                flash(f'❌ Hata: {str(e)}', 'danger')
                
        elif action == 'stop':
            try:
                stop_scheduler()
                flash('🛑 E-posta zamanlayıcısı durduruldu', 'info')
            except Exception as e:
                flash(f'❌ Hata: {str(e)}', 'danger')
                
        elif action == 'test':
            try:
                test_daily_report()
                flash('🧪 Test raporu gönderildi', 'success')
            except Exception as e:
                flash(f'❌ Test hatası: {str(e)}', 'danger')
        
        elif action == 'preview':
            # Önizleme modunda - sadece bilgileri göster, gönderme
            print("DEBUG: Preview action triggered")  # Debug için
            return redirect(url_for('admin.email_scheduler', preview=1))
        
        return redirect(url_for('admin.email_scheduler'))
    
    # Scheduler durumunu getir
    status = get_scheduler_status()
    
    # Önizleme modu kontrolü
    preview_mode = request.args.get('preview') == '1'
    preview_data = None
    print(f"DEBUG: preview_mode = {preview_mode}, preview arg = {request.args.get('preview')}")  # Debug için
    
    if preview_mode:
        # E-posta önizleme verilerini hazırla
        from daily_email_scheduler import get_user_managed_departments, get_dof_statistics
        from models import User, UserRole
        
        try:
            # E-posta alacak kullanıcıları getir
            report_recipients = User.query.filter(
                User.role.in_([
                    UserRole.DEPARTMENT_MANAGER,
                    UserRole.GROUP_MANAGER,
                    UserRole.DIRECTOR,
                    UserRole.QUALITY_MANAGER
                ]),
                User.active == True,
                User.email.isnot(None),
                User.email != ''
            ).all()
            
            # Her kullanıcı için detayları hazırla
            recipient_details = []
            for user in report_recipients:
                departments = get_user_managed_departments(user)
                if departments:
                    department_ids = [dept.id for dept in departments]
                    statistics = get_dof_statistics(department_ids)
                    
                    # ÖNEMLI: Sadece DÖF'ü olan kullanıcıları göster
                    if statistics:
                        total_dofs = statistics.get('total_open', 0) + statistics.get('total_closed_week', 0)
                        if total_dofs > 0:  # DÖF'ü varsa listeye ekle
                            recipient_details.append({
                                'user': user,
                                'departments': departments,
                                'statistics': statistics
                            })
            
            preview_data = {
                'total_recipients': len(recipient_details),
                'recipients': recipient_details[:10]  # İlk 10 tanesi
            }
            
        except Exception as e:
            flash(f'❌ Önizleme hazırlanırken hata: {str(e)}', 'danger')
            preview_data = None
    
    # Son 7 günlük e-posta istatistikleri
    from datetime import datetime, timedelta
    from models import EmailTrack
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Son 7 günde gönderilen günlük rapor e-postaları
    daily_report_emails = EmailTrack.query.filter(
        EmailTrack.subject.like('%Günlük DÖF Raporu%'),
        EmailTrack.created_at >= seven_days_ago
    ).all()
    
    # İstatistikleri hesapla
    total_emails = len(daily_report_emails)
    sent_emails = len([e for e in daily_report_emails if e.status == 'sent'])
    failed_emails = len([e for e in daily_report_emails if e.status == 'failed'])
    
    email_stats = {
        'total': total_emails,
        'sent': sent_emails,
        'failed': failed_emails,
        'success_rate': round((sent_emails / total_emails * 100) if total_emails > 0 else 0, 1)
    }
    
    return render_template('admin/email_scheduler.html', 
                         scheduler_status=status,
                         email_stats=email_stats,
                         recent_emails=daily_report_emails[:10],
                         preview_mode=preview_mode,
                         preview_data=preview_data)
