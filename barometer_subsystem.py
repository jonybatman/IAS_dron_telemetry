def process_barometer_data(data):
    """Procesa datos del barómetro desde el puerto serial."""
    try:
        baro_alt = float(data[3]) if data[3] else 0
        valid = baro_alt != 0
        return {'baro_altitude': baro_alt, 'valid': valid}
    except (ValueError, IndexError):
        return {'baro_altitude': 0, 'valid': False}

def format_barometer_data(baro_data):
    """Formatea datos del barómetro para visualización."""
    return f"Altitud Barométrica: {baro_data['baro_altitude']:.1f} m" if baro_data['valid'] else "Altitud Barométrica: 0"