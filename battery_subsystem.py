def process_battery_data(data):
    """Procesa datos de batería desde el puerto serial."""
    try:
        voltage = float(data[4]) if data[4] else 0
        valid = voltage != 0
        return {'voltage': voltage, 'valid': valid}
    except (ValueError, IndexError):
        return {'voltage': 0, 'valid': False}

def format_battery_data(battery_data):
    """Formatea datos de batería para visualización."""
    return f"Voltaje de Batería: {battery_data['voltage']:.1f} V" if battery_data['valid'] else "Voltaje de Batería: 0"