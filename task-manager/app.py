from flask import Flask, request, jsonify
import pika
import json
import threading
import time
import os

app = Flask(__name__)

# Configuración
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

# Conexión a RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()

# Declarar colas
channel.queue_declare(queue='nlu_tasks')
channel.queue_declare(queue='response_tasks')
channel.queue_declare(queue='logging_tasks')

@app.route('/')
def home():
    return jsonify({'service': 'Task Manager', 'status': 'running'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/task', methods=['POST'])
def add_task():
    """Añadir tarea a la cola"""
    try:
        data = request.get_json()
        task_type = data.get('type', 'general')
        
        # Determinar la cola basada en el tipo de tarea
        queue = 'nlu_tasks' if task_type == 'nlu' else 'response_tasks' if task_type == 'response' else 'logging_tasks'
        
        # Publicar la tarea
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(data),
            properties=pika.BasicProperties(delivery_mode=2)  # Persistente
        )
        
        return jsonify({'status': 'task added', 'queue': queue})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_workers():
    """Iniciar workers en segundo plano"""
    threading.Thread(target=nlu_worker, daemon=True).start()
    threading.Thread(target=response_worker, daemon=True).start()
    print("👷 Workers started in background")

def nlu_worker():
    """Worker para procesar tareas NLU"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='nlu_tasks')
    
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            print(f"👷 NLU Worker processing task: {data.get('type')}")
            # Simular procesamiento
            time.sleep(0.5)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error in NLU worker: {e}")
    
    channel.basic_consume(queue='nlu_tasks', on_message_callback=callback)
    channel.start_consuming()

def response_worker():
    """Worker para procesar tareas de respuesta"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='response_tasks')
    
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            print(f"👷 Response Worker processing task: {data.get('type')}")
            # Simular procesamiento
            time.sleep(0.3)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error in Response worker: {e}")
    
    channel.basic_consume(queue='response_tasks', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    # Iniciar workers
    start_workers()
    
    print("⚙️ Task Manager starting...")
    app.run(host='0.0.0.0', port=8004, threaded=True)