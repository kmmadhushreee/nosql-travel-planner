
from flask import Flask
from config import Config
from models import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.booking import booking_bp
    from routes.stress import stress_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(stress_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
