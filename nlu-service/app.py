from flask import Flask, request, jsonify
import redis
import json
import time
import concurrent.futures
from nlu_parallel import NLUParallelProcessor
import os

app = Flask(__name__)

# Configuración
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', 4))
THREAD_POOL_SIZE = int(os.getenv('THREAD_POOL_SIZE', 10))

# Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Procesador NLU
processor = NLUParallelProcessor(WORKER_PROCESSES, THREAD_POOL_SIZE)

@app.route('/')
def home():
    return jsonify({
        'service': 'NLU Service',
        'parallel_config': {
            'worker_processes': WORKER_PROCESSES,
            'thread_pool_size': THREAD_POOL_SIZE
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """Análisis de texto único"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Verificar cache
        cache_key = f"nlu:{hash(text)}"
        cached = redis_client.get(cache_key)
        
        if cached:
            result = json.loads(cached)
            result['cached'] = True
            return jsonify(result)
        
        # Procesar
        result = processor.process_single(text)
        
        # Cachear resultado
        redis_client.setex(cache_key, 3600, json.dumps(result))
        
        result['cached'] = False
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """Análisis por lotes - DEMOSTRACIÓN DE PARALELISMO"""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        mode = data.get('mode', 'threads')  # sequential, threads, processes
        
        if not texts:
            return jsonify({'error': 'No texts provided'}), 400
        
        # Medir tiempo de procesamiento
        start_time = time.time()
        
        # Seleccionar estrategia de paralelismo
        if mode == 'sequential':
            results = processor.process_batch_sequential(texts)
        elif mode == 'processes':
            results = processor.process_batch_parallel_processes(texts)
        else:  # threads (default)
            results = processor.process_batch_parallel_threads(texts)
        
        processing_time = time.time() - start_time
        
        # Calcular métricas de paralelismo
        estimated_sequential_time = sum(r['processing_time_ms'] for r in results) / 1000
        
        speedup = estimated_sequential_time / processing_time if processing_time > 0 else 1
        
        return jsonify({
            'results': results,
            'parallel_metrics': {
                'batch_size': len(texts),
                'parallel_mode': mode,
                'processing_time_seconds': round(processing_time, 3),
                'estimated_sequential_time_seconds': round(estimated_sequential_time, 3),
                'speedup': round(speedup, 2),
                'efficiency_percent': round((speedup / WORKER_PROCESSES) * 100, 1) if mode == 'processes' else None,
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🧠 NLU Service starting with {WORKER_PROCESSES} worker processes")
    print(f"🧵 Thread pool size: {THREAD_POOL_SIZE}")
    app.run(host='0.0.0.0', port=8001, threaded=True)