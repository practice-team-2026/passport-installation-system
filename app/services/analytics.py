# app/services/analytics.py
from app import db
from app.models.installation import Installation, MaintenanceEvent
from datetime import datetime, timedelta
from sqlalchemy import func

def get_total_installations():
    """
    Получить общее количество установок
    """
    return Installation.query.count()

def get_active_installations():
    """
    Получить количество активных установок
    """
    return Installation.query.filter_by(status='active').count()

def get_overdue_maintenance():
    """
    Получить количество просроченных ТО
    (planned_date < сегодня и статус scheduled)
    """
    today = datetime.now().date()
    return MaintenanceEvent.query.filter(
        MaintenanceEvent.planned_date < today,
        MaintenanceEvent.status == 'scheduled'
    ).count()

def get_upcoming_maintenance(days=7):
    """
    Получить количество ТО в ближайшие N дней
    """
    today = datetime.now().date()
    future = today + timedelta(days=days)
    return MaintenanceEvent.query.filter(
        MaintenanceEvent.planned_date >= today,
        MaintenanceEvent.planned_date <= future,
        MaintenanceEvent.status == 'scheduled'
    ).count()

def get_completed_maintenance_count():
    """
    Получить количество выполненных ТО
    """
    return MaintenanceEvent.query.filter_by(status='completed').count()

def get_maintenance_by_status():
    """
    Получить распределение ТО по статусам
    (для круговой диаграммы)
    """
    result = db.session.query(
        MaintenanceEvent.status,
        func.count(MaintenanceEvent.id).label('count')
    ).group_by(MaintenanceEvent.status).all()
    
    return {row.status: row.count for row in result}

def get_monthly_workload(months=6):
    """
    Получить прогноз загрузки по месяцам
    (группировка ТО по месяцам на следующие N месяцев)
    
    Возвращает словарь с метками и значениями для Chart.js
    """
    today = datetime.now().date()
    
    # Группируем ТО по месяцам (только будущие и scheduled)
    monthly_data = db.session.query(
        func.strftime('%Y-%m', MaintenanceEvent.planned_date).label('month'),
        func.count(MaintenanceEvent.id).label('count')
    ).filter(
        MaintenanceEvent.planned_date >= today,
        MaintenanceEvent.status == 'scheduled'
    ).group_by('month').order_by('month').limit(months).all()
    
    labels = [row.month for row in monthly_data]
    values = [row.count for row in monthly_data]
    
    # Если данных нет, добавляем заглушку
    if not labels:
        for i in range(months):
            month = (today + timedelta(days=30*i)).strftime('%Y-%m')
            labels.append(month)
            values.append(0)
    
    return {
        'labels': labels,
        'values': values
    }

def get_engineer_workload():
    """
    Получить загрузку инженеров
    (количество ТО по каждому инженеру)
    """
    result = db.session.query(
        MaintenanceEvent.engineer,
        func.count(MaintenanceEvent.id).label('count')
    ).filter(
        MaintenanceEvent.status == 'scheduled'
    ).group_by(MaintenanceEvent.engineer).all()
    
    return {row.engineer: row.count for row in result}

def get_dashboard_stats():
    """
    Главная функция для дашборда
    Возвращает все данные в одном JSON-объекте
    """
    return {
        'total': get_total_installations(),
        'active': get_active_installations(),
        'overdue': get_overdue_maintenance(),
        'upcoming': get_upcoming_maintenance(7),
        'completed': get_completed_maintenance_count(),
        'chart': get_monthly_workload(6),
        'by_status': get_maintenance_by_status(),
        'engineers': get_engineer_workload()
    }

def get_installation_stats(installation_id):
    """
    Получить статистику по конкретной установке
    """
    events = MaintenanceEvent.query.filter_by(installation_id=installation_id)
    
    total = events.count()
    completed = events.filter_by(status='completed').count()
    scheduled = events.filter_by(status='scheduled').count()
    overdue = events.filter(
        MaintenanceEvent.planned_date < datetime.now().date(),
        MaintenanceEvent.status == 'scheduled'
    ).count()
    
    return {
        'total_events': total,
        'completed': completed,
        'scheduled': scheduled,
        'overdue': overdue
    }