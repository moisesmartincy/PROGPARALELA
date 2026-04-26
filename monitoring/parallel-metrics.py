from prometheus_client import start_http_server, Gauge
import psutil
import time
import threading

# Métricas Prometheus
CPU_UTILIZATION = Gauge('cpu_utilization_percent', 'CPU utilization percentage')
MEMORY_UTILIZATION = Gauge('memory_utilization_percent', 'Memory utilization percentage')

def collect_system_metrics():
    """Colectar métricas del sistema en segundo plano"""
    while True:
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_UTILIZATION.set(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            MEMORY_UTILIZATION.set(memory.percent)
            
            time.sleep(5)
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            time.sleep(10)

if __name__ == '__main__':
    # Iniciar servidor Prometheus en puerto 9100
    start_http_server(9100)
    
    # Iniciar colector de métricas en segundo plano
    collector_thread = threading.Thread(target=collect_system_metrics, daemon=True)
    collector_thread.start()
    
    print("📊 Parallel metrics server running on port 9100")
    
    # Mantener vivo
    while True:
        time.sleep(1)