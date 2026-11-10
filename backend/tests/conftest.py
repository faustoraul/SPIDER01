import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app import create_app
from app.config import Config
from app.extensions import db as _db


@event.listens_for(Engine, 'connect')
def _set_sqlite_pragma(dbapi_conn, connection_record):
    # SQLite no valida FKs por defecto. Necesitamos que sí para probar
    # el ON DELETE CASCADE y las FK de Branch.company_id.
    if dbapi_conn.__class__.__name__ == 'Connection':
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()