import random
import time
from datetime import datetime

class ResponseGenerator:
    def __init__(self):
        self.templates = self.load_templates()
    
    def load_templates(self):
        return {
            'saludo': [
                "¡Hola! ¿Cómo estás? 😊",
                "¡Buen día! Soy tu asistente virtual. ¿En qué puedo ayudarte?",
                "¡Hola! Me alegra verte. ¿Qué necesitas?",
                "¡Hey! ¿Qué tal? Cuéntame, ¿qué puedo hacer por ti hoy?"
            ],
            'despedida': [
                "¡Hasta luego! Espero verte pronto 👋",
                "¡Adiós! Que tengas un excelente día",
                "Nos vemos. Recuerda que estoy aquí para ayudarte",
                "¡Chao! No dudes en volver si necesitas algo más"
            ],
            'pregunta': [
                "No estoy seguro de entender. ¿Podrías reformular tu pregunta? 🤔",
                "Interesante pregunta. Déjame pensar... ¿Podrías ser más específico?",
                "No tengo una respuesta para eso todavía. ¿Puedo ayudarte con otra cosa?"
            ],
            'tiempo': [
                "No tengo acceso al clima en tiempo real, pero puedo sugerirte consultar una app del tiempo 🌤️",
                "Para el clima exacto, te recomiendo mirar por la ventana o usar una app meteorológica"
            ],
            'chiste': [
                "¿Qué le dice un gusano a otro gusano? ¡Vamos a dar una vuelta a la manzana! 🍎",
                "¿Por qué los pájaros no usan Facebook? ¡Porque ya tienen Twitter! 🐦"
            ],
            'ayuda': [
                "Puedo ayudarte con: responder preguntas, conversar, contar chistes y más. ¿Qué te gustaría hacer?",
                "Mis funciones incluyen: análisis de texto, generación de respuestas, y mantener conversaciones. ¿En qué puedo asistirte?"
            ],
            'unknown': [
                "No estoy seguro de entender. ¿Podrías reformular tu pregunta? 🤔",
                "Interesante pregunta. Déjame pensar... ¿Podrías ser más específico?"
            ]
        }
    
    def generate(self, intent, entities=None):
        """Genera una respuesta basada en la intención"""
        start_time = time.time()
        
        templates = self.templates.get(intent, self.templates['unknown'])
        response = random.choice(templates)
        
        # Personalizar si hay hora
        if intent == 'pregunta' and 'hora' in str(entities).lower():
            now = datetime.now()
            response = f"Son las {now.strftime('%H:%M')} ⏰"
        
        processing_time = time.time() - start_time
        
        return {
            'response': response,
            'intent': intent,
            'processing_time_ms': processing_time * 1000
        }