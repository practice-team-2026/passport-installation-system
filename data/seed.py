# data/seed.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.installation import Installation, Location, Client, Equipment, MaintenanceEvent
from datetime import datetime, timedelta
import random
import uuid

def generate_test_data():
    app = create_app()
    with app.app_context():
        # Очищаем БД
        db.drop_all()
        db.create_all()
        
        # Данные для генерации
        cities = [
            ('Москва', ['Тверская', 'Ленина', 'Пушкина', 'Садовое кольцо', 'Новый Арбат']),
            ('СПб', ['Невский', 'Московский', 'Лиговский', 'Большой пр.']),
            ('Казань', ['Баумана', 'Кремлевская', 'Пушкина']),
            ('Екатеринбург', ['Ленина', 'Малышева', '8 Марта']),
            ('Новосибирск', ['Красный пр.', 'Советская', 'Кирова'])
        ]
        
        models = [
            'VRV-400', 'Вентилятор ВР-100', 'Компрессор X7', 
            'Фильтр G4', 'Датчик PT-100', 'Чиллер YC-200',
            'Теплообменник Т-300', 'Насос Wilo', 'Шкаф управления ШУ-100'
        ]
        
        manufacturers = ['Bosch', 'Siemens', 'LG', 'Daikin', 'Grundfos', 'Danfoss']
        clients = [
            'ООО ТехноСтрой', 'АО Инженерные системы', 'ИП Иванов',
            'ПАО Газпром-сервис', 'ТСЖ Центральное', 'ООО Северные сети'
        ]
        
        engineers = [
            'Бригада №1 (Сидоров)', 'Бригада №2 (Петров)', 
            'Бригада №3 (Смирнов)', 'Бригада №4 (Кузнецов)'
        ]
        
        print('🔄 Начинаю генерацию тестовых данных...')
        
        for i in range(1, 31):
            city_data = random.choice(cities)
            city = city_data[0]
            street = random.choice(city_data[1])
            
            # 1. Локация
            loc = Location(
                id=str(uuid.uuid4()),
                country='Россия',
                region='Центральный' if city == 'Москва' else 'Северо-Западный' if city == 'СПб' else 'Приволжский',
                city=city,
                address=f'{street}, {random.randint(1, 100)}',
                gps_lat=round(random.uniform(55.0, 60.0), 6),
                gps_lon=round(random.uniform(30.0, 40.0), 6)
            )
            db.session.add(loc)
            db.session.flush()
            
            # 2. Клиент
            client = Client(
                id=str(uuid.uuid4()),
                name=random.choice(clients),
                contact_person=f'{random.choice(["Иван", "Петр", "Сергей", "Алексей"])} {random.choice(["Петрович", "Сидорович", "Иванович"])}',
                phone=f'+7 9{random.randint(100, 999)} {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                email=f'client_{i}@{random.choice(["gmail.com", "yandex.ru", "mail.ru"])}'
            )
            db.session.add(client)
            db.session.flush()
            
            # 3. Установка
            statuses = ['active', 'active', 'active', 'draft', 'archived', 'emergency']
            install_types = ['Вентиляционная', 'Кондиционирование', 'Насосная', 'Компрессорная', 'Холодильная']
            install = Installation(
                id=str(uuid.uuid4()),
                name=f'{random.choice(install_types)} установка "{city}-{i:03d}"',
                unique_code=f'ПАС-{i:03d}',
                status=random.choice(statuses),
                description=f'Монтаж выполнен {random.randint(2020, 2025)} году. Обслуживает {random.choice(["ТЦ", "Офис", "Жилой комплекс", "Завод"])}.',
                location_id=loc.id,
                client_id=client.id
            )
            db.session.add(install)
            db.session.flush()
            
            # 4. Оборудование (2-4 единицы)
            equipment_count = random.randint(2, 4)
            for _ in range(equipment_count):
                install_date = datetime.now() - timedelta(days=random.randint(100, 1500))
                eq = Equipment(
                    id=str(uuid.uuid4()),
                    installation_id=install.id,
                    model=random.choice(models),
                    serial_number=f'SN-{random.randint(10000, 99999)}',
                    manufacturer=random.choice(manufacturers),
                    install_date=install_date,
                    warranty_until=install_date + timedelta(days=random.randint(365, 1095))
                )
                db.session.add(eq)
            
            # 5. События ТО (1-3 на объект)
            events_count = random.randint(1, 3)
            for _ in range(events_count):
                days_offset = random.randint(-60, 120)
                planned_date = datetime.now() + timedelta(days=days_offset)
                is_completed = planned_date < datetime.now()
                
                event = MaintenanceEvent(
                    id=str(uuid.uuid4()),
                    installation_id=install.id,
                    type=random.choice(['scheduled', 'urgent', 'inspection']),
                    status='completed' if is_completed else random.choice(['scheduled', 'overdue']),
                    planned_date=planned_date,
                    actual_date=planned_date + timedelta(days=random.randint(0, 5)) if is_completed else None,
                    engineer=random.choice(engineers),
                    description=f'Плановое ТО' if random.random() > 0.3 else f'Внеплановый осмотр',
                    hours_planned=round(random.choice([1.0, 1.5, 2.0, 3.0, 4.0]), 1)
                )
                db.session.add(event)
            
            if i % 10 == 0:
                print(f'  ✅ Создано {i} объектов...')
        
        db.session.commit()
        print('\n✅ ========================================')
        print(f'✅ УСПЕШНО СОЗДАНО 30 ТЕСТОВЫХ ОБЪЕКТОВ!')
        print('✅ ========================================')
        print('📊 Статистика:')
        print(f'   - Установок: {Installation.query.count()}')
        print(f'   - Локаций: {Location.query.count()}')
        print(f'   - Клиентов: {Client.query.count()}')
        print(f'   - Оборудования: {Equipment.query.count()}')
        print(f'   - Событий ТО: {MaintenanceEvent.query.count()}')
        print('\n🚀 Теперь можно запускать сервер: python run.py')

if __name__ == '__main__':
    generate_test_data()