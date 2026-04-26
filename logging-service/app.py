from flask import Flask, request, jsonify
from datetime import datetime
import json
import threading
import queue
import time
import os

app = Flask(__name__)

# Cola para procesamiento asíncrono de logs
log_queue = queue.Queue()

class AsyncLogProcessor:
    """Procesador de logs asíncrono"""
    
    def __init__(self):
        self.batch_size = 10
        self.batch = []
        self.processing = False
        
    def start(self):
        """Iniciar procesador en segundo plano"""
        self.processing = True
        thread = threading.Thread(target=self.process_loop)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """Detener procesador"""
        self.processing = False
    
    def add_log(self, log_data):
        """Añadir log a la cola"""
        log_queue.put(log_data)
    
    def process_loop(self):
        """Loop de procesamiento de logs"""
        while self.processing:
            try:
                # Obtener log de la cola
                log_data = log_queue.get(timeout=1)
                self.batch.append(log_data)
                
                # Si el batch está lleno, escribirlo
                if len(self.batch) >= self.batch_size:
                    self.flush_batch()
                    
            except queue.Empty:
                # Si no hay logs, verificar si debemos escribir el batch
                if self.batch:
                    self.flush_batch()
    
    def flush_batch(self):
        """Escribir batch de logs a archivo"""
        try:
            with open('/app/logs/chatbot.log', 'a') as f:
                for log in self.batch:
                    f.write(json.dumps(log) + '\n')
            
            print(f"📝 Flushed {len(self.batch)} logs to file")
            self.batch = []
            
        except Exception as e:
            print(f"Error flushing logs: {e}")

# Iniciar procesador de logs
log_processor = AsyncLogProcessor()
log_processor.start()

@app.route('/')
def home():
    return jsonify({'service': 'Logging Service', 'status': 'running'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/log', methods=['POST'])
def log_event():
    """Recibir y procesar un evento de log"""
    try:
        log_data = request.get_json()
        
        # Añadir timestamp si no viene
        if 'timestamp' not in log_data:
            log_data['timestamp'] = datetime.now().isoformat()
        
        # Añadir a la cola para procesamiento asíncrono
        log_processor.add_log(log_data)
        
        return jsonify({'status': 'logged', 'timestamp': log_data['timestamp']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs/recent')
def get_recent_logs():
    """Obtener logs recientes"""
    try:
        logs = []
        try:
            with open('/app/logs/chatbot.log', 'r') as f:
                lines = f.readlines()[-50:]  # Últimas 50 líneas
                for line in lines:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        pass
        except FileNotFoundError:
            pass
        
        return jsonify({
            'count': len(logs),
            'logs': logs[-10:]  # Devolver solo los últimos 10
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("📝 Logging Service starting with async processing...")
    app.run(host='0.0.0.0', port=8003, threaded=True)