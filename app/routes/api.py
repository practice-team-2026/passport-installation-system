# app/routes/api.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.installation import Installation, Location, Client, Equipment, MaintenanceEvent
from datetime import datetime
from sqlalchemy import func
import uuid

bp = Blueprint('api', __name__)

# ---------- ПОЛУЧИТЬ СПИСОК ВСЕХ УСТАНОВОК ----------
@bp.route('/installations', methods=['GET'])
def get_installations():
    """Получить список всех установок с краткой информацией"""
    installations = Installation.query.all()
    result = []
    for inst in installations:
        equipment_count = inst.equipment.count()
        
        # Берём дату ТО из поля next_maintenance_date
        next_maintenance = None
        if inst.next_maintenance_date:
            next_maintenance = inst.next_maintenance_date.strftime('%Y-%m-%d')
        
        # Если нет даты в поле, пытаемся найти ближайшее событие ТО
        if not next_maintenance:
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
            'next_maintenance': next_maintenance or None,
            'equipment_count': equipment_count,
            'created_at': inst.created_at.strftime('%Y-%m-%d %H:%M:%S') if inst.created_at else None
        })
    return jsonify(result)


# ---------- ПОЛУЧИТЬ ОДНУ УСТАНОВКУ (ПОЛНАЯ КАРТОЧКА) ----------
@bp.route('/installations/<id>', methods=['GET'])
def get_installation(id):
    """Получить полную информацию об установке по ID"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    # Оборудование
    equipment_list = [{
        'id': eq.id,
        'model': eq.model,
        'serial_number': eq.serial_number,
        'manufacturer': eq.manufacturer,
        'install_date': eq.install_date.strftime('%Y-%m-%d') if eq.install_date else None,
        'warranty_until': eq.warranty_until.strftime('%Y-%m-%d') if eq.warranty_until else None
    } for eq in inst.equipment.all()]
    
    # События ТО
    events = [{
        'id': ev.id,
        'type': ev.type,
        'status': ev.status,
        'planned_date': ev.planned_date.strftime('%Y-%m-%d'),
        'actual_date': ev.actual_date.strftime('%Y-%m-%d') if ev.actual_date else None,
        'engineer': ev.engineer,
        'description': ev.description,
        'hours_planned': ev.hours_planned
    } for ev in inst.maintenance_events.all()]
    
    return jsonify({
        'id': inst.id,
        'unique_code': inst.unique_code,
        'name': inst.name,
        'status': inst.status,
        'description': inst.description,
        'next_maintenance_date': inst.next_maintenance_date.strftime('%Y-%m-%d') if inst.next_maintenance_date else None,
        'location': {
            'id': inst.location.id if inst.location else None,
            'country': inst.location.country if inst.location else '',
            'region': inst.location.region if inst.location else '',
            'city': inst.location.city if inst.location else '',
            'address': inst.location.address if inst.location else '',
            'gps_lat': inst.location.gps_lat if inst.location else None,
            'gps_lon': inst.location.gps_lon if inst.location else None
        } if inst.location else None,
        'client': {
            'id': inst.client.id if inst.client else None,
            'name': inst.client.name if inst.client else '',
            'contact_person': inst.client.contact_person if inst.client else '',
            'phone': inst.client.phone if inst.client else '',
            'email': inst.client.email if inst.client else ''
        } if inst.client else None,
        'equipment': equipment_list,
        'maintenance_events': events,
        'created_at': inst.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': inst.updated_at.strftime('%Y-%m-%d %H:%M:%S') if inst.updated_at else None
    })

    # ---------- СОЗДАНИЕ НОВОЙ УСТАНОВКИ ----------
@bp.route('/installations', methods=['POST'])
def create_installation():
    """
    Создание новой установки с полной информацией.
    Ожидает JSON:
    {
        "unique_code": "ПАС-031",
        "name": "Вентиляционная установка",
        "city": "Москва",
        "address": "ул. Тверская, 12",
        "status": "active",
        "description": "Описание объекта",
        "client_name": "ООО ТехноСтрой",
        "client_contact": "Иванов Иван",
        "client_phone": "+7 999 123-45-67",
        "client_email": "client@mail.ru",
        "next_maintenance_date": "2026-08-15"
    }
    """
    data = request.json
    
    # Валидация обязательных полей
    required_fields = ['unique_code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Поле "{field}" обязательно для заполнения'}), 400
    
    # Проверка уникальности кода
    existing = Installation.query.filter_by(unique_code=data['unique_code']).first()
    if existing:
        return jsonify({'error': f'Установка с кодом "{data["unique_code"]}" уже существует'}), 400
    
    # Создание локации (если есть данные)
    location = None
    if data.get('city') or data.get('address'):
        location = Location(
            id=str(uuid.uuid4()),
            country=data.get('country', 'Россия'),
            region=data.get('region', ''),
            city=data.get('city', ''),
            address=data.get('address', ''),
            gps_lat=data.get('gps_lat'),
            gps_lon=data.get('gps_lon')
        )
        db.session.add(location)
        db.session.flush()
    
    # Создание клиента (если есть данные)
    client = None
    if data.get('client_name'):
        client = Client(
            id=str(uuid.uuid4()),
            name=data['client_name'],
            contact_person=data.get('client_contact', ''),
            phone=data.get('client_phone', ''),
            email=data.get('client_email', '')
        )
        db.session.add(client)
        db.session.flush()
    
    # Парсинг даты ТО
    next_maintenance_date = None
    if data.get('next_maintenance_date'):
        try:
            next_maintenance_date = datetime.strptime(data['next_maintenance_date'], '%Y-%m-%d').date()
        except ValueError:
            # Если дата невалидна — просто игнорируем
            pass
    
    # Создание установки
    installation = Installation(
        id=str(uuid.uuid4()),
        unique_code=data['unique_code'],
        name=data['name'],
        status=data.get('status', 'draft'),
        description=data.get('description', ''),
        location_id=location.id if location else None,
        client_id=client.id if client else None,
        next_maintenance_date=next_maintenance_date
    )
    db.session.add(installation)
    db.session.flush()
    
    # Создание события ТО (если указана дата)
    if next_maintenance_date:
        event = MaintenanceEvent(
            id=str(uuid.uuid4()),
            installation_id=installation.id,
            type='scheduled',
            status='scheduled',
            planned_date=next_maintenance_date,
            engineer=data.get('engineer', 'Не назначен'),
            description=data.get('maintenance_description', 'Плановое техническое обслуживание'),
            hours_planned=data.get('hours_planned', 2.0)
        )
        db.session.add(event)
    
    # Сохранение всех изменений
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при сохранении: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Установка успешно создана',
        'id': installation.id,
        'unique_code': installation.unique_code,
        'created_at': installation.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }), 201


# ---------- ОБНОВЛЕНИЕ УСТАНОВКИ ----------
@bp.route('/installations/<id>', methods=['PUT'])
def update_installation(id):
    """Обновить информацию об установке"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    data = request.json
    
    # Обновление основных полей
    inst.name = data.get('name', inst.name)
    inst.status = data.get('status', inst.status)
    inst.description = data.get('description', inst.description)
    
    # Обновление даты ТО
    if 'next_maintenance_date' in data:
        if data['next_maintenance_date']:
            try:
                inst.next_maintenance_date = datetime.strptime(data['next_maintenance_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            inst.next_maintenance_date = None
    
    # Обновление локации
    if inst.location:
        inst.location.city = data.get('city', inst.location.city)
        inst.location.address = data.get('address', inst.location.address)
        inst.location.region = data.get('region', inst.location.region)
        inst.location.country = data.get('country', inst.location.country)
        if data.get('gps_lat'):
            inst.location.gps_lat = data.get('gps_lat')
        if data.get('gps_lon'):
            inst.location.gps_lon = data.get('gps_lon')
    elif data.get('city') or data.get('address'):
        # Если локации не было, но данные пришли — создаём
        location = Location(
            id=str(uuid.uuid4()),
            country=data.get('country', 'Россия'),
            region=data.get('region', ''),
            city=data.get('city', ''),
            address=data.get('address', ''),
            gps_lat=data.get('gps_lat'),
            gps_lon=data.get('gps_lon')
        )
        db.session.add(location)
        db.session.flush()
        inst.location_id = location.id
    
    # Обновление клиента
    if inst.client and data.get('client_name'):
        inst.client.name = data.get('client_name', inst.client.name)
        inst.client.contact_person = data.get('client_contact', inst.client.contact_person)
        inst.client.phone = data.get('client_phone', inst.client.phone)
        inst.client.email = data.get('client_email', inst.client.email)
    elif data.get('client_name') and not inst.client:
        # Если клиента не было, но данные пришли — создаём
        client = Client(
            id=str(uuid.uuid4()),
            name=data['client_name'],
            contact_person=data.get('client_contact', ''),
            phone=data.get('client_phone', ''),
            email=data.get('client_email', '')
        )
        db.session.add(client)
        db.session.flush()
        inst.client_id = client.id
    
    # Если дата ТО изменилась — обновляем или создаём событие
    if 'next_maintenance_date' in data and data['next_maintenance_date']:
        # Ищем существующее запланированное событие ТО
        existing_event = MaintenanceEvent.query.filter_by(
            installation_id=inst.id,
            status='scheduled'
        ).order_by(MaintenanceEvent.planned_date).first()
        
        if existing_event:
            # Обновляем дату существующего события
            try:
                existing_event.planned_date = datetime.strptime(data['next_maintenance_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            # Создаём новое событие
            try:
                new_date = datetime.strptime(data['next_maintenance_date'], '%Y-%m-%d').date()
                event = MaintenanceEvent(
                    id=str(uuid.uuid4()),
                    installation_id=inst.id,
                    type='scheduled',
                    status='scheduled',
                    planned_date=new_date,
                    engineer=data.get('engineer', 'Не назначен'),
                    description='Плановое техническое обслуживание',
                    hours_planned=data.get('hours_planned', 2.0)
                )
                db.session.add(event)
            except ValueError:
                pass
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при сохранении: {str(e)}'}), 500

    return jsonify({
        'message': 'Установка успешно обновлена',
        'id': inst.id
    }), 200


# ---------- УДАЛЕНИЕ (АРХИВАЦИЯ) УСТАНОВКИ ----------
@bp.route('/installations/<id>', methods=['DELETE'])
def delete_installation(id):
    """Мягкое удаление — меняем статус на archived"""
    inst = Installation.query.get(id)
    if not inst:
        return jsonify({'error': 'Установка не найдена'}), 404
    
    inst.status = 'archived'
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при архивации: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Установка успешно архивирована',
        'id': inst.id,
        'status': inst.status
    }), 200


# ---------- АНАЛИТИКА ДЛЯ ДАШБОРДА ----------
@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Получить статистику для дашборда"""
    try:
        # Общее количество установок
        total = Installation.query.count()
        
        # Количество активных установок
        active = Installation.query.filter_by(status='active').count()
        
        # Количество просроченных ТО
        today = datetime.now().date()
        overdue = MaintenanceEvent.query.filter(
            MaintenanceEvent.planned_date < today,
            MaintenanceEvent.status == 'scheduled'
        ).count()
        
        # Данные для графика (группировка по месяцам на 6 месяцев вперёд)
        monthly_data = db.session.query(
            func.strftime('%Y-%m', MaintenanceEvent.planned_date).label('month'),
            func.count(MaintenanceEvent.id).label('count')
        ).filter(
            MaintenanceEvent.planned_date >= today,
            MaintenanceEvent.status == 'scheduled'
        ).group_by('month').order_by('month').limit(6).all()
        
        chart_data = {
            'labels': [row.month for row in monthly_data] if monthly_data else [],
            'values': [row.count for row in monthly_data] if monthly_data else []
        }
        
        return jsonify({
            'total': total,
            'active': active,
            'overdue': overdue,
            'chart': chart_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения статистики: {str(e)}'}), 500