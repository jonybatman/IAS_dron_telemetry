import serial
import tkinter as tk
from tkinter import ttk
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import pygame
import gps_subsystem
import barometer_subsystem
import battery_subsystem
import ir_subsystem
import video_subsystem
import rth_subsystem
import flystandard_subsystem
import drivingaid_subsystem
import electronicwardefense_subsystem
from threading import Thread
import time
from math import radians, sin, cos, sqrt, atan2

# Configuración inicial
ser = None
try:
    ser = serial.Serial('COM4', 57600, timeout=3)
except Exception as e:
    print(f"Error al abrir puerto serial: {e}")
    print("Ejecutando en modo simulado sin conexión serial")

pygame.init()
pygame.joystick.init()
joystick = None
try:
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print("Joystick Xbox 360 Detectado")
    else:
        print("Joystick Xbox 360 No Detectado")
except Exception as e:
    print(f"Error al inicializar Joystick Xbox 360: {e}")
    print("Joystick Xbox 360 No Detectado")

# Inicializar subsistemas
rth_state = rth_subsystem.initialize_rth()
flystandard_state = flystandard_subsystem.initialize_flystandard()
drivingaid_state = drivingaid_subsystem.initialize_drivingaid()
ewd_state = electronicwardefense_subsystem.initialize_electronicwardefense()

# Estado inicial
initial_position = None
last_position = None
last_time = time.time()
flight_data = {
    'altitude': 0,
    'distance': 0,
    'latitude': 0,
    'longitude': 0,
    'battery_percent': 0,
    'speed': 0
}

# Almacenamiento de datos
data_log = pd.DataFrame(columns=["Timestamp", "Latitude", "Longitude", "GPS_Altitude",
                                 "Baro_Altitude", "Battery_Voltage", "IR_Status"])
plot_data = {
    'times': [],
    'latitudes': [],
    'longitudes': [],
    'gps_altitudes': [],
    'baro_altitudes': [],
    'voltages': []
}
log_buffer = []

# Inicializar figura de Plotly
fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=("Mapa de Ubicación", "Altitud", "Voltaje de Batería"),
    specs=[[{"type": "scattergeo"}], [{"type": "scatter"}], [{"type": "scatter"}]]
)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula la distancia en metros entre dos puntos GPS usando la fórmula de Haversine."""
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def voltage_to_percent(voltage):
    """Convierte el voltaje de batería (LiPo 11.1V) a porcentaje."""
    min_voltage = 9.0
    max_voltage = 12.6
    return max(0, min(100, ((voltage - min_voltage) / (max_voltage - min_voltage)) * 100))

def calculate_signal_strength(last_signal_time):
    """Calcula el nivel de señal (0-4 barras) según el tiempo desde la última recepción."""
    elapsed = time.time() - last_signal_time
    thresholds = [(0.5, 4), (1.0, 3), (1.5, 2), (2.0, 1)]
    for threshold, bars in thresholds:
        if elapsed < threshold:
            return bars
    return 0

def set_frequency_pc(frequency):
    """Cambia la frecuencia del RFD900x en la PC."""
    if ser is None:
        return
    try:
        ser.write(f"ATF={frequency}\r\n".encode('utf-8'))
        time.sleep(0.1)
    except Exception as e:
        print(f"Error al cambiar frecuencia: {e}")

# Ventana principal
root = tk.Tk()
root.title("Tablero de Telemetría y Video del Dron")
root.geometry("1400x800")
print("GUI inicializada correctamente")  # Depuración

# Panel de video
video_frame = ttk.Frame(root)
video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
video_label = ttk.Label(video_frame)
video_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

# Inicializar captura de video
video_cap = video_subsystem.initialize_video_stream(device_index=0)

# Última marca de tiempo para cálculo PID
last_time_pid = time.time()

def read_serial_and_control():
    """Procesa datos seriales, genera comandos y actualiza la GUI."""
    global rth_state, flystandard_state, drivingaid_state, ewd_state, last_time_pid
    global initial_position, last_position, last_time, flight_data, data_log, log_buffer
    update_count = 0  # Contador para depuración

    while True:
        try:
            signal_received = False
            gps_data = {'latitude': 0, 'longitude': 0, 'gps_altitude': 0, 'valid': False}
            baro_data = {'baro_altitude': 0, 'valid': False}
            battery_data = {'voltage': 0, 'valid': False}
            ir_data = {'ir_status': 0, 'valid': False}
            mpu_data = {'pitch': 0, 'roll': 0, 'yaw': 0, 'valid': False}
            now = datetime.datetime.now()

            if ser is not None:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    signal_received = True
                    data = line.split(',')
                    if len(data) == 9:
                        gps_data = gps_subsystem.process_gps_data(data)
                        baro_data = barometer_subsystem.process_barometer_data(data)
                        battery_data = battery_subsystem.process_battery_data(data)
                        ir_data = ir_subsystem.process_ir_data(data)
                        try:
                            mpu_data = {
                                'pitch': float(data[6]),
                                'roll': float(data[7]),
                                'yaw': float(data[8]),
                                'valid': True
                            }
                        except (ValueError, IndexError):
                            mpu_data = {'pitch': 0, 'roll': 0, 'yaw': 0, 'valid': False}

                        if gps_data['valid'] and baro_data['valid'] and battery_data['valid']:
                            flight_data['altitude'] = baro_data['baro_altitude']
                            flight_data['latitude'] = gps_data['latitude']
                            flight_data['longitude'] = gps_data['longitude']
                            flight_data['battery_percent'] = voltage_to_percent(battery_data['voltage'])

                            if initial_position is None:
                                initial_position = (gps_data['latitude'], gps_data['longitude'])

                            flight_data['distance'] = haversine_distance(
                                gps_data['latitude'], gps_data['longitude'],
                                initial_position[0], initial_position[1]
                            )

                            if last_position is not None:
                                distance = haversine_distance(
                                    gps_data['latitude'], gps_data['longitude'],
                                    last_position[0], last_position[1]
                                )
                                time_diff = (now - last_time).total_seconds()
                                if time_diff > 0:
                                    flight_data['speed'] = distance / time_diff
                            last_position = (gps_data['latitude'], gps_data['longitude'])
                            last_time = now

            # Registrar datos
            log_buffer.append({
                "Timestamp": now,
                "Latitude": gps_data['latitude'] if gps_data['valid'] else None,
                "Longitude": gps_data['longitude'] if gps_data['valid'] else None,
                "GPS_Altitude": gps_data['gps_altitude'] if gps_data['valid'] else None,
                "Baro_Altitude": baro_data['baro_altitude'] if baro_data['valid'] else None,
                "Battery_Voltage": battery_data['voltage'] if battery_data['valid'] else None,
                "IR_Status": "ON" if ir_data['valid'] and ir_data['ir_status'] == 1 else "OFF"
            })

            # Actualizar datos para gráficos
            plot_data['times'].append(now)
            plot_data['latitudes'].append(gps_data['latitude'])
            plot_data['longitudes'].append(gps_data['longitude'])
            plot_data['gps_altitudes'].append(gps_data['gps_altitude'] if gps_data['valid'] else None)
            plot_data['baro_altitudes'].append(baro_data['baro_altitude'] if baro_data['valid'] else None)
            plot_data['voltages'].append(battery_data['voltage'])

            # Limitar a 100 puntos
            if len(plot_data['times']) > 100:
                for key in plot_data:
                    plot_data[key].pop(0)

            # Concatenar buffer cada 10 entradas
            if len(log_buffer) >= 10:
                global data_log
                data_log = pd.concat([data_log, pd.DataFrame(log_buffer)], ignore_index=True)
                log_buffer.clear()
                data_log.to_csv("drone_data.csv", index=False)

            # Procesar ElectronicWarDefense
            ewd_state = electronicwardefense_subsystem.process_electronicwardefense(
                ewd_state, signal_received, set_frequency_pc
            )

            # Procesar comandos
            commands = {'pitch': 500, 'roll': 500, 'yaw': 500, 'throttle': 0}
            button_a = False
            button_b = False
            if joystick is not None:
                pygame.event.pump()
                pitch = joystick.get_axis(1)
                roll = joystick.get_axis(0)
                yaw = joystick.get_axis(3)
                throttle = joystick.get_axis(2)
                button_a = joystick.get_button(0)
                button_b = joystick.get_button(1)
                commands = {
                    'pitch': int((pitch + 1) * 500),
                    'roll': int((roll + 1) * 500),
                    'yaw': int((yaw + 1) * 500),
                    'throttle': int((throttle + 1) * 500)
                }

                # Procesar FlyStandard
                flystandard_commands, flystandard_state = flystandard_subsystem.process_flystandard(
                    flystandard_state, baro_data, button_a
                )
                if flystandard_state['flystandard_active']:
                    commands['throttle'] = flystandard_commands['throttle']

            # Procesar DrivingAid
            current_time = time.time()
            dt = current_time - last_time_pid if last_time_pid is not None else 0.1
            last_time_pid = current_time
            drivingaid_commands, drivingaid_state = drivingaid_subsystem.process_drivingaid(
                drivingaid_state, mpu_data, dt, button_b
            )
            if drivingaid_state['drivingaid_active']:
                commands['pitch'] = max(400, min(600, commands['pitch'] + drivingaid_commands['pitch']))
                commands['roll'] = max(400, min(600, commands['roll'] + drivingaid_commands['roll']))
                commands['yaw'] = max(400, min(600, commands['yaw'] + drivingaid_commands['yaw']))

            # Procesar RTH
            rth_commands, rth_state = rth_subsystem.process_rth(rth_state, gps_data, baro_data, battery_data)
            if rth_state['rth_active']:
                commands = rth_commands

            # Enviar comandos al dron
            if ser is not None:
                command = f"CMD,{commands['pitch']},{commands['roll']},{commands['yaw']},{commands['throttle']}"
                ser.write(command.encode('utf-8'))
                ser.write(b'\n')

            # Actualizar video con datos
            telemetry_data = {
                'gps_data': gps_data,
                'baro_data': baro_data,
                'battery_data': battery_data,
                'ir_data': ir_data
            }
            signal_strength = calculate_signal_strength(ewd_state['last_signal_time'])
            if video_subsystem.update_video_frame(video_cap, video_label, flight_data, telemetry_data, signal_strength):
                update_count += 1
                if update_count % 100 == 0:
                    print(f"Actualización de video #{update_count} exitosa")

        except Exception as e:
            print(f"Error en lectura serial o control: {e}")
        time.sleep(0.1)

def update_plot():
    """Actualiza los gráficos en telemetry_plot.html con datos de telemetría y vuelo."""
    global fig, flight_data
    try:
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=("Mapa de Ubicación", "Altitud", "Voltaje de Batería"),
            specs=[[{"type": "scattergeo"}], [{"type": "scatter"}], [{"type": "scatter"}]]
        )

        # Mapa
        fig.add_trace(
            go.Scattergeo(
                lat=plot_data['latitudes'],
                lon=plot_data['longitudes'],
                mode="markers+lines",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="blue")
            ),
            row=1, col=1
        )
        fig.update_geos(projection_type="mercator", showcountries=True, showland=True)

        # Altitud
        fig.add_trace(
            go.Scatter(x=plot_data['times'], y=plot_data['gps_altitudes'], name="Altitud GPS", line=dict(color="blue")),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=plot_data['times'], y=plot_data['baro_altitudes'], name="Altitud Baro", line=dict(color="green")),
            row=2, col=1
        )

        # Voltaje
        fig.add_trace(
            go.Scatter(x=plot_data['times'], y=plot_data['voltages'], name="Voltaje", line=dict(color="orange")),
            row=3, col=1
        )

        # Añadir datos de vuelo como anotaciones
        annotations = []
        if plot_data['times']:
            latest_data = {
                'Altitude': f"{plot_data['baro_altitudes'][-1]:.1f} m" if plot_data['baro_altitudes'] and plot_data['baro_altitudes'][-1] is not None else "0.0 m",
                'Distance': f"{flight_data.get('distance', 0):.1f} m",
                'GPS': f"{plot_data['latitudes'][-1]:.6f}, {plot_data['longitudes'][-1]:.6f}" if plot_data['latitudes'] and plot_data['latitudes'][-1] is not None else "0.000000, 0.000000",
                'Battery': f"{flight_data.get('battery_percent', 0):.0f}%",
                'Speed': f"{flight_data.get('speed', 0):.1f} m/s",
                'Signal': f"{calculate_signal_strength(ewd_state['last_signal_time'])} bars"
            }
            y_pos = 0.95
            for key, value in latest_data.items():
                annotations.append(
                    dict(
                        x=0.05, y=y_pos, xref="paper", yref="paper",
                        text=f"{key}: {value}",
                        showarrow=False, font=dict(size=12, color="white"),
                        bgcolor="rgba(0, 0, 0, 0.5)", xanchor="left", yanchor="top"
                    )
                )
                y_pos -= 0.05

        fig.update_layout(
            height=800, showlegend=True,
            title_text="Telemetría del Dron en Tiempo Real",
            template="plotly_dark", annotations=annotations
        )
        fig.write_html("telemetry_plot.html")
        print("Gráficos actualizados en telemetry_plot.html")  # Depuración
    except Exception as e:
        print(f"Error al actualizar gráficos: {e}")
    root.after(1000, update_plot)

# Iniciar hilo para lectura serial y control
serial_thread = Thread(target=read_serial_and_control, daemon=True)
serial_thread.start()

# Iniciar actualización de gráficos
root.after(1000, update_plot)
print("Programada actualización de gráficos con root.after")  # Depuración

# Forzar actualización inicial de la GUI
root.update()

# Ejecutar GUI y limpieza
try:
    root.mainloop()
finally:
    if video_cap is not None:
        video_subsystem.release_video_stream(video_cap)
    if ser is not None:
        ser.close()
    pygame.quit()