# MemeDB - WebApp para Gestión de Memes con AWS S3, RDS y Imagga
Tabata Mendoza y Geovanny Vera

Este proyecto es una aplicación web que permite a los usuarios subir imágenes de memes, asignarles etiquetas personalizadas y obtener etiquetas generadas automáticamente con la API de Imagga. Los memes se almacenan en **AWS S3**, la base de datos se gestiona con **AWS RDS (MySQL)** y la aplicación está Dockerizada.

---

## 🚀 **Características Principales**
✔ Subir imágenes de memes a **AWS S3**  
✔ Generar etiquetas con **Imagga API**  
✔ Asignar etiquetas personalizadas a los memes  
✔ Buscar memes por etiquetas y descripción  
✔ Listar y eliminar memes  
✔ Desplegado en **Docker** con contenedores de **Flask y MySQL**  

---

## 🛠 **Tecnologías Usadas**
- **Flask** (Python)
- **MySQL** (AWS RDS)
- **Amazon S3** (Almacenamiento de imágenes)
- **Imagga API** (Reconocimiento de imágenes)
- **Docker & Docker Compose**
- **SQLAlchemy** (ORM para Flask)
- **Flask-Migrate** (Manejo de migraciones)
- **Flask-CORS** (Manejo de permisos CORS)