#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DÖF istatistikleri için yardımcı fonksiyonlar
"""

from app import db
from models import DOFStatus


def get_default_status_dict():
    """
    Varsayılan DÖF durum sayılarını içeren sözlük
    """
    return {
        'draft': 0,
        'submitted': 0,
        'in_review': 0,
        'assigned': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0,
        'rejected': 0,
        'planning': 0,
        'implementation': 0,
        'completed': 0,
        'source_review': 0,
        'total': 0
    }


def get_dof_status_counts(department_id=None, user_id=None, current_user=None):
    """
    DÖF'lerin durum bazında sayılarını kullanıcı yetkisine göre filtreli şekilde getir
    Eğer department_id belirtilirse, sadece o departmana ait DÖF'leri sayar
    Eğer user_id belirtilirse, sadece o kullanıcının oluşturduğu DÖF'leri sayar
    Eğer current_user belirtilirse, kullanıcının yetkisi dahilindeki DÖF'leri gösterir
    
    Args:
        department_id: Departman ID (isteğe bağlı)
        user_id: Kullanıcı ID (isteğe bağlı)
        current_user: Mevcut oturum kullanıcısı (yetki kontrollerini uygulamak için)
        
    Returns:
        DöF sayılarını içeren sözlük
    """
    from models import DOF, User, UserRole
    from sqlalchemy import func, or_
    from flask import current_app
    import sys
    
    # Başlangıç sorgusu
    base_query = db.session.query(DOF)
    
    # Kullanıcı ve departman filtreleri
    if user_id:
        base_query = base_query.filter(DOF.created_by == user_id)
    elif department_id:
        # Departman kullanıcılarını bul
        dept_users = User.query.filter_by(department_id=department_id).all()
        dept_user_ids = [user.id for user in dept_users]
        
        # Departman filtresi uygula
        if dept_user_ids:
            base_query = base_query.filter(or_(
                DOF.department_id == department_id,
                DOF.created_by.in_(dept_user_ids)
            ))
        else:
            # Sadece departmana atanan DÖF'leri filtrele
            base_query = base_query.filter(DOF.department_id == department_id)
    
    # Eğer current_user belirtilmişse ve normal admin veya kalite yöneticisi değilse,
    # yönetilen departmanların DÖF'lerini göster
    if current_user:
        try:
            # Merkezi AuthService ile yetki kontrolü
            if hasattr(current_user, 'role') and current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
                # AuthService'i içe aktar
                try:
                    from auth_service import AuthService
                    
                    # Loglamayı aktif et
                    current_app.logger.info(f"DÖF özet sayıları için AuthService filtrelemesi uygulanıyor: {current_user.username}, rol={current_user.role}")
                    
                    # AuthService kullanarak yetkiye göre sorguyu filtrele
                    base_query = AuthService.filter_viewable_dofs(current_user, base_query)
                except ImportError:
                    current_app.logger.error("AuthService import edilemedi: " + str(sys.exc_info()[1]))
                except Exception as e:
                    current_app.logger.error(f"AuthService DÖF filtreleme hatası: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"DÖF özet sayıları filtreleme hatası: {str(e)}")
    
    # Duruma göre gruplama için yeniden sorgu oluştur
    query = db.session.query(DOF.status, func.count(DOF.id)).select_from(base_query.subquery())
    
    # Duruma göre gruplama ve sonuç
    result = query.group_by(DOF.status).all()
    
    # Boş sonuç sözlüğü oluştur
    counts = get_default_status_dict()
    
    # Toplam sayıyı hesapla
    total = 0
    
    # Durum sayılarını doldur
    for status, count in result:
        total += count
        if status == DOFStatus.DRAFT:
            counts['draft'] = count
        elif status == DOFStatus.SUBMITTED:
            counts['submitted'] = count
        elif status == DOFStatus.IN_REVIEW:
            counts['in_review'] = count
        elif status == DOFStatus.ASSIGNED:
            counts['assigned'] = count
        elif status == DOFStatus.IN_PROGRESS:
            counts['in_progress'] = count
        elif status == DOFStatus.RESOLVED:
            counts['resolved'] = count
        elif status == DOFStatus.CLOSED:
            counts['closed'] = count
        elif status == DOFStatus.REJECTED:
            counts['rejected'] = count
        elif status == DOFStatus.PLANNING:
            counts['planning'] = count
        elif status == DOFStatus.IMPLEMENTATION:
            counts['implementation'] = count
        elif status == DOFStatus.COMPLETED:
            counts['completed'] = count
        elif status == DOFStatus.SOURCE_REVIEW:
            counts['source_review'] = count
    
    # Toplam değerini güncelle
    counts['total'] = total
    
    return counts


def get_dof_status_counts_for_multiple_departments(department_ids):
    """
    Birden fazla departmana ait DÖF'lerin durum bazında sayılarını getir
    Bölge müdürleri gibi birden fazla departmanı yöneten kullanıcılar için
    """
    from models import DOF, User
    from sqlalchemy import func, or_
    
    if not department_ids:
        # Boş liste gönderilmişse boş sonuç döndür
        return get_default_status_dict()
    
    # Başlangıç sorgusu
    query = db.session.query(DOF.status, func.count(DOF.id))
    
    # Departmanlara atanan veya departman üyeleri tarafından oluşturulan DÖF'leri filtrele
    # Önce tüm departmanlardaki kullanıcıları bul
    dept_users = User.query.filter(User.department_id.in_(department_ids)).all()
    dept_user_ids = [user.id for user in dept_users]
    
    # Filtreleme yap
    query = query.filter(or_(
        DOF.department_id.in_(department_ids),  # Bu departmanlardan birine atanan DÖF'ler
        DOF.created_by.in_(dept_user_ids)  # Bu departmanlardaki kullanıcıların oluşturduğu DÖF'ler
    ))
    
    # Duruma göre gruplama ve sonuç
    result = query.group_by(DOF.status).all()
    
    counts = get_default_status_dict()
    
    # Toplam sayıyı hesapla
    total = 0
    
    # Sonuçları counts sözlüğüne ekle
    for status, count in result:
        total += count
        if status == DOFStatus.DRAFT:
            counts['draft'] = count
        elif status == DOFStatus.SUBMITTED:
            counts['submitted'] = count
        elif status == DOFStatus.IN_REVIEW:
            counts['in_review'] = count
        elif status == DOFStatus.ASSIGNED:
            counts['assigned'] = count
        elif status == DOFStatus.IN_PROGRESS:
            counts['in_progress'] = count
        elif status == DOFStatus.RESOLVED:
            counts['resolved'] = count
        elif status == DOFStatus.CLOSED:
            counts['closed'] = count
        elif status == DOFStatus.REJECTED:
            counts['rejected'] = count
        elif status == DOFStatus.PLANNING:
            counts['planning'] = count
        elif status == DOFStatus.IMPLEMENTATION:
            counts['implementation'] = count
        elif status == DOFStatus.COMPLETED:
            counts['completed'] = count
        elif status == DOFStatus.SOURCE_REVIEW:
            counts['source_review'] = count
    
    # Toplam değerini güncelle
    counts['total'] = total
    
    return counts
