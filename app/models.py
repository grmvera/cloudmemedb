from app import db

# Tabla intermedia para la relación muchos a muchos
meme_etiqueta = db.Table(
    'meme_etiqueta',
    db.Column('meme_id', db.Integer, db.ForeignKey('memes.id'), primary_key=True),
    db.Column('etiqueta_id', db.Integer, db.ForeignKey('etiquetas.id'), primary_key=True)
)

# tabla meme
class Meme(db.Model):
    __tablename__ = 'memes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    descripcion = db.Column(db.String(255), nullable=False)
    ruta = db.Column(db.String(255), nullable=False)
    usuario = db.Column(db.String(50), nullable=False) 
    cargada = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    etiquetas = db.relationship('Etiqueta', secondary=meme_etiqueta, backref='memes')

# tabla etiqueta
class Etiqueta(db.Model):
    __tablename__ = 'etiquetas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    etiqueta = db.Column(db.String(50), nullable=False, unique=True)  
    confianza = db.Column(db.Float, default=1.0)  
