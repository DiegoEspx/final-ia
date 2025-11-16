import cv2
import numpy as np
from deepface import DeepFace
import os
from pathlib import Path
from datetime import datetime
from database import DatabaseManager  
from assistants import IAAssistant

class FaceAccessControlSystem:
    """Sistema completo de control de acceso facial"""
    def __init__(self, db_path='access_control.db', known_faces_dir='known_faces'):
        
        """Inicializa el sistema."""
        self.known_faces_dir = known_faces_dir
        self.threshold = 0.6  
        self.ai = None
        # Inicializar el manejador de base de datos
        self.db_manager = DatabaseManager(db_path=db_path)
        
        # Crear directorio de caras conocidas
        Path(known_faces_dir).mkdir(exist_ok=True)
        
        # Detector de rostros (Haar Cascade como respaldo)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        print("Lógica del sistema cargada correctamente")
    
    def get_access_statistics(self):
        return self.db_manager.get_access_statistics()
        

    def get_all_users(self):
        return self.db_manager.get_all_users_info()

    def log_access(self, user_id, user_name, granted, confidence):
        self.db_manager.log_access(user_id, user_name, granted, confidence)

    def ask_ai(self, question):
        """Pregunta al asistente IA (Inicialización perezosa)"""
        try:
            if self.ai is None:
                self.ai = IAAssistant() 
                
            return self.ai.chat(question)
            
        except Exception as e:
            self.ai = None 
            return f"Error al consultar IA: {str(e)}"

    # === Lógica de Registro ===
    def register_user(self, name, email=None, photo_source='camera'):
        """Registra un nuevo usuario en el sistema."""
        print(f"\nRegistrando usuario: {name}")
        
        # 1. Verificar si el usuario ya existe
        if self.db_manager.get_user_by_name(name):
            print(f"El usuario '{name}' ya está registrado")
            return False
        
        # 2. Capturar o cargar foto
        if photo_source == 'camera':
            print("Abre la cámara y presiona ESPACIO para capturar, ESC para cancelar")
            photo_path = self._capture_photo(name)
            if not photo_path:
                print("Captura cancelada")
                return False
        else:
            photo_path = photo_source
            if not os.path.exists(photo_path):
                print(f"No se encuentra la foto: {photo_path}")
                return False
        
        # 3. Verificar que la foto contiene un rostro detectable (usando DeepFace)
        try:
            DeepFace.represent(photo_path, model_name='Facenet', enforce_detection=True)
            print("Rostro detectado correctamente")
        except Exception as e:
            print(f"No se pudo detectar un rostro en la imagen: {e}")
            return False
        
        # 4. Guardar en base de datos
        user_id = self.db_manager.add_user(name, email, photo_path)
        
        print(f"Usuario '{name}' registrado exitosamente (ID: {user_id})")
        return True

    # --- Métodos Auxiliares ---
    def _capture_photo(self, name):
        """Captura una foto desde la cámara (igual que antes)"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("No se pudo acceder a la cámara")
            return None
        
        print("Cámara activa. Presiona ESPACIO para capturar, ESC para cancelar")
        
        captured = False
        frame_to_save = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detectar rostros para feedback visual
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Dibujar rectángulos alrededor de rostros
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Rostro detectado", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Mostrar instrucciones
            cv2.putText(frame, "ESPACIO: Capturar | ESC: Cancelar", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Registrar Usuario', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # ESPACIO
                if len(faces) > 0:
                    frame_to_save = frame.copy()
                    captured = True
                    print("Foto capturada!")
                    break
                else:
                    print("No se detectó ningún rostro. Intenta de nuevo.")
            elif key == 27:  
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if captured and frame_to_save is not None:
            filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            photo_path = os.path.join(self.known_faces_dir, filename)
            cv2.imwrite(photo_path, frame_to_save)
            return photo_path
        
        return None

    # === Lógica de Reconocimiento y Control ===
    def recognize_face(self, image_path_or_array):
        """Reconoce un rostro comparándolo con todos los usuarios registrados."""
        # Obtener todos los usuarios registrados
        users = self.db_manager.get_all_users_for_recognition()
        
        if len(users) == 0:
            return {
                'user_id': None, 'name': 'Desconocido', 'distance': 1.0, 
                'verified': False, 'message': 'No hay usuarios registrados'
            }
        
        temp_path = None
        if isinstance(image_path_or_array, np.ndarray):
            temp_path = Path(os.path.dirname(__file__)).parent / 'temp_frame.jpg'
            cv2.imwrite(str(temp_path), image_path_or_array)
            image_path = str(temp_path)
        else:
            image_path = image_path_or_array
        
        best_match = None
        min_distance = float('inf')
        
        # Comparar con cada usuario registrado usando DeepFace
        for user_id, name, photo_path in users:
            try:
                result = DeepFace.verify(
                    img1_path=image_path,
                    img2_path=photo_path,
                    model_name='Facenet',  
                    distance_metric='cosine',
                    enforce_detection=False
                )
                
                distance = result['distance']
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = {
                        'user_id': user_id, 'name': name, 'distance': distance, 
                        'verified': result['verified']
                    }
            
            except Exception:
                continue
        
        # Limpiar archivo temporal
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        if best_match and best_match['verified']:
            return best_match
        else:
            return {
                'user_id': None,
                'name': 'Desconocido',
                'distance': min_distance if min_distance != float('inf') else 1.0,
                'verified': False,
                'message': 'No coincide con ningún usuario registrado'
            }

    def run_access_control(self):
        """Ejecuta el sistema de control de acceso en tiempo real (igual que antes)."""
        print("\nIniciando sistema de control de acceso...")
        print("Presiona 'q' para salir")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("No se pudo acceder a la cámara")
            return
        
        frame_count = 0
        check_interval = 30 
        last_result = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Detectar rostros con Haar Cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Solo procesar con DeepFace cada N frames para mejor rendimiento
            if frame_count % check_interval == 0 and len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                last_result = self.recognize_face(face_roi)
                
                if last_result and last_result['verified']:
                    confidence = 1 - last_result['distance']
                    self.log_access(last_result['user_id'], last_result['name'], True, confidence)
                    print(f"Acceso concedido: {last_result['name']} (confianza: {confidence:.2f})")
                else:
                    self.log_access(None, 'Desconocido', False, 0)
                    print(f"Acceso denegado: Usuario no reconocido")
            
            # Dibujar rectángulos y etiquetas
            for (x, y, w, h) in faces:
                current_match = last_result 
                
                if current_match and current_match['verified']:
                    color = (0, 255, 0)  # Verde
                    label = f"OK: {current_match['name']}"
                else:
                    color = (0, 0, 255)  # Rojo
                    label = "X: Desconocido"
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, label, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Mostrar información
            cv2.putText(frame, "Control de Acceso Activo", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Presiona 'q' para salir", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Control de Acceso Facial', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nDeteniendo sistema...")
                break
        
        cap.release()
        cv2.waitKey(1) 
        cv2.destroyAllWindows()
        print("Sistema detenido")