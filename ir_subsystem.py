def process_ir_data(data):
    """Procesa datos de LEDs IR desde el puerto serial."""
    try:
        ir_status = int(data[5]) if data[5] else 0
        valid = True
        return {'ir_status': ir_status, 'valid': valid}
    except (ValueError, IndexError):
        return {'ir_status': 0, 'valid': False}

def format_ir_data(ir_data):
    """Formatea datos de LEDs IR para visualización."""
    return "LEDs IR: ON" if ir_data['valid'] and ir_data['ir_status'] == 1 else "LEDs IR: OFF"