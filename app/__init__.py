import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Pega o diretório onde este arquivo está e sobe um nível para a raiz do projeto
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Define o caminho do banco explicitamente na pasta 'instance'
    db_path = os.path.join(basedir, 'instance', 'sgsv.db')
    
    app.config['SECRET_KEY'] = 'chave-super-secreta-lja-drones'
    # Usa o caminho absoluto com 3 barras (sqlite:///)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)

        from app import models
        db.create_all()

    return app