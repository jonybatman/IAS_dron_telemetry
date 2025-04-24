try:
    import cv2
    CV2_AVAILABLE = True
except ModuleNotFoundError:
    CV2_AVAILABLE = False
    print("No se pudo importar cv2: OpenCV no está instalado.")

import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError  # Añadido UnidentifiedImageError
import numpy as np
import os
import sys

# Diccionario para controlar mensajes de error (solo se imprimen una vez)
error_messages = {'frame': False, 'image': False}

def initialize_video_stream(device_index=0):
    """Inicializa la captura de video desde una capturadora HDMI-USB en 720p."""
    global error_messages
    if not CV2_AVAILABLE:
        if not error_messages['frame']:
            print("No se pudo leer el fotograma: cv2 no disponible")
            error_messages['frame'] = True
        return None

    try:
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            raise Exception("No se pudo abrir el dispositivo de video")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        print("Capturadora inicializada correctamente")
        return cap
    except Exception as e:
        if not error_messages['frame']:
            print(f"Error al inicializar video: {e}")
            print("No se pudo leer el fotograma")
            error_messages['frame'] = True
        return None

def update_video_frame(cap, label, flight_data, telemetry_data, signal_strength):
    """
    Actualiza el fotograma de video con datos superpuestos en 720p.
    Usa no_signal_image.jpg si no hay video; no muestra nada si la imagen no está disponible.
    """
    global error_messages
    try:
        width, height = 1280, 720
        frame_rgb = None

        # Intentar leer video
        if CV2_AVAILABLE and cap is not None and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.resize(frame_rgb, (width, height))
                print("Fotograma de video cargado correctamente")  # Depuración
            else:
                frame_rgb = load_default_image(width, height)
        else:
            frame_rgb = load_default_image(width, height)

        # Si no hay imagen válida, no actualizar el label
        if frame_rgb is None:
            if not error_messages['frame']:
                print("No se pudo leer el fotograma: ninguna imagen disponible")
                error_messages['frame'] = True
            return False

        # Superponer datos de vuelo y telemetría
        if CV2_AVAILABLE:
            # Validar datos de vuelo
            altitude = flight_data.get('altitude', 0) if isinstance(flight_data.get('altitude'), (int, float)) else 0
            distance = flight_data.get('distance', 0) if isinstance(flight_data.get('distance'), (int, float)) else 0
            latitude = flight_data.get('latitude', 0) if isinstance(flight_data.get('latitude'), (int, float)) else 0
            longitude = flight_data.get('longitude', 0) if isinstance(flight_data.get('longitude'), (int, float)) else 0
            battery_percent = flight_data.get('battery_percent', 0) if isinstance(flight_data.get('battery_percent'), (int, float)) else 0
            speed = flight_data.get('speed', 0) if isinstance(flight_data.get('speed'), (int, float)) else 0

            # Validar datos de telemetría
            gps_data = telemetry_data.get('gps_data', {'latitude': 0, 'longitude': 0, 'gps_altitude': 0, 'valid': False})
            baro_data = telemetry_data.get('baro_data', {'baro_altitude': 0, 'valid': False})
            battery_data = telemetry_data.get('battery_data', {'voltage': 0, 'valid': False})
            ir_data = telemetry_data.get('ir_data', {'ir_status': 0, 'valid': False})

            gps_latitude = gps_data.get('latitude', 0) if isinstance(gps_data.get('latitude'), (int, float)) else 0
            gps_longitude = gps_data.get('longitude', 0) if isinstance(gps_data.get('longitude'), (int, float)) else 0
            gps_altitude = gps_data.get('gps_altitude', 0) if isinstance(gps_data.get('gps_altitude'), (int, float)) else 0
            baro_altitude = baro_data.get('baro_altitude', 0) if isinstance(baro_data.get('baro_altitude'), (int, float)) else 0
            voltage = battery_data.get('voltage', 0) if isinstance(battery_data.get('voltage'), (int, float)) else 0
            ir_status = "ON" if ir_data.get('valid', False) and ir_data.get('ir_status', 0) == 1 else "OFF"

            texts = [
                f"Latitud: {gps_latitude:.6f}",
                f"Longitud: {gps_longitude:.6f}",
                f"Altitud GPS: {gps_altitude:.1f} m",
                f"Altitud Baro: {baro_altitude:.1f} m",
                f"Voltaje: {voltage:.1f} V",
                f"LEDs IR: {ir_status}",
                f"Altura: {altitude:.1f} m",
                f"Distancia: {distance:.1f} m",
                f"Batería: {battery_percent:.0f}%",
                f"Velocidad: {speed:.1f} m/s"
            ]
            y_pos = 35
            for text in texts:
                cv2.putText(frame_rgb, text, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(frame_rgb, text, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
                y_pos += 35

            # Barras de señal
            signal_strength = min(max(signal_strength, 0), 4)
            for i in range(4):
                color = (255, 255, 255) if i < signal_strength else (100, 100, 100)
                border_color = (0, 0, 0)
                x = width - 100 + i * 24
                y_top = 50 + (3 - i) * 40
                y_bottom = y_top + 40
                cv2.rectangle(frame_rgb, (x, y_top), (x + 20, y_bottom), border_color, -1)
                cv2.rectangle(frame_rgb, (x + 1, y_top + 1), (x + 19, y_bottom - 1), color, -1)

        # Convertir a formato Tkinter
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        print(f"PhotoImage creado: {imgtk.width()}x{imgtk.height()}")  # Depuración
        label.imgtk = imgtk
        label.configure(image=imgtk)
        return True
    except Exception as e:
        print(f"Error al actualizar video: {e}")
        return False

def load_default_image(width, height):
    """Carga no_signal_image.jpg desde el directorio del script o devuelve None si falla."""
    global error_messages
    image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no_signal_image.jpg")
    if not os.path.exists(image_path):
        if not error_messages['image']:
            print(f"No se encontró {image_path}")
            error_messages['image'] = True
        return None
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        print(f"Imagen {image_path} cargada correctamente")
        return np.array(img)
    except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
        if not error_messages['image']:
            print(f"Error al cargar {image_path}: {e}")
            error_messages['image'] = True
        return None

def release_video_stream(cap):
    """Libera el objeto de captura de video."""
    if CV2_AVAILABLE and cap is not None:
        cap.release()