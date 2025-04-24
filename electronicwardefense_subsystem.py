import time

def initialize_electronicwardefense():
    """Inicializa el subsistema ElectronicWarDefense para reconexión de frecuencia."""
    print("ElectronicWarDefense ON")
    return {
        'frequencies': [915, 918, 921, 924, 927],
        'current_frequency': 0,
        'last_signal_time': time.time(),
        'signal_timeout': 2.0,
        'scan_interval': 1.0,
        'scanning': False,
        'last_scan_time': time.time()
    }

def process_electronicwardefense(state, signal_received, set_frequency_callback):
    """Procesa la lógica de reconexión en frecuencias alternativas."""
    try:
        current_time = time.time()
        if signal_received:
            state['last_signal_time'] = current_time
            state['scanning'] = False
            return state

        if current_time - state['last_signal_time'] > state['signal_timeout']:
            if not state['scanning']:
                state['scanning'] = True
                print("Signal lost, scanning frequencies")
                state['last_scan_time'] = current_time

            if current_time - state['last_scan_time'] > state['scan_interval']:
                state['current_frequency'] = (state['current_frequency'] + 1) % len(state['frequencies'])
                new_freq = state['frequencies'][state['current_frequency']]
                set_frequency_callback(new_freq)
                print(f"Reconnected on frequency {new_freq} MHz")
                state['last_scan_time'] = current_time

        return state
    except Exception as e:
        print(f"Error en ElectronicWarDefense: {e}")
        return state