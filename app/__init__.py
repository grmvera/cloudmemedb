from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv() 

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configuración de la base de datos
    app.config['AWS_S3_BUCKET'] = 'cloudmemedb'
    app.config['AWS_REGION'] = 'us-east-1'


    # Configuración de Imagga
    app.config['IMAGGA_API_KEY'] = os.getenv('IMAGGA_API_KEY')
    app.config['IMAGGA_API_SECRET'] = os.getenv('IMAGGA_API_SECRET')
    app.config['TAGS_ENDPOINT'] = os.getenv('TAGS_ENDPOINT')

    # Configuración de la base de datos
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Configuración de carpeta para subir imágenes
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # Configuración de AWS
    app.config["AWS_ACCESS_KEY"] = os.getenv("AWS_ACCESS_KEY")
    app.config["AWS_SECRET_KEY"] = os.getenv("AWS_SECRET_KEY")
    app.config["AWS_S3_BUCKET"] = os.getenv("AWS_S3_BUCKET")

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    app.register_blueprint(main)

    return app
