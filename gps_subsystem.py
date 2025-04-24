def process_gps_data(data):
    """Procesa datos GPS desde el puerto serial."""
    try:
        lat = float(data[0]) if data[0] else 0
        lon = float(data[1]) if data[1] else 0
        gps_alt = float(data[2]) if data[2] else 0
        valid = lat != 0 or lon != 0 or gps_alt != 0
        return {
            'latitude': lat,
            'longitude': lon,
            'gps_altitude': gps_alt,
            'valid': valid
        }
    except (ValueError, IndexError):
        return {'latitude': 0, 'longitude': 0, 'gps_altitude': 0, 'valid': False}

def format_gps_data(gps_data):
    """Formatea datos GPS para visualización."""
    if gps_data['valid']:
        lat_text = f"Latitud: {gps_data['latitude']:.6f}"
        lon_text = f"Longitud: {gps_data['longitude']:.6f}"
        gps_alt_text = f"Altitud GPS: {gps_data['gps_altitude']:.1f} m"
    else:
        lat_text = "Latitud: 0"
        lon_text = "Longitud: 0"
        gps_alt_text = "Altitud GPS: 0"
    return lat_text, lon_text, gps_alt_text