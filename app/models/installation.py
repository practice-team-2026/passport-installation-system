# app/models/installation.py
from app import db
from datetime import datetime
import uuid

class Installation(db.Model):
    __tablename__ = 'installations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    unique_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, active, emergency, archived
    description = db.Column(db.Text)
    
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id'))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    location = db.relationship('Location', backref='installations')
    client = db.relationship('Client', backref='installations')
    equipment = db.relationship('Equipment', backref='installation', lazy='dynamic')
    maintenance_events = db.relationship('MaintenanceEvent', backref='installation', lazy='dynamic')

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country = db.Column(db.String(100), default='Россия')
    region = db.Column(db.String(100))
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    gps_lat = db.Column(db.Float)
    gps_lon = db.Column(db.Float)

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    installation_id = db.Column(db.String(36), db.ForeignKey('installations.id'))
    model = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), unique=True)
    manufacturer = db.Column(db.String(100))
    install_date = db.Column(db.Date)
    warranty_until = db.Column(db.Date)

class MaintenanceEvent(db.Model):
    __tablename__ = 'maintenance_events'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    installation_id = db.Column(db.String(36), db.ForeignKey('installations.id'), nullable=False)
    type = db.Column(db.String(50))  # scheduled, urgent, inspection
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, overdue
    planned_date = db.Column(db.Date, nullable=False)
    actual_date = db.Column(db.Date)
    engineer = db.Column(db.String(150))
    description = db.Column(db.Text)
    hours_planned = db.Column(db.Float, default=2.0)