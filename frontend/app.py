from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración
LOAD_BALANCER_URL = os.getenv('LOAD_BALANCER_URL', 'http://load-balancer')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para enviar mensajes al chatbot"""
    try:
        message = request.json.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Enviar al load balancer
        response = requests.post(
            f'{LOAD_BALANCER_URL}/chat',
            json={'message': message, 'user_id': 'web_user'},
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Service unavailable'}), 503
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check"""
    try:
        # Verificar load balancer
        response = requests.get(f'{LOAD_BALANCER_URL}/health', timeout=2)
        return jsonify({
            'frontend': 'healthy',
            'load_balancer': 'healthy' if response.status_code == 200 else 'unhealthy'
        })
    except:
        return jsonify({'frontend': 'healthy', 'load_balancer': 'unreachable'})

@app.route('/admin')
def admin():
    """Panel de administración"""
    return render_template('admin.html')

# Crear directorios si no existen
import os
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

if __name__ == '__main__':
    print("🎨 Frontend starting...")
    app.run(host='0.0.0.0', port=8080, threaded=True)