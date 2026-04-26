# Este archivo es importado por app.py
# Contiene funciones auxiliares para workers

def process_nlu_task(data):
    """Procesar tarea NLU"""
    print(f"Processing NLU task: {data}")
    # Aquí iría el procesamiento real
    return {'status': 'processed'}

def process_response_task(data):
    """Procesar tarea de respuesta"""
    print(f"Processing response task: {data}")
    return {'status': 'processed'}