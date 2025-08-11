from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
# app ve db lazy import olarak fonksiyonlarda kullanılacak
from models import User, SystemLog, UserRole, Department, UserDepartmentMapping, DirectorManagerMapping
from forms import LoginForm, RegisterForm, UserProfileForm, ChangePasswordForm, ForgotPasswordForm
from utils import log_activity
import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# Defer app/db imports to avoid circular
from extensions import db

auth_bp = Blueprint('auth', __name__)

def _get_serializer():
    # Uygulama bağlamı içinde güvenli bir şekilde serializer oluştur
    from flask import current_app
    secret = current_app.config.get('SECRET_KEY')
    return URLSafeTimedSerializer(secret)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dof.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Bu hesap devre dışı bırakılmış.', 'danger')
                return render_template('login.html', form=form, now=datetime.datetime.now())
            
            login_user(user, remember=form.remember.data)
            
            # Son giriş tarihini güncelle
            user.last_login = datetime.datetime.now()
            db.session.commit()
            
            # Log kaydı oluştur
            log_activity(
                user_id=user.id,
                action="Giriş Yapıldı",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dof.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
    
    return render_template('login.html', form=form, now=datetime.datetime.now())

@auth_bp.route('/logout')
@login_required
def logout():
    # Log kaydı oluştur
    log_activity(
        user_id=current_user.id,
        action="Çıkış Yapıldı",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Sadece Admin veya Kalite Yöneticisi kullanıcı ekleyebilir
    if current_user.role not in [1, 2]:  # 1: Admin, 2: Kalite Yöneticisi
        flash('Bu işlemi gerçekleştirmek için yetkiniz yok.', 'danger')
        return redirect(url_for('dof.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Rolü al ve gerekli işlemleri yap
        selected_role = form.role.data
        
        # Bölge Müdürü rolü için departman ilişkisi özel olarak işlenmeli
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=selected_role,
            is_active=True,
            created_at=datetime.datetime.now()
        )
        
        # Role göre departman ilişkilerini ayarla
        if selected_role == UserRole.DEPARTMENT_MANAGER or selected_role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
            user.department_id = form.department.data if form.department.data != 0 else None
        elif selected_role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            user.department_id = None  # Grup yöneticisi doğrudan bir departmana bağlı değil
        elif selected_role == UserRole.DIRECTOR:
            user.department_id = None  # Direktör de doğrudan bir departmana bağlı değil
        else:
            user.department_id = form.department.data if form.department.data != 0 else None
            
        user.set_password(form.password.data)
        
        # Şifre bilgisini saklayalım, e-posta için kullanacağız
        password = form.password.data
        
        db.session.add(user)
        db.session.commit()
        
        # Bölge Müdürü veya Direktör ise çoklu ilişkileri ekle
        try:
            # Çoklu departman yöneticisi için çoklu departman ilişkisi ekle
            if selected_role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING] and form.managed_departments.data:
                current_app.logger.info(f"Çoklu departman yöneticisi için departman ataması: {form.managed_departments.data}")
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

            # Direktör için yönetilen bölge müdürleri ve departmanlar ilişkisi ekle
            if selected_role == UserRole.DIRECTOR:
                # Çoklu departman ilişkisi ekle
                if form.managed_departments.data:
                    current_app.logger.info(f"Direktör için departman ataması: {form.managed_departments.data}")
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
                
                # Direktör-Bölge Müdürü ilişkilerini kaydet
                if form.managed_managers.data:
                    current_app.logger.info(f"Direktör için bölge müdürü ataması: {form.managed_managers.data}")
                    
                    # Her bir seçilen bölge müdürü için ilişki oluştur
                    for manager_id in form.managed_managers.data:
                        # ID'nin integer olduğundan emin ol
                        manager_id = int(manager_id) if not isinstance(manager_id, int) else manager_id
                        
                        # Çoklu departman yöneticisinin varlığını kontrol et
                        manager = User.query.get(manager_id)
                        if manager and manager.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                            # DirectorManagerMapping tablosuna kayıt ekle
                            mapping = DirectorManagerMapping(
                                director_id=user.id, 
                                manager_id=manager_id
                            )
                            db.session.add(mapping)
                            current_app.logger.info(f"Direktör-Bölge Müdürü ilişkisi oluşturuldu: Direktör={user.id}, Bölge Müdürü={manager_id}")
                        else:
                            current_app.logger.error(f"Bölge müdürü bulunamadı veya rolü uygun değil ID: {manager_id}")
                
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Bölge müdürü departman ataması hatası: {str(e)}")
            flash(f'Kullanıcı oluşturuldu ancak departman atama işlemi sırasında hata: {str(e)}', 'warning')
        
        # Log kaydı oluştur
        log_activity(
            user_id=current_user.id,
            action="Kullanıcı Oluşturma",
            details=f"Kullanıcı oluşturuldu: {user.username}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        # Kullanıcıya bilgilerini e-posta olarak gönder
        try:
            from utils import send_email
            
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
                            <p><strong>Şifre:</strong> {password}</p>
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
            
            # Düz metin içeriği
            plain_text = f"""
            Sayın {user.first_name} {user.last_name},
            
            DÖF Bildirim Sistemi'ne hoş geldiniz. Kullanıcı bilgileriniz aşağıda yer almaktadır:
            
            Kullanıcı Adı: {user.username}
            Şifre: {password}
            
            Sisteme giriş yaptıktan sonra güvenliğiniz için lütfen şifrenizi değiştirmeyi unutmayın.
            Sisteme giriş yapmak için: {url_for('auth.login', _external=True)}
            
            Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayın.
            """
            
            # Doğrudan Flask-Mail kullanarak e-posta gönderimi (şifre sıfırlama mantığı gibi)
            from flask_mail import Message
            from app import mail
            
            # E-posta ayarlarının doğru yüklendiğini kontrol et ve logla
            current_app.logger.info("E-posta ayarları: Server=" + str(current_app.config.get('MAIL_SERVER')) + 
                                  ", Port=" + str(current_app.config.get('MAIL_PORT')) + 
                                  ", Sender=" + str(current_app.config.get('MAIL_DEFAULT_SENDER')))
            
            # Debug için ayarları yazdır
            current_app.logger.debug("Mail server: " + str(current_app.config.get('MAIL_SERVER')))
            current_app.logger.debug("Mail port: " + str(current_app.config.get('MAIL_PORT')))
            current_app.logger.debug("Mail username: " + str(current_app.config.get('MAIL_USERNAME')))
            current_app.logger.debug("Mail default sender: " + str(current_app.config.get('MAIL_DEFAULT_SENDER')))
            
            # E-posta takip sistemi ile gönder
            from utils import send_email
            result = send_email(subject, [user.email], html_content, plain_text)
            
            if result:
                current_app.logger.info("E-posta başarıyla gönderildi: " + user.email)
                flash('Kullanıcı ' + user.username + ' başarıyla oluşturuldu. Bilgileri e-posta ile gönderildi.', 'success')
            else:
                current_app.logger.error("E-posta gönderilemedi: " + user.email)
                flash('Kullanıcı ' + user.username + ' başarıyla oluşturuldu fakat e-posta gönderilemedi!', 'warning')
        except Exception as e:
            current_app.logger.error("E-posta gönderme hatası: " + str(e))
            flash('Kullanıcı ' + user.username + ' başarıyla oluşturuldu fakat e-posta gönderilemedi! Hata: ' + str(e), 'warning')
        
        return redirect(url_for('admin.users'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # E-posta adresi değiştiriliyorsa, başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et
        new_email = form.email.data
        if new_email != current_user.email:
            existing_user = User.query.filter(User.email == new_email, User.id != current_user.id).first()
            if existing_user:
                flash(f'Bu e-posta adresi ({new_email}) başka bir kullanıcı tarafından zaten kullanılıyor.', 'danger')
                return render_template('profile.html', form=form, user=current_user)
        
        try:
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.email = new_email
            current_user.phone = form.phone.data
            current_user.updated_at = datetime.datetime.now()
            
            db.session.commit()
            
            # Log kaydı oluştur
            log_activity(
                user_id=current_user.id,
                action="Profil Güncelleme",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            flash('Profiliniz başarıyla güncellendi.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Profil güncellenirken bir hata oluştu: {str(e)}', 'danger')
    
    return render_template('profile.html', form=form, user=current_user)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.updated_at = datetime.datetime.now()
            db.session.commit()
            
            # Log kaydı oluştur
            log_activity(
                user_id=current_user.id,
                action="Şifre Değiştirme",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            flash('Şifreniz başarıyla değiştirildi.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Mevcut şifre yanlış.', 'danger')
    
    return render_template('change_password.html', form=form)

@auth_bp.route('/sifremi-unuttum', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dof.dashboard'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                s = _get_serializer()
                token = s.dumps(user.email, salt='sifre-sifirlama-salt')
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                # Log kaydı oluştur
                log_activity(
                    user_id=user.id,
                    action="Şifre Sıfırlama Talebi",
                    details=f"E-posta: {user.email}",
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                
                # Email gönder - notification_system kullanarak
                email_message = f"""
                Sayın {user.first_name} {user.last_name},
                
                Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:
                {reset_url}
                
                Bu bağlantı 1 saat süreyle geçerlidir.
                
                Eğer şifre sıfırlama talebinde bulunmadıysanız, bu e-postayı dikkate almayın.
                """
                
                try:
                    # Admin panelinden yapılan e-posta ayarlarını kullan (otomatik olarak app.py içinde yükleniyor)
                    from flask_mail import Message
                    from app import mail
                    
                    # E-posta ayarlarının doğru yüklendiğini kontrol et ve logla
                    current_app.logger.info(f"E-posta ayarları: Server={current_app.config.get('MAIL_SERVER')}, "
                                          f"Port={current_app.config.get('MAIL_PORT')}, "
                                          f"Sender={current_app.config.get('MAIL_DEFAULT_SENDER')}")
                    
                    
                    subject = "Şifre Sıfırlama İsteği"
                    recipients = [user.email]
                    
                    # HTML içerikli e-posta oluştur
                    html_content = f"""
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                            .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                            .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2>Şifre Sıfırlama İsteği</h2>
                            </div>
                            <p>Sayın {user.first_name} {user.last_name},</p>
                            <p>Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:</p>
                            <p><a href="{reset_url}" class="button">Şifremi Sıfırla</a></p>
                            <p>Veya aşağıdaki bağlantıyı tarayıcınıza kopyalayın:</p>
                            <p>{reset_url}</p>
                            <p>Bu bağlantı 1 saat süreyle geçerlidir.</p>
                            <p>Eğer şifre sıfırlama talebinde bulunmadıysanız, bu e-postayı dikkate almayın.</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Düz metin için
                    text_content = f"""
                    Sayın {user.first_name} {user.last_name},
                    
                    Şifrenizi sıfırlamak için aşağıdaki bağlantıyı kullanın:
                    {reset_url}
                    
                    Bu bağlantı 1 saat süreyle geçerlidir.
                    
                    Eğer şifre sıfırlama talebinde bulunmadıysanız, bu e-postayı dikkate almayın.
                    """
                    
                    # Debug için ayarları yazdır
                    current_app.logger.debug(f"Mail server: {current_app.config.get('MAIL_SERVER')}")
                    current_app.logger.debug(f"Mail port: {current_app.config.get('MAIL_PORT')}")
                    current_app.logger.debug(f"Mail username: {current_app.config.get('MAIL_USERNAME')}")
                    current_app.logger.debug(f"Mail default sender: {current_app.config.get('MAIL_DEFAULT_SENDER')}")
                    
                    # E-posta takip sistemi ile gönder
                    from utils import send_email
                    result = send_email(subject, recipients, html_content, text_content)
                    
                    if result:
                        current_app.logger.info(f"Şifre sıfırlama e-postası gönderildi: {user.email}")
                        flash('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.', 'info')
                    else:
                        current_app.logger.error(f"Şifre sıfırlama e-postası gönderilemedi: {user.email}")
                        flash('E-posta gönderilirken bir hata oluştu.', 'danger')
                except Exception as e:
                    current_app.logger.error(f"E-posta gönderme hatası: {str(e)}")
                    # E-posta gönderilemezse, kullanıcıya doğrudan bağlantıyı göster
                    flash('E-posta gönderilirken bir hata oluştu. Lütfen aşağıdaki bağlantıyı kullanarak şifrenizi sıfırlayın:', 'warning')
                    flash(reset_url, 'info')
                    # Hatayı konsola da yazdır
                    import traceback
                    current_app.logger.error(traceback.format_exc())
                
            except Exception as e:
                current_app.logger.error(f"Şifre sıfırlama hatası: {str(e)}")
                flash('Şifre sıfırlama işlemi sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyiniz.', 'danger')
        else:
            flash('Bu e-posta adresi sistemde kayıtlı değil.', 'danger')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('forgot_password.html', form=form)

@auth_bp.route('/sifre-sifirla/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dof.dashboard'))
        
    try:
        s = _get_serializer()
        email = s.loads(token, salt='sifre-sifirlama-salt', max_age=3600)  # 1 saat geçerli
    except (SignatureExpired, BadTimeSignature):
        flash('Şifre sıfırlama bağlantısı geçersiz veya süresi dolmuş.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    # WTForms kullanarak validasyon ekleyelim
    from forms import PasswordResetForm
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            user.updated_at = datetime.datetime.now()
            db.session.commit()
            
            # Log kaydı oluştur
            log_activity(
                user_id=user.id,
                action="Şifre Sıfırlama",
                details="Şifre başarıyla sıfırlandı",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            current_app.logger.info(f"Kullanıcı şifresi sıfırlandı: {user.email}")
            flash('Şifreniz başarıyla güncellendi. Yeni şifrenizle giriş yapabilirsiniz.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form, token=token)
