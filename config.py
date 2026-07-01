# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/passport.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Режим работы: development / production
    APP_ENV = os.environ.get('APP_ENV') or 'development'
    
    # Настройки для пагинации
    ITEMS_PER_PAGE = 20

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    # В production можно добавить более строгие настройки

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}