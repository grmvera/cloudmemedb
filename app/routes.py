from flask import Blueprint, request, jsonify, render_template, current_app
import requests
from app import db
from app.models import Meme, Etiqueta
import boto3
import threading  

# Función para obtener el cliente de S3
def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['AWS_SECRET_KEY']
    )


main = Blueprint('main', __name__)

#pagina principal
@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

#listar memes
@main.route('/api/memes', methods=['GET'])
def listar_memes():
    memes = Meme.query.all()
    response = []
    for meme in memes:
        etiquetas = [etiqueta.etiqueta for etiqueta in meme.etiquetas]
        print(f"📡 Meme {meme.id} tiene etiquetas: {etiquetas} y URL: {meme.ruta}")  

        response.append({
            "id": meme.id,
            "descripcion": meme.descripcion,
            "ruta": meme.ruta,  
            "usuario": meme.usuario,
            "etiquetas": etiquetas
        })
    return jsonify(response)


def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Subir meme
@main.route('/api/memes', methods=['POST'])
def subir_meme():
    descripcion = request.form.get('descripcion')
    usuario = request.form.get('usuario')
    imagen = request.files.get('imagen')
    etiquetas_personalizadas = request.form.getlist('etiquetas')  

    if not descripcion or not usuario or not imagen:
        return jsonify({"error": "Descripción, usuario e imagen son requeridos"}), 400

    # Guardar en S3
    s3_client = get_s3_client()
    bucket_name = current_app.config["AWS_S3_BUCKET"]
    s3_key = f"memes/{imagen.filename}" 
    s3_client.upload_fileobj(imagen, bucket_name, s3_key)

    # URL pública de la imagen en S3
    imagen_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

    # Guardar meme en la base de datos SIN etiquetas aún
    meme = Meme(descripcion=descripcion, ruta=imagen_url, usuario=usuario)
    db.session.add(meme)
    db.session.flush()  

    print(f"✅ Meme {meme.id} creado en la base de datos.")

    # Guardar etiquetas personalizadas ingresadas por el usuario
    for etiqueta_texto in etiquetas_personalizadas:
        etiqueta_texto = etiqueta_texto.strip().lower()
        if etiqueta_texto:
            etiqueta_existente = Etiqueta.query.filter_by(etiqueta=etiqueta_texto).first()
            if not etiqueta_existente:
                etiqueta_existente = Etiqueta(etiqueta=etiqueta_texto, confianza=1.0) 
                db.session.add(etiqueta_existente)
                db.session.flush()


            if etiqueta_existente not in meme.etiquetas:
                print(f"✅ Asociando etiqueta personalizada '{etiqueta_texto}' al meme {meme.id}")
                meme.etiquetas.append(etiqueta_existente)

    db.session.commit()

    # Obtener la configuración de Imagga antes de lanzar el hilo
    imagga_config = {
        "IMAGGA_API_KEY": current_app.config['IMAGGA_API_KEY'],
        "IMAGGA_API_SECRET": current_app.config['IMAGGA_API_SECRET'],
        "TAGS_ENDPOINT": current_app.config['TAGS_ENDPOINT']
    }

    print(f"🔥 Llamando a procesar_etiquetas_immaga() en un hilo separado...")

    # Ejecutar la obtención de etiquetas de Imagga en segundo plano
    threading.Thread(target=procesar_etiquetas_immaga, args=(meme.id, imagen_url, imagga_config)).start()

    return jsonify({"message": "Meme subido exitosamente. Las etiquetas serán procesadas en segundo plano.", "id": meme.id}), 201


#proceso de immaga
def procesar_etiquetas_immaga(meme_id, imagen_url, imagga_config):
    from app import create_app, db
    from sqlalchemy.exc import OperationalError
    app = create_app()

    with app.app_context():
        print(f"🚀 Ejecutando procesar_etiquetas_immaga() para el meme {meme_id}")

        api_key = imagga_config['IMAGGA_API_KEY']
        api_secret = imagga_config['IMAGGA_API_SECRET']
        endpoint = imagga_config['TAGS_ENDPOINT']

        response = requests.get(
            endpoint,
            auth=(api_key, api_secret),
            params={"image_url": imagen_url}
        )

        print(f"📡 Imagga Response Status: {response.status_code}")
        print(f"📡 Imagga Response: {response.text}")

        if response.status_code == 200:
            etiquetas_immaga = response.json().get("result", {}).get("tags", [])

            if not etiquetas_immaga:
                print("⚠️ No se encontraron etiquetas en la respuesta de Imagga.")
                return

            meme = Meme.query.get(meme_id)
            if meme:
                for tag in etiquetas_immaga:
                    etiqueta_texto = tag["tag"]["en"].strip().lower()
                    confianza = tag["confidence"]

                    try:
                        # Iniciar una nueva sesión para evitar Deadlock
                        with db.session.begin_nested():
                            etiqueta_existente = Etiqueta.query.filter_by(etiqueta=etiqueta_texto).first()
                            if not etiqueta_existente:
                                etiqueta_existente = Etiqueta(etiqueta=etiqueta_texto, confianza=confianza)
                                db.session.add(etiqueta_existente)
                                db.session.flush() 

                            if etiqueta_existente not in meme.etiquetas:
                                print(f"✅ Agregando etiqueta '{etiqueta_existente.etiqueta}' al meme {meme.id}")
                                meme.etiquetas.append(etiqueta_existente)

                        db.session.commit()  

                    except OperationalError as e:
                        db.session.rollback() 
                        print(f"❌ Error al insertar etiqueta '{etiqueta_texto}': {str(e)}")
                    
                print(f"✅ Etiquetas de Imagga agregadas correctamente al meme {meme.id}")
        else:
            print(f"❌ Error al obtener etiquetas de Imagga: {response.text}")


#eliminar meme
@main.route('/api/memes/<int:id>', methods=['DELETE'])
def eliminar_meme(id):
    meme = Meme.query.get(id)
    if not meme:
        return jsonify({"error": "Meme no encontrado"}), 404

    s3_client = get_s3_client()
    s3_client.delete_object(
        Bucket=current_app.config["AWS_S3_BUCKET"],
        Key=meme.ruta
    )

    meme.etiquetas.clear()
    db.session.delete(meme)
    db.session.commit()
    return jsonify({"message": "Meme eliminado exitosamente"}), 200

#buscar meme
@main.route('/api/memes/buscar', methods=['GET'])
def buscar_memes():
    query = request.args.get('query', '').lower().strip()
    if not query:
        memes = Meme.query.all() 
    else:
        memes = Meme.query.filter(
            (Meme.descripcion.ilike(f"%{query}%")) |
            (Meme.etiquetas.any(Etiqueta.etiqueta.ilike(f"%{query}%")))
        ).all()

    return jsonify([{
        "id": meme.id,
        "descripcion": meme.descripcion,
        "ruta": meme.ruta,
        "usuario": meme.usuario,
        "etiquetas": [etiqueta.etiqueta for etiqueta in meme.etiquetas]
    } for meme in memes])

