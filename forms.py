from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, DateField, IntegerField, FileField, HiddenField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, NumberRange
from models import User, Department, UserRole, DOFType, DOFSource
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(message='Kullanıcı adı gereklidir')])
    password = PasswordField('Şifre', validators=[DataRequired(message='Şifre gereklidir')])
    remember = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class RegisterForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(message='Kullanıcı adı gereklidir'), Length(min=4, max=64, message='Kullanıcı adı 4-64 karakter arasında olmalıdır')])
    email = StringField('E-posta', validators=[DataRequired(message='E-posta gereklidir'), Email(message='Geçerli bir e-posta adresi giriniz')])
    first_name = StringField('Ad', validators=[DataRequired(message='Ad gereklidir')])
    last_name = StringField('Soyad', validators=[DataRequired(message='Soyad gereklidir')])
    phone = StringField('Telefon', validators=[Optional()])
    password = PasswordField('Şifre', validators=[
        DataRequired(message='Şifre gereklidir'), 
        Length(min=6, message='Şifre en az 6 karakter olmalıdır')
    ])
    confirm_password = PasswordField('Şifre Tekrar', validators=[
        DataRequired(message='Şifre tekrarı gereklidir'), 
        EqualTo('password', message='Şifreler eşleşmiyor')
    ])
    role = SelectField('Rol', coerce=int, validators=[DataRequired(message='Rol seçimi gereklidir')])
    department = SelectField('Departman', coerce=int, validators=[Optional()])
    managed_departments = SelectMultipleField('Yönetilen Departmanlar', coerce=int, validators=[Optional()])
    managed_managers = SelectMultipleField('Yönetilen Bölge Müdürleri', coerce=int, validators=[Optional()])
    submit = SubmitField('Kaydet')
    
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.role.choices = [
            (UserRole.ADMIN, 'Yönetici'),
            (UserRole.QUALITY_MANAGER, 'Kalite Yöneticisi'),
            (UserRole.GROUP_MANAGER, 'Bölge Müdürü'),
            (UserRole.DEPARTMENT_MANAGER, 'Departman Yöneticisi'),
            (UserRole.FRANCHISE_DEPARTMENT_MANAGER, 'Franchise Departman Yöneticisi'),
            (UserRole.DIRECTOR, 'Direktör'),
            (UserRole.PROJECTS_QUALITY_TRACKING, 'Projeler Kalite Takip'),
            (UserRole.BRANCHES_QUALITY_TRACKING, 'Şubeler Kalite Takip')
        ]
        departments = Department.query.filter_by(is_active=True).all()
        self.department.choices = [(0, 'Departman Seçiniz')] + [(d.id, d.name) for d in departments]
        self.managed_departments.choices = [(d.id, d.name) for d in departments]
        
        # Bölge Müdürleri listesini hazırla (Direktör rolü için)
        from flask import current_app
        current_app.logger.info("Bölge Müdürleri sorgulanıyor...")
        current_app.logger.info(f"UserRole.GROUP_MANAGER değeri: {UserRole.GROUP_MANAGER}")
        
        # is_active property yerine veritabanı kolonu olan active kullan
        group_managers = User.query.filter(
            User.role.in_([UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]),
            User.active == True
        ).all()
        
        current_app.logger.info(f"Bulunan bölge müdürü sayısı: {len(group_managers)}")
        for manager in group_managers:
            current_app.logger.info(f"Bölge Müdürü: ID={manager.id}, Ad={manager.first_name} {manager.last_name}, Rol={manager.role}")
        
        # Seçenekleri hazırla
        self.managed_managers.choices = [(u.id, f"{u.first_name} {u.last_name}") for u in group_managers]
        
        # Kullanıcı düzenlenirken mevcut departman ve bölge müdürü mappinglerini yükle
        # NOT: Bu işlem admin.py'de de yapılıyor, o yüzden forms.py'de yapmayalım
        # Çifte yükleme conflict'i olabiliyor
        if False:  # Geçici olarak devre dışı
            if self.user_id:
                user = User.query.get(self.user_id)
                if user:
                    # Çoklu departman yöneticileri için mevcut departman mappinglerini yükle
                    if user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                        current_dept_ids = [mapping.department_id for mapping in user.managed_department_mappings]
                        self.managed_departments.data = current_dept_ids
                        current_app.logger.info(f"Forms.py - Kullanıcı {user.username} için mevcut departmanlar yüklendi: {current_dept_ids}")
                    
                    # Direktör için mevcut bölge müdürü mappinglerini yükle
                    elif user.role == UserRole.DIRECTOR:
                        current_manager_ids = [mapping.manager_id for mapping in user.managed_managers_links]
                        self.managed_managers.data = current_manager_ids
                        current_app.logger.info(f"Forms.py - Direktör {user.username} için mevcut bölge müdürleri yüklendi: {current_manager_ids}")
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and (self.user_id is None or user.id != self.user_id):
            raise ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and (self.user_id is None or user.id != self.user_id):
            raise ValidationError('Bu e-posta adresi zaten kullanılıyor.')

class UserProfileForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired(message='Ad gereklidir')])
    last_name = StringField('Soyad', validators=[DataRequired(message='Soyad gereklidir')])
    email = StringField('E-posta', validators=[DataRequired(message='E-posta gereklidir'), Email(message='Geçerli bir e-posta adresi giriniz')])
    phone = StringField('Telefon', validators=[Optional()])
    submit = SubmitField('Güncelle')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mevcut Şifre', validators=[DataRequired(message='Mevcut şifre gereklidir')])
    new_password = PasswordField('Yeni Şifre', validators=[
        DataRequired(message='Yeni şifre gereklidir'), 
        Length(min=6, message='Şifre en az 6 karakter olmalıdır')
    ])
    confirm_new_password = PasswordField('Yeni Şifre Tekrar', validators=[
        DataRequired(message='Şifre tekrarı gereklidir'), 
        EqualTo('new_password', message='Şifreler eşleşmiyor')
    ])
    submit = SubmitField('Şifreyi Değiştir')

class DepartmentForm(FlaskForm):
    name = StringField('Departman Adı', validators=[DataRequired(message='Departman adı gereklidir')])
    description = TextAreaField('Açıklama')
    manager = SelectField('Departman Yöneticisi', coerce=int, validators=[Optional()])
    is_active = BooleanField('Aktif')
    submit = SubmitField('Kaydet')
    
    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        # Sadece departman yöneticisi, franchise departman yöneticisi veya normal kullanıcı rolüne sahip kullanıcıları listele
        managers = User.query.filter(User.role.in_([UserRole.DEPARTMENT_MANAGER, UserRole.FRANCHISE_DEPARTMENT_MANAGER, UserRole.USER])).all()
        self.manager.choices = [(0, 'Yönetici Seçiniz')] + [(u.id, f"{u.first_name} {u.last_name}") for u in managers]

class DOFForm(FlaskForm):
    """DÖF oluşturma ve düzenleme formu"""
    title = StringField('Başlık', validators=[DataRequired(message='Başlık gereklidir')])
    description = TextAreaField('Açıklama', validators=[DataRequired(message='Açıklama gereklidir')])
    dof_type = SelectField('DÖF Tipi', coerce=int, validators=[DataRequired(message='DÖF tipi gereklidir')])
    dof_source = SelectField('DÖF Kaynağı', coerce=int, validators=[DataRequired(message='DÖF kaynağı gereklidir')])
    department = SelectField('Sorumlu Departman', coerce=int, validators=[Optional()])
    # Bölge müdürü için yönetilen departmanlar listesi 
    managed_departments = SelectField('Yönetilen Departman', coerce=int, validators=[Optional()]) 
    # Öncelik alanı kaldırıldı - artık kullanılmıyor
    files = FileField('Dosya Ekle', validators=[Optional()])
    due_date = DateField('Termin Tarihi', format='%Y-%m-%d', validators=[Optional()])
    
    # Müşteri şikayeti için yeni alanlar
    channel = SelectField('Şikayet/Talep Kanalı', validators=[Optional()])
    complaint_date = DateField('Şikayet/Talep Tarihi', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Kaydet')
    
    def __init__(self, *args, **kwargs):
        # Form tipini al - varsayılan olarak 'edit' (düzenleme)
        self.form_type = kwargs.pop('form_type', 'edit') 
        self.user = kwargs.pop('current_user', None)  # Mevcut kullanıcıyı al
        super(DOFForm, self).__init__(*args, **kwargs)
        
        # DÖF oluşturma sırasında termin tarihi alanını gizle (güvenli yöntem)
        if self.form_type == 'create':
            # Field'ı silmek yerine, render_kw kullanarak gizleyelim
            if hasattr(self, 'due_date') and self.due_date:
                self.due_date.render_kw = {'style': 'display: none;'}
                self.due_date.validators = []  # Validasyon kurallarını kaldır
            
        self.dof_type.choices = [
            (DOFType.CORRECTIVE, 'Düzeltici Faaliyet'),
            (DOFType.CORRECTIVE_REQUEST, 'Düzeltici Faaliyet Talebi'),
            (DOFType.IMPROVEMENT, 'İyileştirme Talebi'),
            (DOFType.PREVENTIVE, 'Önleyici Faaliyet')
        ]
        self.dof_source.choices = [
            (DOFSource.INTERNAL_AUDIT, 'İç Tetkik'),
            (DOFSource.EXTERNAL_AUDIT, 'Dış Tetkik'),
            (DOFSource.CUSTOMER_COMPLAINT, 'Müşteri Talebi/Şikayeti'),
            (DOFSource.EMPLOYEE_SUGGESTION, 'Çalışan Önerisi'),
            (DOFSource.EXTERNAL_INSPECTION, 'Dış Denetim'),
            (DOFSource.SUPPLIER, 'Tedarikçi'),
            (DOFSource.PROCESS, 'Proses/Süreç'),
            (DOFSource.LEGAL_REQUIREMENT, 'Yasal Gereksinim'),
            (DOFSource.NONCONFORMITY, 'Uygunsuzluk'),
            (DOFSource.OTHER, 'Diğer')
        ]
        
        # Kanal seçeneklerini ayarla
        self.channel.choices = [
            ('', 'Kanal Seçiniz'),
            ('trendyol', 'Trendyol'),
            ('yemeksepeti', 'Yemeksepeti'),
            ('getir', 'Getir'),
            ('google', 'Google Yorumlar'),
            ('website', 'Website'),
            ('migros', 'Migros Yemek'),
            ('fuudy', 'Fuudy'),
            ('telefon', 'Telefon'),
            ('whatsapp', 'WhatsApp'),
            ('eticaret', 'e-Ticaret'),
            ('diger', 'Diğer')
        ]
        
        # Kullanıcı rolüne göre departman seçenekleri ayarlamaları
        all_departments = Department.query.filter_by(is_active=True).all()
        
        # Kullanıcının kendi departmanını hariç tutma (DÖF oluşturma sırasında)
        if self.form_type == 'create' and self.user and self.user.department_id:
            # Kendi departmanını hariç tut
            filtered_departments = [d for d in all_departments if d.id != self.user.department_id]
            self.department.choices = [(0, 'Departman Seçiniz')] + [(d.id, d.name) for d in filtered_departments]
        else:
            # Düzenleme durumunda veya departmanı yoksa tüm departmanları göster
            self.department.choices = [(0, 'Departman Seçiniz')] + [(d.id, d.name) for d in all_departments]
        
        # Bölge müdürü için özel departman seçim listesi
        managed_dept_list = []
        if self.user and self.user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            # Sadece yönettiği departmanları göster
            for mapping in self.user.managed_department_mappings:
                dept = Department.query.get(mapping.department_id)
                if dept and dept.is_active:
                    managed_dept_list.append((dept.id, dept.name))
        
        # Her zaman en azından boş bir liste ata, böylece None hatası oluşmaz
        self.managed_departments.choices = managed_dept_list
    
    def validate_channel(self, field):
        """Müşteri şikayeti seçildiğinde kanal alanının zorunlu olmasını sağlar"""
        if self.dof_source.data == DOFSource.CUSTOMER_COMPLAINT and not field.data:
            raise ValidationError('Müşteri talebi/şikayeti seçildiğinde kanal bilgisi zorunludur')
    
    def validate_complaint_date(self, field):
        """Müşteri şikayeti seçildiğinde şikayet tarihi alanının zorunlu olmasını sağlar"""
        if self.dof_source.data == DOFSource.CUSTOMER_COMPLAINT and not field.data:
            raise ValidationError('Müşteri talebi/şikayeti seçildiğinde şikayet tarihi zorunludur')

class DOFActionForm(FlaskForm):
    comment = TextAreaField('Yorum', validators=[Optional()])
    root_cause = TextAreaField('Kök Neden Analizi', validators=[Optional()])
    resolution_plan = TextAreaField('Aksiyon Planı', validators=[Optional()])
    deadline = DateField('Termin Tarihi', format='%Y-%m-%d', validators=[Optional()])
    new_status = SelectField('Durum', coerce=int, validators=[Optional()])
    assigned_to = SelectField('Atanan Kişi', coerce=int, validators=[Optional()])
    files = FileField('Dosya Ekle', validators=[Optional()])
    submit = SubmitField('Gönder')
    
    def __init__(self, dof_status=None, *args, **kwargs):
        super(DOFActionForm, self).__init__(*args, **kwargs)
        
        from models import DOFStatus
        # Mevcut duruma göre sonraki olası durumları belirle
        if dof_status is not None:
            if dof_status == DOFStatus.DRAFT:
                self.new_status.choices = [(DOFStatus.SUBMITTED, 'Gönderildi')]
            elif dof_status == DOFStatus.SUBMITTED:
                self.new_status.choices = [(DOFStatus.IN_REVIEW, 'İncelemede'), (DOFStatus.REJECTED, 'Reddedildi')]
            elif dof_status == DOFStatus.IN_REVIEW:
                self.new_status.choices = [(DOFStatus.ASSIGNED, 'Atandı'), (DOFStatus.REJECTED, 'Reddedildi')]
            elif dof_status == DOFStatus.ASSIGNED:
                # Atanan departman formu gönderince PLANNING durumuna geçer (kod içinde yapılıyor)
                self.new_status.choices = []
            elif dof_status == DOFStatus.PLANNING:
                # Kalite incelemesi sonrası durumlar
                self.new_status.choices = [
                    (DOFStatus.IMPLEMENTATION, 'Uygulama Aşamasına Geç'), 
                    (DOFStatus.ASSIGNED, 'Düzeltme Talep Et'),
                    (DOFStatus.COMPLETED, 'Tamamlandı')
                ]
            elif dof_status == DOFStatus.IMPLEMENTATION or dof_status == 9:  # 9: IMPLEMENTATION (Aksiyon Planı Uygulama Aşamasında)
                # Uygulama aşamasında sonraki durum
                self.new_status.choices = [(DOFStatus.COMPLETED, 'Tamamlandı')]
            elif dof_status == DOFStatus.COMPLETED or dof_status == 10:  # 10: COMPLETED (Aksiyonlar Tamamlandı)
                # Kaynak departmanın değerlendirmesi
                self.new_status.choices = [
                    (DOFStatus.SOURCE_REVIEW, 'Kaynak Onayına Gönder'),
                    (5, 'Çözüldü'),  # 5: RESOLVED (Çözüldü)
                    (4, 'Çözümden Memnun Değilim')  # 4: IN_PROGRESS (Devam Ediyor)
                ]
            elif dof_status == DOFStatus.SOURCE_REVIEW:
                # Kaynak departman değerlendirmesi
                self.new_status.choices = [(DOFStatus.RESOLVED, 'Çözümü Onayla'), (DOFStatus.IN_PROGRESS, 'Çözüm Sağlanamadı')]
            elif dof_status == DOFStatus.RESOLVED:
                # Final kalite incelemesi
                self.new_status.choices = [(DOFStatus.CLOSED, 'DÖF\'u Kapat'), (DOFStatus.IN_PROGRESS, 'Yeni DÖF Açılsın')]
            elif dof_status == DOFStatus.IN_PROGRESS:
                # Eski sistem uyumluluğu
                self.new_status.choices = [(DOFStatus.RESOLVED, 'Çözüldü')]
            else:
                self.new_status.choices = []
        else:
            self.new_status.choices = []
        
        # Atanabilecek kullanıcıları listele
        users = User.query.filter(User.is_active == True).all()
        self.assigned_to.choices = [(0, 'Kişi Seçiniz')] + [(u.id, f"{u.first_name} {u.last_name}") for u in users]

class WorkflowDefinitionForm(FlaskForm):
    name = StringField('İş Akışı Adı', validators=[DataRequired(message='İş akışı adı gereklidir')])
    description = TextAreaField('Açıklama')
    is_active = BooleanField('Aktif')
    submit = SubmitField('Kaydet')

class WorkflowStepForm(FlaskForm):
    name = StringField('Adım Adı', validators=[DataRequired(message='Adım adı gereklidir')])
    description = TextAreaField('Açıklama')
    step_order = IntegerField('Sıra No', validators=[DataRequired(message='Sıra no gereklidir')])
    required_role = SelectField('Gerekli Rol', coerce=int, validators=[DataRequired(message='Rol seçimi gereklidir')])
    from_status = SelectField('Başlangıç Durumu', coerce=int, validators=[DataRequired(message='Başlangıç durumu gereklidir')])
    to_status = SelectField('Hedef Durum', coerce=int, validators=[DataRequired(message='Hedef durum gereklidir')])
    is_active = BooleanField('Aktif')
    workflow_id = HiddenField()
    submit = SubmitField('Kaydet')
    
    def __init__(self, *args, **kwargs):
        super(WorkflowStepForm, self).__init__(*args, **kwargs)
        self.required_role.choices = [
            (UserRole.ADMIN, 'Yönetici'),
            (UserRole.QUALITY_MANAGER, 'Kalite Yöneticisi'),
            (UserRole.DEPARTMENT_MANAGER, 'Departman Yöneticisi'),
            (UserRole.FRANCHISE_DEPARTMENT_MANAGER, 'Franchise Departman Yöneticisi'),
            (UserRole.USER, 'Kullanıcı'),
            (UserRole.PROJECTS_QUALITY_TRACKING, 'Projeler Kalite Takip'),
            (UserRole.BRANCHES_QUALITY_TRACKING, 'Şubeler Kalite Takip')
        ]
        
        from models import DOFStatus
        self.from_status.choices = [
            (DOFStatus.DRAFT, 'Taslak'),
            (DOFStatus.SUBMITTED, 'Gönderildi'),
            (DOFStatus.IN_REVIEW, 'İncelemede'),
            (DOFStatus.ASSIGNED, 'Atandı'),
            (DOFStatus.IN_PROGRESS, 'Devam Ediyor'),
            (DOFStatus.RESOLVED, 'Çözüldü'),
            (DOFStatus.CLOSED, 'Kapatıldı'),
            (DOFStatus.REJECTED, 'Reddedildi')
        ]
        
        self.to_status.choices = self.from_status.choices

class DOFResolveForm(FlaskForm):
    # Kök neden analizi alanları - İlk 3'ü zorunlu
    root_cause1 = TextAreaField('1. Kök Neden', validators=[DataRequired(message='En az 3 kök neden belirtilmelidir')])
    root_cause2 = TextAreaField('2. Kök Neden', validators=[DataRequired(message='En az 3 kök neden belirtilmelidir')])
    root_cause3 = TextAreaField('3. Kök Neden', validators=[DataRequired(message='En az 3 kök neden belirtilmelidir')])
    root_cause4 = TextAreaField('4. Kök Neden', validators=[Optional()])
    root_cause5 = TextAreaField('5. Kök Neden', validators=[Optional()])
    
    # Termin tarihi
    deadline = DateField('Termin Tarihi', format='%Y-%m-%d', validators=[DataRequired(message='Termin tarihi belirtilmelidir')])
    
    # Aksiyon planı
    action_plan = TextAreaField('Aksiyon Planı', validators=[DataRequired(message='Aksiyon planı belirtilmelidir')])
    
    # Yorum
    comment = TextAreaField('Açıklama', validators=[Optional()])
    
    submit = SubmitField('Kaydet')

class QualityReviewForm(FlaskForm):
    """Kalite yöneticisi değerlendirme formu"""
    
    department = SelectField('Atanacak Departman', coerce=int, validators=[Optional()])
    comment = TextAreaField('Değerlendirme', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(QualityReviewForm, self).__init__(*args, **kwargs)
        self.department.choices = [(d.id, d.name) for d in Department.query.filter_by(is_active=True).all()]

class QualityClosureForm(FlaskForm):
    comment = TextAreaField('Değerlendirme', validators=[Optional()])

class SearchForm(FlaskForm):
    keyword = StringField('Arama', validators=[Optional()])
    status = SelectField('Durum', coerce=int, validators=[Optional()])
    department = SelectField('Departman', coerce=int, validators=[Optional()])
    date_from = DateField('Başlangıç Tarihi', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateField('Bitiş Tarihi', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Ara')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        
        from models import DOFStatus
        self.status.choices = [(0, 'Tüm Durumlar')] + [
            (DOFStatus.DRAFT, 'Taslak'),
            (DOFStatus.SUBMITTED, 'Gönderildi'),
            (DOFStatus.IN_REVIEW, 'İncelemede'),
            (DOFStatus.ASSIGNED, 'Atandı'),
            (DOFStatus.IN_PROGRESS, 'Devam Ediyor'),
            (DOFStatus.RESOLVED, 'Çözüldü'),
            (DOFStatus.CLOSED, 'Kapatıldı'),
            (DOFStatus.REJECTED, 'Reddedildi')
        ]
        
        self.department.choices = [(0, 'Tüm Departmanlar')] + [(d.id, d.name) for d in Department.query.filter_by(is_active=True).all()]


class EmailSettingsForm(FlaskForm):
    """E-mail sunucu ayarları formu"""
    mail_service = SelectField('Mail Servisi', 
                              choices=[
                                  ('smtp', 'SMTP Sunucu'), 
                                  ('gmail', 'Gmail')
                              ],
                              validators=[DataRequired(message='Mail servisi seçilmelidir')])
    
    smtp_host = StringField('SMTP Sunucu Adresi', 
                             validators=[Optional()],
                             description='Örn: smtp.gmail.com')
    
    smtp_port = IntegerField('SMTP Port', 
                            validators=[Optional(), NumberRange(min=1, max=65535)],
                            description='Örn: 465 (SSL) veya 587 (TLS)')
    
    smtp_use_tls = BooleanField('TLS Kullan')
    smtp_use_ssl = BooleanField('SSL Kullan')
    
    smtp_user = StringField('SMTP Kullanıcı Adı',
                               validators=[Optional()],
                               description='Örn: alikokrtv@gmail.com')
    
    smtp_pass = StringField('SMTP Şifre',
                           validators=[Optional()],
                           description='Mail hesabı şifresi veya uygulama şifresi')
    
    default_sender = StringField('Varsayılan Gönderen',
                                validators=[Optional()],
                                description='Örn: alikokrtv@gmail.com')
    
    submit = SubmitField('Kaydet')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # SMTP sunucu kontrolleri
        if self.mail_service.data == 'smtp':
            if not self.smtp_host.data:
                self.smtp_host.errors.append('SMTP sunucu adresi gereklidir')
                return False
            
            if not self.smtp_port.data:
                self.smtp_port.errors.append('SMTP port numarası gereklidir')
                return False
            
            if not self.smtp_user.data:
                self.smtp_user.errors.append('SMTP kullanıcı adı gereklidir')
                return False
            
            if not self.smtp_pass.data and not self.smtp_pass.flags.placeholder:
                self.smtp_pass.errors.append('SMTP şifresi gereklidir')
                return False
        
        return True

class ForgotPasswordForm(FlaskForm):
    email = StringField('E-posta', validators=[
        DataRequired(message='E-posta adresi gereklidir'),
        Email(message='Geçerli bir e-posta adresi giriniz')
    ])
    submit = SubmitField('Şifre Sıfırlama Bağlantısı Gönder')
    
class PasswordResetForm(FlaskForm):
    """Kullanıcı şifre sıfırlama formu"""
    password = PasswordField('Yeni Şifre', validators=[
        DataRequired(message='Şifre gereklidir'), 
        Length(min=6, message='Şifre en az 6 karakter olmalıdır')
    ])
    password_confirm = PasswordField('Şifre Tekrarı', validators=[
        DataRequired(message='Şifre tekrarı gereklidir'),
        EqualTo('password', message='Şifreler eşleşmeli')
    ])
    submit = SubmitField('Şifremi Güncelle')

class FeedbackForm(FlaskForm):
    """Hata/geri bildirim formu"""
    feedback_type = SelectField('Bildirim Türü', 
                              choices=[
                                  ('bug', 'Hata Bildirimi'), 
                                  ('suggestion', 'Geliştirme Önerisi'),
                                  ('question', 'Soru'),
                                  ('other', 'Diğer')
                              ],
                              validators=[DataRequired(message='Bildirim türü seçilmelidir')])
    subject = StringField('Konu', validators=[DataRequired(message='Konu gereklidir')])
    message = TextAreaField('Mesajınız', validators=[DataRequired(message='Mesaj gereklidir')])
    screenshot = FileField('Ekran Görüntüsü', validators=[Optional()])
    submit = SubmitField('Gönder')


class ThankYouForm(FlaskForm):
    """
    Teşekkür Bildirim Formu
    Müşteri İlişkileri departmanı yöneticileri için dışarıdan gelen teşekkürleri kaydetme formu
    """
    title = StringField('Başlık', validators=[
        DataRequired(message='Başlık gereklidir'), 
        Length(min=3, max=100, message='Başlık 3-100 karakter arasında olmalıdır')
    ])
    description = TextAreaField('Açıklama / Teşekkür Metni', validators=[
        DataRequired(message='Teşekkür metni gereklidir')
    ])
    department_id = SelectField('İlgili Departman', 
        validators=[DataRequired(message='Departman seçimi gereklidir')],
        coerce=int
    )
    submit = SubmitField('Teşekkür Bildir')
    
    def __init__(self, *args, **kwargs):
        super(ThankYouForm, self).__init__(*args, **kwargs)
        # Aktif departmanları form seçeneği olarak ekle
        self.department_id.choices = [(d.id, d.name) for d in Department.query.filter_by(is_active=True).order_by(Department.name).all()]
