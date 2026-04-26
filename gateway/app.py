from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import redis
import json
import time
import threading
import concurrent.futures
from datetime import datetime
import os
import logging
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

# Añade estas métricas al inicio del archivo
REQUESTS_TOTAL = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration')
PARALLEL_REQUESTS = Gauge('gateway_parallel_requests', 'Current parallel requests')
CACHE_HITS = Counter('gateway_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('gateway_cache_misses_total', 'Total cache misses')

# Configuración
app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del sistema
INSTANCE_ID = os.getenv('INSTANCE_ID', '1')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = 6379

# Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ThreadPoolExecutor para procesamiento paralelo
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# URLs de servicios
SERVICES = {
    'nlu': os.getenv('NLU_SERVICE_URL', 'http://nlu-service:8001'),
    'response': os.getenv('RESPONSE_SERVICE_URL', 'http://response-service:8002'),
    'logging': os.getenv('LOGGING_SERVICE_URL', 'http://logging-service:8003')
}

# Añade este endpoint
@app.route('/metrics')
def metrics():
    """Exponer métricas Prometheus"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
def home():
    return jsonify({
        'service': 'API Gateway',
        'instance_id': INSTANCE_ID,
        'status': 'running',
        'features': [
            'Load Balancing',
            'Parallel Processing',
            'Distributed Caching'
        ]
    })

@app.route('/health')
def health():
    """Health check con verificación paralela de servicios"""
    services_status = {}
    
    def check_service(service_name, url):
        try:
            response = requests.get(f"{url}/health", timeout=2)
            return service_name, response.status_code == 200
        except:
            return service_name, False
    
    # Verificar servicios en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SERVICES)) as executor_health:
        futures = []
        for service_name, url in SERVICES.items():
            future = executor_health.submit(check_service, service_name, url)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            service_name, status = future.result()
            services_status[service_name] = 'healthy' if status else 'unhealthy'
    
    return jsonify({
        'gateway': 'healthy',
        'instance': INSTANCE_ID,
        'services': services_status,
        'parallel_checks': len(SERVICES)
    })

@app.route('/chat', methods=['POST'])

def chat_endpoint():
    """Endpoint principal del chatbot con procesamiento paralelo"""
    REQUESTS_TOTAL.labels(method='POST', endpoint='/chat', status='200').inc()
    PARALLEL_REQUESTS.inc()
    with REQUEST_DURATION.time():
        # ... código existente ...
        start_time = time.time()
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'anonymous')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # 1. Verificar cache en paralelo
        cache_key = f"chat:{user_id}:{hash(user_message)}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            result = json.loads(cached_result)
            result['cached'] = True
            result['instance'] = INSTANCE_ID
            return jsonify(result)
        
        # 2. Procesar con NLU
        nlu_response = requests.post(
            f"{SERVICES['nlu']}/analyze",
            json={'text': user_message},
            timeout=3
        ).json()
        
        # 3. Generar respuesta
        response_data = requests.post(
            f"{SERVICES['response']}/generate",
            json={
                'text': user_message,
                'intent': nlu_response.get('intent', 'unknown'),
                'confidence': nlu_response.get('confidence', 0.0),
                'entities': nlu_response.get('entities', [])
            },
            timeout=3
        ).json()
        
        # 4. Crear resultado final
        final_result = {
            'response': response_data.get('response', ''),
            'intent': nlu_response.get('intent'),
            'confidence': nlu_response.get('confidence', 0.0),
            'entities': nlu_response.get('entities', []),
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': (time.time() - start_time) * 1000,
            'instance': INSTANCE_ID,
            'cached': False
        }
        
        # 5. Cachear resultado (asíncrono)
        threading.Thread(
            target=cache_result_async,
            args=(cache_key, final_result, 300)
        ).start()
        
        # 6. Loggear (asíncrono)
        threading.Thread(
            target=log_interaction_async,
            args=(user_message, final_result, start_time)
        ).start()
        
        return jsonify(final_result)
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({
            'response': 'Lo siento, estoy teniendo problemas técnicos.',
            'error': str(e),
            'instance': INSTANCE_ID
        }), 500
    PARALLEL_REQUESTS.dec()

    

@app.route('/parallel/demo')
def parallel_demo():
    """Demo interactiva de paralelismo"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo de Paralelismo</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .demo-container { max-width: 800px; margin: 0 auto; }
            button { padding: 10px 20px; margin: 5px; }
            .result { margin-top: 10px; padding: 10px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <div class="demo-container">
            <h1>Demo de Programación Paralela</h1>
            <button onclick="testSequential()">Probar Secuencial</button>
            <button onclick="testParallel()">Probar Paralelo</button>
            <div class="result" id="result"></div>
        </div>
        <script>
            async function testSequential() {
                const start = performance.now();
                for(let i = 0; i < 5; i++) {
                    await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: 'Test ' + i})
                    });
                }
                const time = performance.now() - start;
                document.getElementById('result').innerHTML = 
                    `Tiempo secuencial: ${time.toFixed(0)}ms`;
            }
            
            async function testParallel() {
                const start = performance.now();
                const promises = [];
                for(let i = 0; i < 5; i++) {
                    promises.push(
                        fetch('/chat', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({message: 'Test ' + i})
                        })
                    );
                }
                await Promise.all(promises);
                const time = performance.now() - start;
                document.getElementById('result').innerHTML = 
                    `Tiempo paralelo: ${time.toFixed(0)}ms<br>
                     Speedup: ${(2500/time).toFixed(2)}x`;
            }
        </script>
    </body>
    </html>
    '''

def cache_result_async(cache_key, result, ttl):
    """Cachear resultado de manera asíncrona"""
    try:
        redis_client.setex(cache_key, ttl, json.dumps(result))
    except Exception as e:
        logger.error(f"Error caching result: {str(e)}")

def log_interaction_async(user_message, result, start_time):
    """Loggear interacción de manera asíncrona"""
    try:
        log_data = {
            'user_message': user_message,
            'bot_response': result.get('response', ''),
            'intent': result.get('intent', ''),
            'confidence': result.get('confidence', 0.0),
            'response_time': (time.time() - start_time) * 1000,
            'timestamp': datetime.now().isoformat(),
            'instance': INSTANCE_ID
        }
        
        requests.post(
            f"{SERVICES['logging']}/log",
            json=log_data,
            timeout=1
        )
    except:
        pass

if __name__ == '__main__':
    print(f"🚀 Gateway Instance {INSTANCE_ID} starting...")
    app.run(host='0.0.0.0', port=8000, threaded=True)