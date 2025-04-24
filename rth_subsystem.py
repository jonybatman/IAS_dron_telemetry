def initialize_rth():
    """Inicializa el subsistema Return-to-Home (RTH)."""
    print("RTH ON")
    return {
        'rth_active': False,
        'home_lat': None,
        'home_lon': None,
        'target_altitude': 10.0  # Altitud objetivo en metros
    }

def process_rth(rth_state, gps_data, baro_data, battery_data):
    """Procesa la lógica de Return-to-Home."""
    try:
        # Activar RTH si el voltaje es bajo
        if battery_data['valid'] and battery_data['voltage'] < 10.5 and not rth_state['rth_active']:
            rth_state['rth_active'] = True
            rth_state['home_lat'] = gps_data['latitude'] if gps_data['valid'] else 0
            rth_state['home_lon'] = gps_data['longitude'] if gps_data['valid'] else 0
            print("RTH ON")

        # Comandos RTH
        commands = {'pitch': 500, 'roll': 500, 'yaw': 500, 'throttle': 500}
        if rth_state['rth_active']:
            if gps_data['valid'] and baro_data['valid']:
                # Lógica simplificada: mantener altitud objetivo
                error_alt = rth_state['target_altitude'] - baro_data['baro_altitude']
                throttle_adjust = int(error_alt * 50)  # Ganancia proporcional
                commands['throttle'] = max(400, min(600, 500 + throttle_adjust))
            else:
                commands['throttle'] = 500  # Neutral si no hay datos válidos

        return commands, rth_state
    except Exception as e:
        print(f"Error en RTH: {e}")
        return {'pitch': 500, 'roll': 500, 'yaw': 500, 'throttle': 500}, rth_state