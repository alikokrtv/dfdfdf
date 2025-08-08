from datetime import datetime
from extensions import db
from flask_login import UserMixin
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Kullanıcı rolleri
class UserRole:
    ADMIN = 1  # Admin
    QUALITY_MANAGER = 2  # Kalite Yöneticisi
    GROUP_MANAGER = 3  # Grup Yöneticisi (Birden fazla departmanı yönetebilir)
    DEPARTMENT_MANAGER = 4  # Departman Yöneticisi
    USER = 5  # Normal Kullanıcı
    DIRECTOR = 6  # Direktör (Bölge Müdürlerinin Üstü)
    FRANCHISE_DEPARTMENT_MANAGER = 7  # Franchise Departman Yöneticisi
    PROJECTS_QUALITY_TRACKING = 8  # Projeler Kalite Takip
    BRANCHES_QUALITY_TRACKING = 9  # Şubeler Kalite Takip

# DÖF durumları
class DOFStatus:
    DRAFT = 0       # Taslak
    SUBMITTED = 1   # Gönderildi
    IN_REVIEW = 2   # İncelemede (Kalite inceleme aşaması)
    ASSIGNED = 3    # Atandı (Departmana atandı, plan/kök neden bekleniyor)
    IN_PROGRESS = 4 # Devam Ediyor (Eski sistem uyumluluğu için)
    RESOLVED = 5    # Çözüldü (Eski sistem uyumluluğu için)
    CLOSED = 6      # Kapatıldı
    REJECTED = 7    # Reddedildi
    PLANNING = 8    # Planlama (Kök neden ve aksiyon planı hazırlandı, kalite incelemesi bekleniyor)
    IMPLEMENTATION = 9  # Uygulama (Kalite onayladı, uygulama aşamasında)
    COMPLETED = 10   # Tamamlandı (Atanan departman işlemi tamamladı)
    SOURCE_REVIEW = 11 # Kaynak İncelemesi (Kaynak departmanın onayı bekleniyor)
    
    @classmethod
    def get_label(cls, status_code):
        """Durum kodlarını insan tarafından okunabilir metinlere dönüştürür"""
        status_names = {
            cls.DRAFT: "Taslak",
            cls.SUBMITTED: "Gönderildi",
            cls.IN_REVIEW: "İncelemede",
            cls.ASSIGNED: "Atandı",
            cls.IN_PROGRESS: "Devam Ediyor",
            cls.RESOLVED: "Çözüldü",
            cls.CLOSED: "Kapatıldı",
            cls.REJECTED: "Reddedildi",
            cls.PLANNING: "Aksiyon Planı İncelemede",
            cls.IMPLEMENTATION: "Uygulama Aşamasında",
            cls.COMPLETED: "Tamamlandı",
            cls.SOURCE_REVIEW: "Kaynak İncelemesinde"
        }
        return status_names.get(status_code, f"Bilinmeyen Durum ({status_code})")

# DÖF tipleri
class DOFType:
    CORRECTIVE = 1  # Düzeltici Faaliyet
    PREVENTIVE = 2  # Önleyici Faaliyet
    IMPROVEMENT = 3  # İyileştirme Talebi
    CORRECTIVE_REQUEST = 4  # Düzeltici Faaliyet Talebi

# DÖF Aksiyon Tipleri
class DOFActionType:
    COMMENT = 1     # Yorum
    STATUS_CHANGE = 2 # Durum Değişikliği
    ASSIGNMENT = 3   # Atama
    NEW_DOF = 4       # Yeni DÖF
    PLAN_REVISION = 5 # Plan Revizyonu

# DÖF kaynakları
class DOFSource:
    INTERNAL_AUDIT = 1  # İç Tetkik
    EXTERNAL_AUDIT = 2  # Dış Tetkik
    CUSTOMER_COMPLAINT = 3  # Müşteri Talebi/Şikayeti
    EMPLOYEE_SUGGESTION = 4  # Çalışan Önerisi
    NONCONFORMITY = 5  # Uygunsuzluk
    EXTERNAL_INSPECTION = 7  # Dış Denetim (Yeni)
    SUPPLIER = 8  # Tedarikçi
    PROCESS = 9  # Proses/Süreç
    LEGAL_REQUIREMENT = 10  # Yasal Gereksinim
    OTHER = 6  # Diğer

# Kullanıcı modeli
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Integer, default=UserRole.USER)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_active(self):
        return self.active
        
    @is_active.setter
    def is_active(self, value):
        self.active = value
    
    # İlişkiler
    department = db.relationship('Department', foreign_keys=[department_id], backref='users')
    created_dofs = db.relationship('DOF', backref='creator', foreign_keys='DOF.created_by', lazy='dynamic')
    assigned_dofs = db.relationship('DOF', backref='assignee', foreign_keys='DOF.assigned_to', lazy='dynamic')
    actions = db.relationship('DOFAction', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    # Direktör-Bölge Müdürü ilişkileri
    # Bir direktörün yönettiği bölge müdürleri
    managed_managers_links = db.relationship('DirectorManagerMapping', 
                                        foreign_keys='DirectorManagerMapping.director_id',
                                        backref='director', cascade="all, delete-orphan")
    # Bir bölge müdürüne bağlı direktörler
    managing_directors_links = db.relationship('DirectorManagerMapping',
                                        foreign_keys='DirectorManagerMapping.manager_id',
                                        backref='manager', cascade="all, delete-orphan")
    
    @property
    def managed_manager_users(self):
        """Direktörün yönettiği bölge müdürlerini döndürür"""
        return [link.manager for link in self.managed_managers_links]
    
    @property
    def managing_director_users(self):
        """Bölge müdürünün bağlı olduğu direktörleri döndürür"""
        return [link.director for link in self.managing_directors_links]
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def role_name(self):
        roles = {
            UserRole.ADMIN: "Yönetici",
            UserRole.QUALITY_MANAGER: "Kalite Yöneticisi",
            UserRole.GROUP_MANAGER: "Bölge Müdürü",
            UserRole.DEPARTMENT_MANAGER: "Departman Yöneticisi",
            UserRole.USER: "Kullanıcı",
            UserRole.DIRECTOR: "Direktör",
            UserRole.FRANCHISE_DEPARTMENT_MANAGER: "Franchise Departman Yöneticisi",
            UserRole.PROJECTS_QUALITY_TRACKING: "Projeler Kalite Takip",
            UserRole.BRANCHES_QUALITY_TRACKING: "Şubeler Kalite Takip"
        }
        return roles.get(self.role, "Kullanıcı")
    
    def is_admin(self):
        """Kullanıcının admin olup olmadığını kontrol eder"""
        return self.role == UserRole.ADMIN
        
    def is_quality_manager(self):
        """Kullanıcının kalite yöneticisi olup olmadığını kontrol eder"""
        return self.role == UserRole.QUALITY_MANAGER
        
    def is_department_manager(self):
        """Kullanıcının departman yöneticisi olup olmadığını kontrol eder"""
        return (self.role == UserRole.DEPARTMENT_MANAGER or self.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and self.department_id is not None
    
    def get_managed_departments(self):
        """Kullanıcının yönettiği tüm departmanları döndürür"""
        departments = []
        
        # Admin ise tüm departmanlar
        if self.role == UserRole.ADMIN:
            return Department.query.filter_by(is_active=True).all()
            
        # Departman yöneticisi veya franchise departman yöneticisi ise, kendi yönettiği departman
        if (self.role == UserRole.DEPARTMENT_MANAGER or self.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and self.department_id:
            dept = Department.query.get(self.department_id)
            if dept and dept.manager_id == self.id:
                departments.append(dept)
        
        # Grup yöneticisi, Projeler Kalite Takip, Şubeler Kalite Takip rolleri ise
        if self.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            # 1. Yönetici olduğu gruplar
            managed_groups = DepartmentGroup.query.filter_by(manager_id=self.id).all()
            
            # Grupların departmanları
            for group in managed_groups:
                # Doğrudan departman-grup ilişkisi
                direct_depts = Department.query.filter_by(group_id=group.id).all()
                departments.extend(direct_depts)
                
                # Grup-Departman ara tablosundaki ilişkiler
                mapped_depts = [gd.department for gd in group.department_mappings]
                departments.extend(mapped_depts)
            
            # 2. UserDepartmentMapping tablosundaki ilişkiler
            # Bölge Müdürü için kullanıcı-departman eşleştirmelerini kontrol et
            from app import db
            user_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=self.id).all()
            
            if user_dept_mappings:
                mapped_depts = [udm.department for udm in user_dept_mappings if udm.department and udm.department.is_active]
                departments.extend(mapped_depts)
                
            # Log kayıtları ekle
            try:
                from flask import current_app
                current_app.logger.debug(f"Grup yöneticisi {self.username} için departman eşleştirmeleri: {len(user_dept_mappings) if 'user_dept_mappings' in locals() else 0}")
                current_app.logger.debug(f"Grup yöneticisi {self.username} için toplam departman sayısı: {len(departments)}")
            except:
                pass  # Flask context yoksa log kaydı yapma
        
        # Direktör ise - altındaki bölge müdürlerinin yönettiği departmanları getir
        if self.role == UserRole.DIRECTOR:
            # DirectorManagerMapping tablosundan bu direktörün yönettiği bölge müdürlerini al
            director_mappings = DirectorManagerMapping.query.filter_by(director_id=self.id).all()
            
            for mapping in director_mappings:
                manager = mapping.manager
                if manager and manager.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                    # Bu çoklu departman yöneticisinin yönettiği departmanları al
                    manager_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=manager.id).all()
                    for dept_mapping in manager_dept_mappings:
                        if dept_mapping.department and dept_mapping.department.is_active:
                            departments.append(dept_mapping.department)
            
            # Log kayıtları ekle
            try:
                from flask import current_app
                current_app.logger.debug(f"Direktör {self.username} için {len(director_mappings)} bölge müdürü eşleştirmesi bulundu")
                current_app.logger.debug(f"Direktör {self.username} için toplam departman sayısı: {len(departments)}")
            except:
                pass  # Flask context yoksa log kaydı yapma
            
        # Tekil bir liste haline getir (aynı departmanı iki kez listelemeyi önle)
        unique_departments = []
        seen_ids = set()
        
        for dept in departments:
            if dept.id not in seen_ids and dept.is_active:
                seen_ids.add(dept.id)
                unique_departments.append(dept)
                
        return unique_departments
    
    def can_manage_department(self, department_id):
        """Kullanıcının belirli bir departmanı yönetme yetkisi var mı?"""
        # Admin ise her departmanı yönetebilir
        if self.role == UserRole.ADMIN:
            return True
        
        # Direkt atanmış departman yöneticisi veya franchise departman yöneticisi ise
        if (self.role == UserRole.DEPARTMENT_MANAGER or self.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and self.department_id == department_id:
            dept = Department.query.get(department_id)
            return dept and dept.manager_id == self.id
            
        # Grup yöneticisi, Projeler Kalite Takip, Şubeler Kalite Takip rolleri ise
        if self.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            # Departmanın bağlı olduğu grup
            dept = Department.query.get(department_id)
            if not dept:
                return False
                
            # Direkt grup ilişkisi
            if dept.group_id:
                group = DepartmentGroup.query.get(dept.group_id)
                if group and group.manager_id == self.id:
                    return True
            
            # Grup-Departman ara tablosu ilişkisi
            group_depts = GroupDepartment.query.filter_by(department_id=department_id).all()
            for gd in group_depts:
                group = DepartmentGroup.query.get(gd.group_id)
                if group and group.manager_id == self.id:
                    return True
        
        # Direktör ise - altındaki bölge müdürlerinin yönettiği departmanları yönetebilir
        if self.role == UserRole.DIRECTOR:
            # Bu direktörün yönettiği tüm departmanları kontrol et
            managed_departments = self.get_managed_departments()
            managed_dept_ids = [dept.id for dept in managed_departments]
            return department_id in managed_dept_ids
        
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

# Departman Grubu modeli
class DepartmentGroup(db.Model):
    __tablename__ = 'department_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Grup yöneticisi ile ilişki
    manager = db.relationship('User', backref='managed_groups', foreign_keys=[manager_id])
    
    def __repr__(self):
        return f'<DepartmentGroup {self.name}>'

# Grup Yönetici İlişkisi (Grup yöneticilerinin göreceği departmanlar için ara tablo)
class GroupDepartment(db.Model):
    __tablename__ = 'group_departments'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('department_groups.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    group = db.relationship('DepartmentGroup', backref='department_mappings')
    department = db.relationship('Department', backref='group_mappings')

# Departman modeli
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Departman yöneticisi
    group_id = db.Column(db.Integer, db.ForeignKey('department_groups.id'), nullable=True)  # Bağlı olduğu grup
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # İlişkiler
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_department', uselist=False)
    group = db.relationship('DepartmentGroup', foreign_keys=[group_id], backref='direct_departments')
    dofs = db.relationship('DOF', backref='department', lazy='dynamic')
    
    def __repr__(self):
        return f'<Department {self.name}>'

# DÖF modeli
class DOF(db.Model):
    __tablename__ = 'dofs'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=True)  # DOF kodu: Örn. DEKNEM-001
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    dof_type = db.Column(db.Integer, nullable=False)
    dof_source = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, default=DOFStatus.DRAFT)
    # priority alanı kaldırıldı - artık kullanılmıyor
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    due_date = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Müşteri şikayeti için yeni alanlar
    channel = db.Column(db.String(50), nullable=True)  # Şikayet/Talep kanalı: Trendyol, Yemeksepeti, vs.
    complaint_date = db.Column(db.DateTime, nullable=True)  # Şikayet/Talep tarihi
    # Kök neden analizi alanları (ilk 3'ü zorunlu)
    root_cause1 = db.Column(db.Text, nullable=True)
    root_cause2 = db.Column(db.Text, nullable=True)
    root_cause3 = db.Column(db.Text, nullable=True)
    root_cause4 = db.Column(db.Text, nullable=True)
    root_cause5 = db.Column(db.Text, nullable=True)
    # Termin tarihi
    deadline = db.Column(db.DateTime, nullable=True)
    # Aksiyon planı
    action_plan = db.Column(db.Text, nullable=True)
    # Tamamlanma tarihi
    completion_date = db.Column(db.DateTime, nullable=True)
    
    # İlişkiler
    actions = db.relationship('DOFAction', backref='dof', lazy='dynamic')
    attachments = db.relationship('Attachment', backref='dof', lazy='dynamic')
    
    @property
    def status_name(self):
        statuses = {
            DOFStatus.DRAFT: "Taslak",
            DOFStatus.SUBMITTED: "Gönderildi",
            DOFStatus.IN_REVIEW: "İncelemede",
            DOFStatus.ASSIGNED: "Atandı",
            DOFStatus.IN_PROGRESS: "Devam Ediyor",
            DOFStatus.RESOLVED: "Çözüldü",
            DOFStatus.CLOSED: "Kapatıldı",
            DOFStatus.REJECTED: "Reddedildi",
            DOFStatus.PLANNING: "Aksiyon Planı Hazırlanıyor",
            DOFStatus.IMPLEMENTATION: "Aksiyon Planı Onaylandı",
            DOFStatus.COMPLETED: "Tamamlandı",
            DOFStatus.SOURCE_REVIEW: "Kaynak İncelemesi"
        }
        return statuses.get(self.status, "Bilinmiyor")
    
    @property
    def type_name(self):
        types = {
            DOFType.CORRECTIVE: "Düzeltici Faaliyet",
            DOFType.PREVENTIVE: "Önleyici Faaliyet",
            DOFType.IMPROVEMENT: "İyileştirme Talebi",
            DOFType.CORRECTIVE_REQUEST: "Düzeltici Faaliyet Talebi"
        }
        return types.get(self.dof_type, "Bilinmiyor")
    
    @property
    def source_name(self):
        sources = {
            DOFSource.INTERNAL_AUDIT: "İç Denetim",
            DOFSource.EXTERNAL_AUDIT: "Dış Denetim",
            DOFSource.CUSTOMER_COMPLAINT: "Müşteri Şikayeti",
            DOFSource.EMPLOYEE_SUGGESTION: "Çalışan Önerisi",
            DOFSource.NONCONFORMITY: "Uygunsuzluk",
            DOFSource.OTHER: "Diğer"
        }
        return sources.get(self.dof_source, "Bilinmiyor")
    
    # priority_name property'si kaldırıldı - artık kullanılmıyor
    
    def auto_assign_department(self):
        """Eğer DÖF'ün departmanı atanmamışsa, oluşturan kullanıcının departmanını ata"""
        if self.department_id is None and self.created_by is not None:
            from app import db
            creator = User.query.get(self.created_by)
            if creator and creator.department_id:
                self.department_id = creator.department_id
                db.session.commit()
                return True
        return False
        
    def can_be_deleted_by(self, user):
        """DÖF'ü belirli kullanıcının silme yetkisi var mı?"""
        # Admin her DÖF'ü silebilir
        if user.role == UserRole.ADMIN:
            return True
            
        # Kalite Yöneticisi her DÖF'ü silebilir
        if user.role == UserRole.QUALITY_MANAGER:
            return True
            
        # Taslak aşamasında ve oluşturan kişi ise silebilir
        if self.status == DOFStatus.DRAFT and self.created_by == user.id:
            return True
            
        return False
        
    def __repr__(self):
        return f'<DOF {self.id}: {self.title}>'

# DÖF Aksiyon Türleri
class DOFActionType:
    COMMENT = 1       # Yorum
    STATUS_CHANGE = 2 # Durum Değişikliği
    ASSIGNMENT = 3    # Atama
    DEPARTMENT_CHANGE = 4 # Departman Değişikliği
    NEW_DOF = 5      # Yeni DÖF Oluşturma

# DÖF Aksiyon modeli
class DOFAction(db.Model):
    __tablename__ = 'dof_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    dof_id = db.Column(db.Integer, db.ForeignKey('dofs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.Integer, nullable=True, default=1) # Kaldırıldı ama geriye uyumluluk için bırakıldı
    comment = db.Column(db.Text)
    old_status = db.Column(db.Integer, nullable=True)
    new_status = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Yorumlara ek dosyalar için ilişki
    attachments = db.relationship('ActionAttachment', backref='action', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DOFAction {self.id} for DOF {self.dof_id}>'

# Dosya Eki modeli
class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    dof_id = db.Column(db.Integer, db.ForeignKey('dofs.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    file_size = db.Column(db.Integer)  # Bytes cinsinden
    file_type = db.Column(db.String(50))
    
    # İlişkiler
    uploader = db.relationship('User', backref='uploads')
    
    def __repr__(self):
        return f'<Attachment {self.filename}>'

# Yorum Ekleri için yeni model
class ActionAttachment(db.Model):
    __tablename__ = 'action_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.Integer, db.ForeignKey('dof_actions.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    file_size = db.Column(db.Integer)  # Bytes cinsinden
    file_type = db.Column(db.String(50))
    
    # İlişkiler
    uploader = db.relationship('User', backref='action_uploads')
    
    def __repr__(self):
        return f'<ActionAttachment {self.filename}>'

# Bildirim modeli
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dof_id = db.Column(db.Integer, db.ForeignKey('dofs.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

# İş Akışı Tanımları modeli
class WorkflowDefinition(db.Model):
    __tablename__ = 'workflow_definitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # İlişkiler
    steps = db.relationship('WorkflowStep', backref='workflow', lazy='dynamic')
    
    def __repr__(self):
        return f'<WorkflowDefinition {self.name}>'

# İş Akışı Adımları modeli
class WorkflowStep(db.Model):
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow_definitions.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    required_role = db.Column(db.Integer)  # Hangi rolün bu adımı gerçekleştirebileceği
    from_status = db.Column(db.Integer, nullable=False)
    to_status = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<WorkflowStep {self.name} of {self.workflow.name}>'

# Sistem Logları modeli
class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    user = db.relationship('User', backref='logs')
    
    def __repr__(self):
        return f'<SystemLog {self.id}: {self.action}>'

# E-posta Ayarları modeli
class EmailSettings(db.Model):
    __tablename__ = 'email_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    mail_service = db.Column(db.String(20), default='smtp')  # smtp veya gmail
    smtp_host = db.Column(db.String(100))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_use_tls = db.Column(db.Boolean, default=True)
    smtp_use_ssl = db.Column(db.Boolean, default=False)
    smtp_user = db.Column(db.String(100))
    smtp_pass = db.Column(db.String(255))
    default_sender = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # İlişkiler
    user = db.relationship('User', backref='email_settings_updates')
    
    def __repr__(self):
        return f'<EmailSettings {self.id}: {self.smtp_host}>'

# Kullanıcı-Departman İlişki Tablosu (Çoklu departman yönetimi için)
class UserDepartmentMapping(db.Model):
    __tablename__ = 'user_department_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    user = db.relationship('User', backref=db.backref('managed_department_mappings', cascade="all, delete-orphan"))
    department = db.relationship('Department')

class DirectorManagerMapping(db.Model):
    __tablename__ = 'director_manager_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        # Bir direktör-bölge müdürü çifti tekil olmalı
        db.UniqueConstraint('director_id', 'manager_id', name='uq_director_manager'),
    )
    
    def __repr__(self):
        return f'<DirectorManagerMapping Director:{self.director_id} - Manager:{self.manager_id}>'

# Kullanıcı Aktiviteleri modeli
class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # login, logout, create_dof, review_dof, vb.
    description = db.Column(db.Text, nullable=True)
    related_id = db.Column(db.Integer, nullable=True)  # DOF ID, User ID, vb.
    ip_address = db.Column(db.String(50), nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişki
    user = db.relationship('User', backref='activities')
    
    def __repr__(self):
        return f'<UserActivity {self.user_id}: {self.activity_type}>'
    
    @staticmethod
    def log_activity(user, activity_type, description=None, related_id=None, ip_address=None, browser_info=None):
        """Kullanıcı aktivitesi kaydetme yardımcı metodu"""
        activity = UserActivity(
            user_id=user.id,
            activity_type=activity_type,
            description=description,
            related_id=related_id,
            ip_address=ip_address,
            browser_info=browser_info
        )
        db.session.add(activity)
        db.session.commit()
        return activity

# E-posta Takip modeli
class EmailTrack(db.Model):
    __tablename__ = 'email_tracks'
    
    id = db.Column(db.String(50), primary_key=True)  # UUID string formatında ID
    subject = db.Column(db.String(255), nullable=False)  # E-posta konusu
    recipients = db.Column(db.Text, nullable=False)  # Alıcılar (virgülle ayrılmış)
    status = db.Column(db.String(20), nullable=False)  # queued, sent, failed
    error = db.Column(db.Text)  # Hata mesajı (başarısız ise)
    created_at = db.Column(db.DateTime, default=datetime.now)  # Oluşturulma zamanı
    completed_at = db.Column(db.DateTime)  # Tamamlanma zamanı
    retry_count = db.Column(db.Integer, default=0)  # Yeniden deneme sayısı
    related_dof_id = db.Column(db.Integer, db.ForeignKey('dofs.id'), nullable=True)  # İlişkili DÖF ID
    
    # İlişkiler
    dof = db.relationship('DOF', backref='email_tracks', foreign_keys=[related_dof_id])
    
    def __repr__(self):
        return f'<EmailTrack {self.id[:8]}: {self.status}>'
    
    @classmethod
    def create_track(cls, subject, recipients, related_dof_id=None):
        """Yeni bir e-posta takibi oluştur"""
        import uuid
        track_id = str(uuid.uuid4())
        
        if isinstance(recipients, list):
            recipients_str = ",".join(recipients)
        else:
            recipients_str = recipients
            
        track = cls(
            id=track_id,
            subject=subject,
            recipients=recipients_str,
            status="queued",
            related_dof_id=related_dof_id
        )
        
        db.session.add(track)
        db.session.commit()
        return track
    
    @classmethod
    def update_status(cls, track_id, status, error=None):
        """E-posta takip durumunu güncelle"""
        track = cls.query.get(track_id)
        if track:
            track.status = status
            track.error = error
            track.completed_at = datetime.now()
            db.session.commit()
            return True
        return False
    
    @classmethod
    def get_pending_emails(cls):
        """Bekleyen e-postaları getir"""
        return cls.query.filter_by(status="queued").all()
    
    @classmethod
    def get_failed_emails(cls):
        """Başarısız e-postaları getir"""
        return cls.query.filter_by(status="failed").all()


# Teşekkür bildirim modeli
class ThankYou(db.Model):
    __tablename__ = 'thank_you'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    is_notified = db.Column(db.Boolean, default=False)
    
    # İlişkiler
    department = db.relationship('Department', backref='thank_yous')
    creator = db.relationship('User', backref='created_thank_yous')
    
    def __repr__(self):
        return f'<ThankYou {self.title}>'
    
    @classmethod
    def get_all_thank_yous(cls):
        """Tüm teşekkür bildirimlerini döndürür"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_department_thank_yous(cls, department_id):
        """Belirli bir departmana ait teşekkür bildirimlerini döndürür"""
        return cls.query.filter_by(department_id=department_id).order_by(cls.created_at.desc()).all()
