import os


class Config:
    """Configuración base de SPIDER."""

    # Seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-insecure-key')

    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Revalida conexiones antes de usarlas (evita errores por conexiones
        # cerradas por MySQL después de inactividad).
        'pool_pre_ping': True,
        # Recicla conexiones cada ~4:40 min (por debajo del wait_timeout
        # por defecto de MySQL, 8h, pero seguro para servidores con
        # timeout corto).
        'pool_recycle': 280,
    }

    # Entorno
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'