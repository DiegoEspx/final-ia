Sistema de Control de Acceso Facial con Python + DeepFace + Groq
Este proyecto implementa un Sistema de Control de Acceso basado en Reconocimiento Facial utilizando:

- Python 3.11.0 
- OpenCV
- DeepFace (Facenet)
- SQLite
- Groq LLM API (asistente IA opcional dentro del sistema)

Permite registrar usuarios, almacenar rostros, reconocer personas en tiempo real mediante cámara, y llevar un registro de accesos.

1. Requisitos Previos
- Python 3.11.0

Este proyecto fue probado y funciona correctamente en Python 3.11.0.

Puedes verificar tu versión:
python --version
Si no tienes Python 3.11:

Windows: instala desde https://www.python.org/downloads/release/python-3110/
Linux/Mac: pyenv recomendado.

2. Crear y activar entorno virtual
Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

Linux / MacOS
python3 -m venv venv
source venv/bin/activate


Verifica que el entorno está activo:
- Debe aparecer (venv) al inicio de la terminal.

3. Instalar las dependencias

Con el entorno ya activado:
pip install -r requirements.txt

Si aún no tienes el archivo requirements.txt, usa este contenido:
opencv-python
deepface
numpy
sqlite-utils
groq
pillow

(O el que ya trae tu repo.)

4. Configurar la clave GROQ (opcional)

El módulo IA usa Groq.
Debes configurar tu variable de entorno GROQ_API_KEY.

Windows (PowerShell):
setx GROQ_API_KEY "TU_API_KEY_AQUI"

Linux/Mac:
export GROQ_API_KEY="TU_API_KEY_AQUI"

Verifica:
echo $GROQ_API_KEY

📁 5. Estructura de Carpetas del Proyecto
/project
│── system_core.py
│── assistants.py
│── database.py
│── requirements.txt
│── README.md
│── known_faces/         ← se crea automáticamente
│── access_control.db    ← se crea automáticamente

6. Cómo iniciar el sistema

Ejecuta el archivo principal :
python main.py


El menú te permitirá:
- Registrar usuario
- Consultar accesos
- Ejecutar reconocimiento en tiempo real
- Hacer preguntas al asistente IA (Groq)

7. Registrar un usuario

En el menú:
1 - Registrar usuario

El sistema:
- Abrirá la cámara
- Dibujará un recuadro verde cuando detecte un rostro
- Presiona ESPACIO para capturar
- Se guardará la imagen en known_faces/
- Se insertará en la base de datos

8. Ejecutar reconocimiento en tiempo real
En el menú:
2 - Ejecutar control de acceso
El sistema:
- Detecta rostros con Haar Cascade
- Cada cierto intervalo compara con los usuarios registrados
- Usa DeepFace + Facenet
- Si reconoce alguien → acceso permitido
- Si no → acceso denegado

9. Base de datos
Todo se almacena en:
- access_control.db
- Tablas:
- users
- access_logs

Puedes ver la info con:
sqlite3 access_control.db

10. Uso del Asistente IA (Groq)
En el menú:
5 - Preguntar a la IA

La clase IAAssistant usa:
model="llama-3.1-70b-versatile"
Y responde preguntas técnicas sobre el proyecto.