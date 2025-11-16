import sqlite3
from datetime import datetime

class DatabaseManager:
    """Gestiona la conexión y las operaciones de la base de datos SQLite."""
    
    def __init__(self, db_path='access_control.db'):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        """Retorna una conexión a la base de datos."""
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        """Crea las tablas necesarias en la base de datos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                photo_path TEXT NOT NULL,
                registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de logs de acceso
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_granted BOOLEAN,
                confidence REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Base de datos inicializada")
        
    # --- Operaciones de Usuario ---

    def get_user_by_name(self, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, photo_path FROM users WHERE name = ?', (name,))
        user = cursor.fetchone()
        conn.close()
        return user

    def get_all_users_for_recognition(self):
        """Obtiene ID, nombre y ruta de foto para reconocimiento."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, photo_path FROM users')
        users = cursor.fetchall()
        conn.close()
        return users

    def get_all_users_info(self):
        """Obtiene todos los detalles de los usuarios."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, registered_date FROM users ORDER BY name')
        users = cursor.fetchall()
        conn.close()
        return users

    def add_user(self, name, email, photo_path):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, photo_path) VALUES (?, ?, ?)',
            (name, email, photo_path)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id

    # --- Operaciones de Logs ---
    
    def log_access(self, user_id, user_name, granted, confidence):
        """Registra un intento de acceso."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO access_logs 
               (user_id, user_name, access_granted, confidence) 
               VALUES (?, ?, ?, ?)''',
            (user_id, user_name, granted, confidence)
        )
        conn.commit()
        conn.close()

    def get_access_statistics(self):
        """Obtiene estadísticas generales y logs recientes."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total de intentos
        cursor.execute('SELECT COUNT(*) FROM access_logs')
        total_attempts = cursor.fetchone()[0]
        
        # Accesos concedidos
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE access_granted = 1')
        granted = cursor.fetchone()[0]
        
        # Accesos denegados
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE access_granted = 0')
        denied = cursor.fetchone()[0]
        
        # Usuarios registrados
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Últimos 5 accesos
        cursor.execute('''
            SELECT user_name, access_granted, confidence, timestamp 
            FROM access_logs 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        recent_logs = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_attempts': total_attempts,
            'granted': granted,
            'denied': denied,
            'total_users': total_users,
            'recent_logs': recent_logs
        }