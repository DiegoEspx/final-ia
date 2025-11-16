from groq import Groq
import os
import sqlite3
from dotenv import load_dotenv
load_dotenv()

class IAAssistant:
    """Asistente IA para consultas sobre el sistema de control de acceso"""
    
    def __init__(self, db_path='access_control.db'):
        """
        Inicializa el asistente con Groq
        Args:
            db_path: Ruta a la base de datos del sistema
        """
        self.db_path = db_path
        
        # Obtener API key de Groq desde variables de entorno
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No existe GROQ_API_KEY en el entorno. Configúrala con: $env:GROQ_API_KEY='tu-key'")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile" 
        print(f"Asistente IA inicializado con modelo: {self.model}")
    
    def get_context_from_db(self):
        """
        Extrae información relevante de la base de datos para dar contexto a la IA
        Returns:
            String con información del sistema
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            context_parts = []
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            context_parts.append(f"Usuarios registrados: {user_count}")
            
            # 2. Total de intentos de acceso
            cursor.execute('SELECT COUNT(*) FROM access_logs')
            log_count = cursor.fetchone()[0]
            context_parts.append(f"Total de intentos de acceso: {log_count}")
            
            # 3. Accesos de hoy
            cursor.execute('''
                SELECT COUNT(*), SUM(access_granted) 
                FROM access_logs 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            result = cursor.fetchone()
            if result[0]:
                today_total = result[0]
                today_granted = result[1] or 0
                today_denied = today_total - today_granted
                context_parts.append(
                    f"Accesos hoy: {today_total} intentos "
                    f"({today_granted} concedidos, {today_denied} ; denegados)"
                )
            
            # 4. Últimos 5 accesos
            cursor.execute('''
                SELECT user_name, access_granted, confidence, timestamp 
                FROM access_logs 
                ORDER BY timestamp DESC 
                LIMIT 5
            ''')
            recent_logs = cursor.fetchall()
            if recent_logs:
                context_parts.append("\n📋 Últimos 5 accesos:")
                for user, granted, conf, ts in recent_logs:
                    status = "✅" if granted else "❌"
                    context_parts.append(f"  {status} {ts}: {user} (confianza: {conf:.2f})")
            
            # 5. Lista de usuarios (nombres)
            cursor.execute('SELECT name FROM users ORDER BY name')
            users = cursor.fetchall()
            if users:
                user_names = ", ".join([u[0] for u in users])
                context_parts.append(f"\n👤 Usuarios: {user_names}")
            
            conn.close()
            
            return "\n".join(context_parts)
        
        except Exception as e:
            return f"Error al obtener datos: {str(e)}"
    
    def chat(self, message: str):
        """
        Procesa un mensaje del usuario y genera respuesta usando Groq
        Args:
            message: Pregunta o mensaje del usuario
        Returns:
            Respuesta del asistente IA
        """
        try:
            db_context = self.get_context_from_db()
            system_prompt = f"""Eres un asistente inteligente para un sistema de control de acceso con reconocimiento facial.

INFORMACIÓN ACTUAL DEL SISTEMA:
{db_context}

TU FUNCIÓN:
- Responder preguntas sobre el sistema de forma clara y precisa
- Usar los datos proporcionados arriba para dar respuestas exactas
- Si no tienes información suficiente, indícalo claramente
- Ser amigable, profesional y útil
- Usar emojis apropiados para hacer las respuestas más amigables

SOBRE EL SISTEMA:
- Usa reconocimiento facial con IA (DeepFace con modelo FaceNet)
- Detecta rostros en tiempo real con OpenCV (Haar Cascades)
- Base de datos SQLite para gestión de usuarios y logs de acceso
- Puede registrar nuevos usuarios mediante cámara web
- Control de acceso en tiempo real con feedback visual (verde=permitido, rojo=denegado)
- Registra todos los intentos con timestamp, usuario y nivel de confianza

Responde de manera concisa (máximo 3-4 párrafos) a menos que se pida más detalle."""
            
            response = self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7, 
                max_tokens=1024,  
                top_p=1
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = str(e)
            
            if "model_decommissioned" in error_msg:
                return "El modelo está descontinuado. Por favor actualiza el código con un modelo compatible."
            elif "api_key" in error_msg.lower():
                return "Error de autenticación. Verifica tu GROQ_API_KEY."
            elif "rate_limit" in error_msg.lower():
                return "Límite de solicitudes alcanzado. Espera un momento e intenta de nuevo."
            else:
                return f"Error al consultar IA: {error_msg}"
