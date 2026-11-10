from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .config import Config
from .extensions import db, migrate
from .core.exceptions import register_error_handlers
from .cli import register_cli

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    allowed_origins = ['http://localhost:5173', 'http://127.0.0.1:5173']
    CORS(app, resources={r'/api/*': {'origins': allowed_origins}})

    db.init_app(app)
    migrate.init_app(app, db)

    # Importar modelos
    from .modules.companies import models as _companies_models  # noqa: F401
    from .modules.branches import models as _branches_models  # noqa: F401
    from .modules.crm import models as _crm_models  # noqa: F401
    from .modules.leads import models as _leads_models  # noqa: F401
    from .modules.pipeline import models as _pipeline_models  # noqa: F401
    from .modules.social_media import models as _social_models  # noqa: F401
    from .modules.inventory import models as _inventory_models  # noqa: F401

    # Blueprints
    from .modules.companies.routes import companies_bp
    from .modules.branches.routes import branches_bp
    from .modules.crm.routes import crm_bp
    from .modules.leads.routes import leads_bp, public_leads_bp
    from .modules.pipeline.routes import pipeline_bp
    from .modules.social_media.routes import social_bp
    from .modules.inventory.routes import inventory_bp

    app.register_blueprint(companies_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(public_leads_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(inventory_bp)

    register_error_handlers(app)
    register_cli(app)

    @app.route('/api/health', methods=['GET'])
    def health():
        database_status = 'unavailable'
        try:
            db.session.execute(text('SELECT 1'))
            database_status = 'ok'
        except Exception:
            db.session.rollback()
        return jsonify({
            'status': 'ok',
            'service': 'spider-backend',
            'version': '0.8.0',
            'database': database_status,
        })

    @app.route('/api/ping', methods=['GET'])
    def ping():
        return jsonify({'message': 'pong'})

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'not_found', 'message': 'Ruta no encontrada'}), 404

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        return jsonify({'error': 'conflict', 'message': 'Conflicto de integridad en la base de datos.'}), 409

    return app