import time


def initialize_flystandard():
    """Inicializa el subsistema FlyStandard para mantener altura constante."""
    print("FlyStandard ON")
    return {
        'flystandard_active': False,
        'target_altitude': None,
        'last_time': None,
        'error_sum': 0.0,
        'last_error': 0.0
    }

def process_flystandard(flystandard_state, baro_data, button_a):
    """Procesa la lógica de FlyStandard para control de altura."""
    try:
        # Togglear estado con botón A
        if button_a:
            if flystandard_state['flystandard_active']:
                flystandard_state['flystandard_active'] = False
                flystandard_state['target_altitude'] = None
                print("FlyStandard OFF")
            else:
                flystandard_state['flystandard_active'] = True
                if baro_data['valid']:
                    flystandard_state['target_altitude'] = baro_data['baro_altitude']
                else:
                    flystandard_state['target_altitude'] = 0
                print("FlyStandard ON")

        # Procesar comandos si está activo
        commands = {'throttle': 500}
        if flystandard_state['flystandard_active'] and baro_data['valid']:
            current_time = time.time()
            dt = current_time - flystandard_state['last_time'] if flystandard_state['last_time'] else 0.1
            flystandard_state['last_time'] = current_time

            error = flystandard_state['target_altitude'] - baro_data['baro_altitude']
            flystandard_state['error_sum'] += error * dt
            d_error = (error - flystandard_state['last_error']) / dt
            flystandard_state['last_error'] = error

            kp, ki, kd = 50.0, 0.1, 10.0
            throttle_adjust = kp * error + ki * flystandard_state['error_sum'] + kd * d_error
            commands['throttle'] = max(400, min(600, 500 + int(throttle_adjust)))

        return commands, flystandard_state
    except Exception as e:
        print(f"Error en FlyStandard: {e}")
        return {'throttle': 500}, flystandard_state