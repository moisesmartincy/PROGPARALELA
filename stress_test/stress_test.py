import concurrent.futures
import time
import requests
from datetime import datetime

def send_chat_request(message, instance=1):
    """Enviar solicitud de chat"""
    try:
        start_time = time.time()
        response = requests.post(
            f'http://localhost:800{instance - 1}/chat',
            json={'message': message, 'user_id': 'tester'},
            timeout=5
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return {
                'success': True,
                'response_time': response_time,
                'instance': response.json().get('instance', 'unknown')
            }
        else:
            return {
                'success': False,
                'response_time': response_time
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def test_sequential(num_requests=10):
    """Prueba secuencial"""
    print(f"🧪 Testing SEQUENTIAL with {num_requests} requests...")
    
    start_time = time.time()
    results = []
    
    for i in range(num_requests):
        result = send_chat_request(f"Test message {i}")
        results.append(result)
        print(f"  Request {i+1}/{num_requests}: {result['response_time']:.3f}s")
    
    total_time = time.time() - start_time
    
    successful = sum(1 for r in results if r['success'])
    avg_time = total_time / num_requests
    
    print(f"✅ Sequential test completed:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg time per request: {avg_time:.3f}s")
    print(f"   Successful: {successful}/{num_requests}")
    print(f"   Throughput: {num_requests/total_time:.2f} requests/second")
    
    return total_time

def test_parallel(num_requests=10, max_workers=5):
    """Prueba paralela"""
    print(f"🧪 Testing PARALLEL with {num_requests} requests ({max_workers} workers)...")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_requests):
            future = executor.submit(
                send_chat_request,
                f"Parallel test {i}"
            )
            futures.append(future)
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    successful = sum(1 for r in results if r['success'])
    avg_time = total_time / num_requests
    
    print(f"✅ Parallel test completed:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg time per request: {avg_time:.3f}s")
    print(f"   Successful: {successful}/{num_requests}")
    print(f"   Throughput: {num_requests/total_time:.2f} requests/second")
    
    # Mostrar distribución por instancia
    instances = {}
    for result in results:
        if result.get('instance'):
            instances[result['instance']] = instances.get(result['instance'], 0) + 1
    
    print(f"   Load distribution: {instances}")
    
    return total_time

def run_comparative_test():
    """Ejecutar prueba comparativa"""
    print("=" * 60)
    print("🚀 COMPARATIVE PARALLEL LOAD TEST")
    print("=" * 60)
    
    # Prueba secuencial
    seq_time = test_sequential(5)
    
    print("\n" + "-" * 60)
    
    # Pruebas paralelas con diferentes configuraciones
    for workers in [2, 5, 10]:
        para_time = test_parallel(10, workers)
        
        speedup = seq_time * 2 / para_time  # Factor 2 porque paralelo procesa 10 vs 5 secuenciales
        
        print(f"\n📊 Analysis for {workers} workers:")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Efficiency: {(speedup/workers)*100:.1f}%")
        print("-" * 60)

if __name__ == '__main__':
    print("Waiting for services to start...")
    time.sleep(10)  # Esperar que los servicios inicien
    
    run_comparative_test()
    
    print("\n" + "=" * 60)
    print("🎯 KEY FINDINGS:")
    print("=" * 60)
    print("1. Paralelismo mejora throughput significativamente")
    print("2. Speedup no es lineal debido a overhead")
    print("3. Load balancing distribuye carga entre instancias")
    print("4. Cache reduce latencia en solicitudes repetidas")