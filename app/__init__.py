# app/__init__.py

import os
from flask import Flask
from flask_mail import Mail
from config import config
from .extensions import db, login_manager, migrate, bcrypt, csrf, cache, limiter
from .models import User, Notification

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Initialize AI services
    initialize_ai_services(app)
    
    return app

def initialize_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    Mail(app)
    
    # Flask-Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

def register_blueprints(app):
    """Register Flask blueprints"""
    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .medications.routes import medications_bp
    from .health.routes import health_bp
    from .insights.routes import insights_bp
    from .notifications.routes import notifications_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(medications_bp, url_prefix='/medications')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(insights_bp, url_prefix='/insights')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

def register_context_processors(app):
    """Register context processors"""
    from datetime import datetime
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.context_processor
    def inject_user_notifications():
        from flask_login import current_user
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
            return {'unread_notifications': unread_count}
        return {'unread_notifications': 0}

def register_commands(app):
    """Register CLI commands"""
    from .commands import init_db, seed_db, create_admin
    
    app.cli.add_command(init_db)
    app.cli.add_command(seed_db)
    app.cli.add_command(create_admin)

def initialize_ai_services(app):
    """Initialize AI/ML services"""
    # This can be expanded to load AI models
    pass