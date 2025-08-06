"""
Auth Service - Yetki ve İzin Kontrol Servisi
-------------------------------------------
Tüm yetki kontrolleri için kullanılacak merkezi servis modülü.
Bu modül, farklı kullanıcı rollerine göre görüntüleme ve düzenleme izinlerini yönetir.
Proje genelinde tutarlı yetkilendirme sağlar.

Kullanım:
    from auth_service import AuthService
    
    # Bir DOF'un görüntülenebilirlik kontrolü
    if AuthService.can_view_dof(current_user, dof_object):
        # Görüntüleme işlemleri
"""

from flask import current_app
from enum import Enum
from typing import List, Optional, Any
from sqlalchemy import or_, and_

class AuthService:
    """Merkezi yetki kontrol servisi"""

    @staticmethod
    def can_view_dof(user: Any, dof: Any) -> bool:
        """
        Kullanıcının bir DÖF'ü görüntüleme yetkisi olup olmadığını kontrol eder
        
        Args:
            user: Kullanıcı nesnesi (current_user)
            dof: Görüntülenecek DÖF nesnesi
            
        Returns:
            bool: Görüntüleme yetkisi varsa True, yoksa False
        """
        # Import burada yapılıyor çünkü circular import sorununu önlemek gerekiyor
        from models import UserRole
        
        try:
            # Admin ve kalite yöneticileri her şeyi görebilir
            if user.role == UserRole.ADMIN or user.role == UserRole.QUALITY_MANAGER:
                return True
            
            # Normal kullanıcılar sadece kendi oluşturdukları ve kendilerine atananları görebilir
            if user.role == UserRole.USER:
                return dof.created_by == user.id or dof.assigned_to == user.id
            
            # Departman yöneticileri kendi departmanlarını görebilir
            if user.role == UserRole.DEPARTMENT_MANAGER and user.department_id:
                return dof.department_id == user.department_id
            
            # Bölge müdürleri sadece kendi yönettikleri departmanların DÖF'lerini görebilir
            if user.role == UserRole.GROUP_MANAGER:
                managed_departments = user.get_managed_departments()
                managed_dept_ids = [dept.id for dept in managed_departments]
                return dof.department_id in managed_dept_ids
            
            # Direktörler altındaki bölge müdürlerinin yönettiği departmanların DÖF'lerini görebilir
            if user.role == UserRole.DIRECTOR:
                managed_departments = user.get_managed_departments()
                managed_dept_ids = [dept.id for dept in managed_departments]
                return dof.department_id in managed_dept_ids
            
            # Diğer tüm durumlar için yetki yok
            return False
            
        except Exception as e:
            current_app.logger.error(f"DÖF görüntüleme yetki kontrolü hatası: {str(e)}")
            # Hata durumunda güvenli tarafta kal - yetkisiz
            return False
    
    @staticmethod
    def filter_viewable_dofs(user: Any, query: Any) -> Any:
        """
        Sorguyu kullanıcının yetkisine göre filtreler
        
        Args:
            user: Kullanıcı nesnesi (current_user)
            query: Başlangıç DÖF sorgusu
            
        Returns:
            query: Filtrelenmiş sorgu
        """
        # Import burada yapılıyor çünkü circular import sorununu önlemek gerekiyor
        from models import UserRole, DOF
        
        try:
            # İlişkili DÖF'leri filtreleme - tüm kullanıcı rolleri için geçerli
            # İlişkili DÖF'ler başlığında "[İlişkili #" prefix'i içerir
            related_dof_filter = ~DOF.title.like("[İlişkili #%")
            query = query.filter(related_dof_filter)
            current_app.logger.info("AuthService: İlişkili DÖF'ler filtrelendi")
            
            # Admin ve kalite yöneticileri için başka filtreleme yok, tümünü görebilirler
            if user.role == UserRole.ADMIN or user.role == UserRole.QUALITY_MANAGER:
                return query
            
            # Normal kullanıcılar sadece kendi oluşturdukları ve kendilerine atananları görebilir 
            elif user.role == UserRole.USER:
                return query.filter(or_(DOF.created_by == user.id, DOF.assigned_to == user.id))
            
            # Departman yöneticileri kendi departmanlarına ait DÖF'leri görebilir
            elif user.role == UserRole.DEPARTMENT_MANAGER and user.department_id:
                # Widget amacı için departman_id ile eşleşen VEYA bu departmandaki herhangi biri tarafından 
                # oluşturulan DÖF'leri göster (oluşturan kullanıcının departmanı)
                dept_users_ids = [u.id for u in user.department.users] if hasattr(user, 'department') and user.department else []
                current_app.logger.debug(f"Departman yöneticisi {user.username} için dept_id={user.department_id}, dept_users={dept_users_ids}")
                
                if dept_users_ids:
                    # Hem departmanın atandığı DÖF'ler hem de departman üyeleri tarafından oluşturulan DÖF'ler
                    return query.filter(or_(DOF.department_id == user.department_id, 
                                           DOF.created_by.in_(dept_users_ids)))
                else:
                    return query.filter(DOF.department_id == user.department_id)
            
            # Çoklu departman yöneticileri sadece yönettikleri departmanların DÖF'lerini görebilir
            elif user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                managed_departments = user.get_managed_departments()
                managed_dept_ids = [dept.id for dept in managed_departments]
                
                if managed_dept_ids:
                    current_app.logger.debug(f"Çoklu departman yöneticisi ({user.role_name}) {user.username} için departman filtresi: {managed_dept_ids}")
                    return query.filter(DOF.department_id.in_(managed_dept_ids))
                else:
                    current_app.logger.warning(f"Çoklu departman yöneticisi ({user.role_name}) {user.username} için yönetilen departman bulunamadı")
                    # Hiçbir departman yönetmiyorsa boş sorgu döndür
                    return query.filter(DOF.id == -1)  # Hiçbir zaman eşleşmeyecek bir filtre
            
            # Direktörler altındaki bölge müdürlerinin yönettiği departmanların DÖF'lerini görebilir
            elif user.role == UserRole.DIRECTOR:
                managed_departments = user.get_managed_departments()
                managed_dept_ids = [dept.id for dept in managed_departments]
                
                if managed_dept_ids:
                    current_app.logger.debug(f"Direktör {user.username} için departman filtresi: {managed_dept_ids}")
                    return query.filter(DOF.department_id.in_(managed_dept_ids))
                else:
                    current_app.logger.warning(f"Direktör {user.username} için yönetilen departman bulunamadı")
                    # Hiçbir departman yönetmiyorsa boş sorgu döndür
                    return query.filter(DOF.id == -1)  # Hiçbir zaman eşleşmeyecek bir filtre
            
            # Diğer tüm durumlar için boş sorgu döndür - güvenli tarafta kal
            return query.filter(DOF.id == -1)  # Hiçbir zaman eşleşmeyecek bir filtre
            
        except Exception as e:
            current_app.logger.error(f"DÖF filtreleme hatası: {str(e)}")
            # Hata durumunda güvenli tarafta kal - boş sorgu
            return query.filter(DOF.id == -1)  # Hiçbir zaman eşleşmeyecek bir filtre
    
    @staticmethod 
    def can_edit_dof(user: Any, dof: Any) -> bool:
        """
        Kullanıcının bir DÖF'ü düzenleme yetkisi olup olmadığını kontrol eder
        
        Args:
            user: Kullanıcı nesnesi (current_user)
            dof: Düzenlenecek DÖF nesnesi
            
        Returns:
            bool: Düzenleme yetkisi varsa True, yoksa False
        """
        # Import burada yapılıyor çünkü circular import sorununu önlemek gerekiyor
        from models import UserRole, DOFStatus
        
        try:
            # Admin her şeyi düzenleyebilir
            if user.role == UserRole.ADMIN:
                return True
            
            # Kalite yöneticisi çoğu durumda düzenleyebilir
            if user.role == UserRole.QUALITY_MANAGER:
                # Kalite yöneticileri tamamlanan DÖF'leri düzenleyemez
                if dof.status == DOFStatus.COMPLETED or dof.status == DOFStatus.CLOSED:
                    return False
                return True
            
            # Hem oluşturan kişi hem de DÖF'ün durumu uygunsa düzenleme yapılabilir
            is_creator = dof.created_by == user.id
            is_editable_status = dof.status in [DOFStatus.DRAFT, DOFStatus.PENDING]
            
            # Oluşturucuysa ve durum uygunsa düzenlenebilir
            if is_creator and is_editable_status:
                return True
            
            # Diğer tüm durumlar için yetki yok
            return False
            
        except Exception as e:
            current_app.logger.error(f"DÖF düzenleme yetki kontrolü hatası: {str(e)}")
            # Hata durumunda güvenli tarafta kal - yetkisiz
            return False
