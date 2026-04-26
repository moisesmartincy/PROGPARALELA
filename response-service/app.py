from flask import Flask, request, jsonify
import redis
import json
from response_generator import ResponseGenerator
import os

app = Flask(__name__)

# Configuración
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')

# Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Generador de respuestas
generator = ResponseGenerator()

@app.route('/')
def home():
    return jsonify({'service': 'Response Service', 'status': 'running'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/generate', methods=['POST'])
def generate_response():
    """Generar respuesta basada en intención"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        intent = data.get('intent', 'unknown')
        entities = data.get('entities', [])
        
        # Verificar cache
        cache_key = f"response:{intent}:{hash(text)}"
        cached = redis_client.get(cache_key)
        
        if cached:
            result = json.loads(cached)
            result['cached'] = True
            return jsonify(result)
        
        # Generar respuesta
        result = generator.generate(intent, entities)
        
        # Cachear resultado
        redis_client.setex(cache_key, 300, json.dumps(result))
        
        result['cached'] = False
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("💬 Response Service starting...")
    app.run(host='0.0.0.0', port=8002, threaded=True)