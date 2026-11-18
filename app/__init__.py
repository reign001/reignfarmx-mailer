from flask import Flask
from app.config import Config
from app.extensions import (
    db,
    migrate,
    mail
)


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Import models
    from app import models

    # Import blueprints
    from app.routes import (
        dashboard_bp,
        company_bp,
        templates_bp,
        campaigns_bp,
        company_contact_bp,
        product_bp,
        import_center_bp
    )

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(company_contact_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(import_center_bp)

    print("MAIL_SERVER:", app.config["MAIL_SERVER"])
    print("MAIL_PORT:", app.config["MAIL_PORT"])
    print("MAIL_USERNAME:", app.config["MAIL_USERNAME"])
    print("MAIL_USE_TLS:", app.config.get("MAIL_USE_TLS"))
    print("MAIL_USE_SSL:", app.config.get("MAIL_USE_SSL"))

    return app