# app/routes/api.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.installation import Installation, Location, Client, Equipment, MaintenanceEvent
from datetime import datetime
from sqlalchemy import func
import uuid
import os
from werkzeug.utils import secure_filename

bp = Blueprint('api', __name__)

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ЗАГРУЗКИ ФОТО ----------
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- НОВАЯ РУЧКА: ЗАГРУЗКА ФОТО ----------
@bp.route('/upload-photo', methods=['POST'])
def upload_photo():
    """Загрузить фото для объекта"""
    if 'photo' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Неподдерживаемый формат. Разрешены: png, jpg, jpeg, gif'
        }), 400
    
    # Генерируем уникальное имя файла
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Убеждаемся, что папка существует
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Сохраняем файл
    file.save(filepath)
    
    # Возвращаем путь для сохранения в БД
    return jsonify({
        'message': 'Фото успешно загружено',
        'photo_url': f"/uploads/{unique_filename}"
    }), 200


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
            'photo_url': inst.photo_url,
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
        'photo_url': inst.photo_url,
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
    """
    data = request.json
    print("📥 Получены данные:", data)  # 👈 Добавляем логирование
    
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
            pass
    
    # 👇 СОЗДАНИЕ УСТАНОВКИ (ЗДЕСЬ ВАЖНО)
    photo_url = data.get('photo_url')  # Получаем путь
    print(f"📸 photo_url получен: {photo_url}")  # 👈 Логируем
    
    installation = Installation(
        id=str(uuid.uuid4()),
        unique_code=data['unique_code'],
        name=data['name'],
        status=data.get('status', 'draft'),
        description=data.get('description', ''),
        location_id=location.id if location else None,
        client_id=client.id if client else None,
        next_maintenance_date=next_maintenance_date,
        photo_url=photo_url  # 👈 СОХРАНЯЕМ В БАЗУ
    )
    db.session.add(installation)
    db.session.flush()
    
    # Создание события ТО (если указана дата)
    if next_maintenance_date:
        from app.services.analytics import create_or_update_maintenance_event
        create_or_update_maintenance_event(
            installation_id=installation.id,
            date=next_maintenance_date,
            engineer=data.get('engineer', 'Не назначен'),
            description=data.get('maintenance_description', 'Плановое техническое обслуживание'),
            hours=data.get('hours_planned', 2.0)
        )
    
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
    
    if 'photo_url' in data:
        inst.photo_url = data.get('photo_url')
    
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
        try:
            from app.services.analytics import create_or_update_maintenance_event
            new_date = datetime.strptime(data['next_maintenance_date'], '%Y-%m-%d').date()
            create_or_update_maintenance_event(
                installation_id=inst.id,
                date=new_date,
                engineer=data.get('engineer', 'Не назначен'),
                description='Плановое техническое обслуживание',
                hours=data.get('hours_planned', 2.0)
            )
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
    """Получить статистику для дашборда (использует analytics сервис)"""
    try:
        from app.services.analytics import get_dashboard_stats as get_analytics_stats
        stats = get_analytics_stats()
        return jsonify({
            'total': stats['total'],
            'active': stats['active'],
            'overdue': stats['overdue'],
            'chart': stats['chart']
        }), 200
    except Exception as e:
        return jsonify({'error': f'Ошибка получения статистики: {str(e)}'}), 500