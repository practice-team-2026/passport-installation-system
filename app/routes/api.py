# app/routes/api.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.installation import Installation, Location, Client, Equipment, MaintenanceEvent
from datetime import datetime

bp = Blueprint('api', __name__)

# ---------- УСТАНОВКИ (CRUD) ----------

@bp.route('/installations', methods=['GET'])
def get_installations():
    """Получить список всех установок"""
    installations = Installation.query.all()
    result = []
    for inst in installations:
        equipment_count = inst.equipment.count()
        next_maintenance = None
        upcoming_event = MaintenanceEvent.query.filter_by(
            installation_id=inst.id,
            status='scheduled'
        ).order_by(MaintenanceEvent.planned_date).first()
        if upcoming_event:
            next_maintenance = upcoming_event.planned_date.strftime('%Y-%m-%d')
        
        result.append({
            'id': inst.id,
            'unique_code': inst.unique_code,
            'name': inst.name,
            'status': inst.status,
            'city': inst.location.city if inst.location else '',
            'address': inst.location.address if inst.location else '',
            'next_maintenance': next_maintenance or '—',
            'equipment_count': equipment_count
        })
    return jsonify(result)

@bp.route('/installations/<id>', methods=['GET'])
def get_installation(id):
    """Получить полную карточку установки"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    equipment_list = [{
        'model': eq.model,
        'serial_number': eq.serial_number,
        'manufacturer': eq.manufacturer,
        'install_date': eq.install_date.strftime('%Y-%m-%d') if eq.install_date else None
    } for eq in inst.equipment.all()]
    
    events = [{
        'id': ev.id,
        'type': ev.type,
        'status': ev.status,
        'planned_date': ev.planned_date.strftime('%Y-%m-%d'),
        'actual_date': ev.actual_date.strftime('%Y-%m-%d') if ev.actual_date else None,
        'engineer': ev.engineer,
        'hours_planned': ev.hours_planned
    } for ev in inst.maintenance_events.all()]
    
    return jsonify({
        'id': inst.id,
        'unique_code': inst.unique_code,
        'name': inst.name,
        'status': inst.status,
        'description': inst.description,
        'location': {
            'city': inst.location.city if inst.location else '',
            'address': inst.location.address if inst.location else '',
            'gps_lat': inst.location.gps_lat if inst.location else None,
            'gps_lon': inst.location.gps_lon if inst.location else None
        },
        'client': {
            'name': inst.client.name if inst.client else '',
            'contact_person': inst.client.contact_person if inst.client else '',
            'phone': inst.client.phone if inst.client else '',
            'email': inst.client.email if inst.client else ''
        },
        'equipment': equipment_list,
        'maintenance_events': events,
        'created_at': inst.created_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/installations', methods=['POST'])
def create_installation():
    """Создать новую установку"""
    data = request.json
    
    location = Location(
        city=data.get('city', ''),
        address=data.get('address', '')
    )
    db.session.add(location)
    db.session.flush()
    
    inst = Installation(
        name=data['name'],
        unique_code=data['unique_code'],
        status=data.get('status', 'draft'),
        location_id=location.id
    )
    db.session.add(inst)
    db.session.commit()
    
    return jsonify({'message': 'Установка создана', 'id': inst.id}), 201

@bp.route('/installations/<id>', methods=['PUT'])
def update_installation(id):
    """Обновить установку"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    data = request.json
    inst.name = data.get('name', inst.name)
    inst.status = data.get('status', inst.status)
    
    if inst.location:
        inst.location.city = data.get('city', inst.location.city)
        inst.location.address = data.get('address', inst.location.address)
    
    db.session.commit()
    return jsonify({'message': 'Установка обновлена'})

@bp.route('/installations/<id>', methods=['DELETE'])
def delete_installation(id):
    """Мягкое удаление (архивация)"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    inst.status = 'archived'
    db.session.commit()
    return jsonify({'message': 'Установка архивирована'})

# ---------- АНАЛИТИКА (ДАШБОРД) ----------

@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Получить статистику для дашборда"""
    total = Installation.query.count()
    active = Installation.query.filter_by(status='active').count()
    
    today = datetime.now().date()
    overdue = MaintenanceEvent.query.filter(
        MaintenanceEvent.planned_date < today,
        MaintenanceEvent.status == 'scheduled'
    ).count()
    
    from sqlalchemy import func
    monthly_data = db.session.query(
        func.strftime('%Y-%m', MaintenanceEvent.planned_date).label('month'),
        func.count(MaintenanceEvent.id).label('count')
    ).filter(
        MaintenanceEvent.planned_date >= today
    ).group_by('month').order_by('month').limit(6).all()
    
    chart_data = {
        'labels': [row.month for row in monthly_data],
        'values': [row.count for row in monthly_data]
    }
    
    return jsonify({
        'total': total,
        'active': active,
        'overdue': overdue,
        'chart': chart_data
    })