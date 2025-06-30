from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, User, UserActivity, SystemLog
from sqlalchemy import desc
from functools import wraps

activity_bp = Blueprint('activity', __name__, url_prefix='/activity')

# Yetki kontrol dekoratörü
def admin_or_quality_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            if not current_user.is_quality_manager():
                flash('Bu sayfaya erişim yetkiniz bulunmamaktadır.', 'danger')
                return redirect(url_for('dof.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Sadece admin için yetki kontrol dekoratörü
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Bu sayfaya sadece admin erişebilir.', 'danger')
            return redirect(url_for('dof.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Kullanıcı aktiviteleri listesi sayfası
@activity_bp.route('/', methods=['GET'])
@login_required
@admin_or_quality_required
def activity_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtreleme parametreleri
    user_id = request.args.get('user_id', type=int)
    activity_type = request.args.get('activity_type', type=str)
    date_from = request.args.get('date_from', type=str)
    date_to = request.args.get('date_to', type=str)
    
    # Sorgu oluştur
    query = UserActivity.query.join(User)
    
    # Filtreleri uygula
    if user_id:
        query = query.filter(UserActivity.user_id == user_id)
    if activity_type:
        query = query.filter(UserActivity.activity_type == activity_type)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(UserActivity.created_at >= date_from_obj)
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı', 'warning')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(UserActivity.created_at <= date_to_obj)
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı', 'warning')
    
    # Sonuçları sırala ve sayfalandır
    activities = query.order_by(desc(UserActivity.created_at)).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Kullanıcı ve aktivite tip listelerini hazırla
    users = User.query.all()
    activity_types = db.session.query(UserActivity.activity_type).distinct().all()
    activity_types = [a[0] for a in activity_types]
    
    return render_template('activity/list.html', 
                          activities=activities,
                          users=users,
                          activity_types=activity_types,
                          selected_user_id=user_id,
                          selected_activity_type=activity_type,
                          selected_date_from=date_from,
                          selected_date_to=date_to)

# Sistem logları listesi - sadece admin
@activity_bp.route('/system-logs', methods=['GET'])
@login_required
@admin_required
def system_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtreleme parametreleri
    date_from = request.args.get('date_from', type=str)
    date_to = request.args.get('date_to', type=str)
    
    # Sorgu oluştur
    query = SystemLog.query
    
    # Filtreleri uygula
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SystemLog.created_at >= date_from_obj)
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı', 'warning')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(SystemLog.created_at <= date_to_obj)
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı', 'warning')
    
    # Sonuçları sırala ve sayfalandır
    logs = query.order_by(desc(SystemLog.created_at)).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('activity/system_logs.html', 
                          logs=logs,
                          selected_date_from=date_from,
                          selected_date_to=date_to)
