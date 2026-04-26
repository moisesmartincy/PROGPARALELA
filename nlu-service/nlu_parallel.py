import re
import time
from collections import defaultdict
import concurrent.futures
import multiprocessing
import os

class NLUParallelProcessor:
    """Procesador NLU con múltiples estrategias de paralelismo"""
    
    def __init__(self, num_processes=None, num_threads=None):
        self.num_processes = num_processes or int(os.getenv('WORKER_PROCESSES', 4))
        self.num_threads = num_threads or int(os.getenv('THREAD_POOL_SIZE', 10))
        self.patterns = self.load_intent_patterns()
        self.entity_patterns = self.load_entity_patterns()
        
    def load_intent_patterns(self):
        return {
            'saludo': [r'hola', r'buen(os|as).*(días|tardes|noches)', r'hey'],
            'despedida': [r'adiós', r'chao', r'hasta.*luego'],
            'pregunta': [r'qué', r'cómo', r'cuándo', r'dónde', r'por.qué'],
            'tiempo': [r'clima', r'tiempo', r'temperatura'],
            'chiste': [r'chiste', r'gracioso', r'reír'],
            'ayuda': [r'ayuda', r'puedes.*hacer', r'funciones']
        }
    
    def load_entity_patterns(self):
        return {
            'nombre': r'me llamo (\w+)|soy (\w+)',
            'ubicacion': r'en (\w+)|de (\w+)',
            'fecha': r'hoy|mañana|ayer|\d+ de \w+',
            'numero': r'\d+'
        }
    
    def process_single(self, text):
        """Procesa un solo texto"""
        start_time = time.time()
        
        text_lower = text.lower().strip()
        
        # Clasificar intención
        intent_scores = defaultdict(float)
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    intent_scores[intent] += 0.1
        
        if intent_scores:
            main_intent = max(intent_scores.items(), key=lambda x: x[1])
        else:
            main_intent = ('unknown', 0.1)
        
        # Extraer entidades
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value = match.group(1) or match.group(2) or match.group()
                entities.append({
                    'entity': entity_type,
                    'value': value,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return {
            'intent': main_intent[0],
            'confidence': min(main_intent[1], 1.0),
            'entities': entities,
            'processing_time_ms': (time.time() - start_time) * 1000
        }
    
    def process_batch_sequential(self, texts):
        """Procesa un lote de textos secuencialmente"""
        return [self.process_single(text) for text in texts]
    
    def process_batch_parallel_threads(self, texts):
        """Procesa un lote de textos en paralelo usando threads"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_text = {executor.submit(self.process_single, text): text for text in texts}
            
            for future in concurrent.futures.as_completed(future_to_text):
                results.append(future.result())
        
        return results
    
    def process_batch_parallel_processes(self, texts):
        """Procesa un lote de textos en paralelo usando procesos"""
        with multiprocessing.Pool(processes=self.num_processes) as pool:
            results = pool.map(self.process_single, texts)
        return results