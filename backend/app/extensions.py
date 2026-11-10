from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


# Instancias globales (sin app asociada todavía).
# Se inicializan en create_app() con init_app().
db = SQLAlchemy()
migrate = Migrate()