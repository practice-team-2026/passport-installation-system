from app import create_app, db
from app.models.installation import *

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Таблицы созданы!")