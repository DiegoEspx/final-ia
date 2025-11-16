import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from dotenv import load_dotenv
load_dotenv()

try:
    from system_core import FaceAccessControlSystem
except ImportError as e:
    print(f"Error al importar el módulo central: {e}")
    print("Asegúrate de que 'system_core.py' existe en la carpeta 'src'.")
    sys.exit(1)


# ==================== PROGRAMA PRINCIPAL ====================

def main():
    """Función principal con menú interactivo"""
    # Inicializar sistema
    try:
        system = FaceAccessControlSystem()
    except Exception as e:
        print(f"Error al inicializar el sistema: {e}")
        print("Asegúrate de tener instaladas las librerías necesarias (opencv-python, deepface, numpy).")
        return

    print("\n" + "="*60)
    print("     SISTEMA DE CONTROL DE ACCESO FACIAL")
    print("           Con Reconocimiento IA")
    print("="*60)

    while True:
        print("\n" + "-"*60)
        print("MENÚ PRINCIPAL:")
        print("-"*60)
        print("1. Registrar nuevo usuario")
        print("2. Iniciar control de acceso en tiempo real")
        print("3. Ver estadísticas del sistema")
        print("4. Ver usuarios registrados")
        print("5. Consultar asistente IA")
        print("6. Salir")
        print("-"*60)

        choice = input("\n> Selecciona una opción (1-6): ").strip()

        if choice == '1':
            print("\n" + "="*60)
            print("REGISTRO DE NUEVO USUARIO")
            print("="*60)
            name = input("> Nombre completo del usuario: ").strip()
            if not name:
                print("El nombre no puede estar vacío")
                continue

            email = input("> Email (opcional, Enter para omitir): ").strip() or None

            print("\nOpciones de foto:")
            print("1. Capturar desde cámara (recomendado)")
            print("2. Usar foto existente")
            photo_option = input("> Selecciona (1-2): ").strip()

            if photo_option == '1':
                system.register_user(name, email, photo_source='camera')
            elif photo_option == '2':
                photo_path = input("> Ruta de la foto: ").strip()
                system.register_user(name, email, photo_source=photo_path)
            else:
                print("Opción inválida")

        elif choice == '2':
            print("\n" + "="*60)
            print("INICIANDO CONTROL DE ACCESO")
            print("="*60)
            print("El sistema verificará rostros cada 1 segundo aprox.")
            print("Presiona 'q' para detener el sistema")
            input("\n> Presiona Enter para comenzar...")
            system.run_access_control()

        elif choice == '3':
            print("\n" + "="*60)
            print("ESTADÍSTICAS DEL SISTEMA")
            print("="*60)
            stats = system.get_access_statistics()

            print(f"\nResumen General:")
            print(f"  • Usuarios registrados: {stats['total_users']}")
            print(f"  • Total de intentos de acceso: {stats['total_attempts']}")
            print(f"  • Accesos concedidos: {stats['granted']} ✅")
            print(f"  • Accesos denegados: {stats['denied']} ❌")

            if stats['total_attempts'] > 0:
                success_rate = (stats['granted'] / stats['total_attempts']) * 100
                print(f"  • Tasa de éxito: {success_rate:.1f}%")

            if stats['recent_logs']:
                print(f"\nÚltimos 5 accesos:")
                for log in stats['recent_logs']:
                    user, granted, conf, timestamp = log
                    status = "✅ CONCEDIDO" if granted else "❌ DENEGADO"
                    print(f"  • {timestamp} | {user:20s} | {status} | Conf: {conf:.2f}")

        elif choice == '4':
            print("\n" + "="*60)
            print("USUARIOS REGISTRADOS")
            print("="*60)
            users = system.get_all_users()

            if not users:
                print("\nNo hay usuarios registrados aún")
            else:
                print(f"\nTotal: {len(users)} usuario(s)\n")
                for user_id, name, email, reg_date in users:
                    email_display = email if email else "N/A"
                    print(f"  ID {user_id}: {name:30s} | Email: {email_display:30s} | Registrado: {reg_date}")

        elif choice == '5':
            print("\n" + "="*60)
            print("ASISTENTE INTELIGENTE (GROQ AI)")
            print("="*60)

            while True:
                question = input("\n> Escribe tu pregunta (o 'salir' para volver): ")

                if question.lower() == "salir":
                    break

                print("\n⏳Procesando la respuesta de la IA...\n")
                answer = system.ask_ai(question)

                print("IA:", answer)
                
        elif choice == '6':
            print("\n" + "="*60)
            print("Gracias por usar el sistema")
            print("Desarrollado para proyecto de IA")
            print("="*60)
            break

        else:
            print("\nOpción inválida. Por favor selecciona 1-6")


if __name__ == "__main__":
    main()