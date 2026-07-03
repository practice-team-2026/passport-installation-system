# app/routes/main.py
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Главная страница со списком объектов"""
    return render_template('index.html')

@bp.route('/dashboard')
def dashboard():
    """Страница дашборда с аналитикой"""
    return render_template('dashboard.html')