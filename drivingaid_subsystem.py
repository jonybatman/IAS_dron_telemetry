import time

def initialize_drivingaid():
    """Inicializa el subsistema DrivingAid para estabilización."""
    print("DrivingAid ON")
    return {
        'last_time': None,
        'error_sum_pitch': 0.0,
        'error_sum_roll': 0.0,
        'error_sum_yaw': 0.0,
        'last_error_pitch': 0.0,
        'last_error_roll': 0.0,
        'last_error_yaw': 0.0,
        'drivingaid_active': True
    }

def process_drivingaid(drivingaid_state, mpu_data, dt, button_b):
    """Procesa datos del MPU-6050 para estabilizar el dron."""
    try:
        # Validar button_b
        button_b = button_b if button_b is not None else False

        # Togglear estado con botón B
        if button_b:
            drivingaid_state['drivingaid_active'] = not drivingaid_state['drivingaid_active']
            print("DrivingAid ON" if drivingaid_state['drivingaid_active'] else "DrivingAid OFF")

        if not drivingaid_state['drivingaid_active']:
            return {'pitch': 0, 'roll': 0, 'yaw': 0}, drivingaid_state

        if not mpu_data.get('valid', False):
            return {'pitch': 0, 'roll': 0, 'yaw': 0}, drivingaid_state

        pitch = mpu_data['pitch']
        roll = mpu_data['roll']
        yaw = mpu_data['yaw']

        kp, ki, kd = 2.0, 0.1, 0.5
        error_pitch = 0 - pitch
        drivingaid_state['error_sum_pitch'] += error_pitch * dt
        d_error_pitch = (error_pitch - drivingaid_state['last_error_pitch']) / dt
        pitch_adjust = kp * error_pitch + ki * drivingaid_state['error_sum_pitch'] + kd * d_error_pitch

        error_roll = 0 - roll
        drivingaid_state['error_sum_roll'] += error_roll * dt
        d_error_roll = (error_roll - drivingaid_state['last_error_roll']) / dt
        roll_adjust = kp * error_roll + ki * drivingaid_state['error_sum_roll'] + kd * d_error_roll

        error_yaw = 0 - yaw
        drivingaid_state['error_sum_yaw'] += error_yaw * dt
        d_error_yaw = (error_yaw - drivingaid_state['last_error_yaw']) / dt
        yaw_adjust = kp * error_yaw + ki * drivingaid_state['error_sum_yaw'] + kd * d_error_yaw

        pitch_adjust = max(-100, min(100, pitch_adjust))
        roll_adjust = max(-100, min(100, roll_adjust))
        yaw_adjust = max(-100, min(100, yaw_adjust))

        drivingaid_state['last_error_pitch'] = error_pitch
        drivingaid_state['last_error_roll'] = error_roll
        drivingaid_state['last_error_yaw'] = error_yaw
        drivingaid_state['last_time'] = time.time()

        return {
            'pitch': int(pitch_adjust),
            'roll': int(roll_adjust),
            'yaw': int(yaw_adjust)
        }, drivingaid_state
    except Exception as e:
        print(f"Error en DrivingAid: {e}")
        return {'pitch': 0, 'roll': 0, 'yaw': 0}, drivingaid_state