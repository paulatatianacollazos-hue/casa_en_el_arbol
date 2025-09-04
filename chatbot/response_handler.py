import random
import re
from typing import Dict, List, Any
from datetime import datetime

class ResponseHandler:
    """Manejador de respuestas del chatbot"""
    
    def __init__(self, knowledge_base):
        self.knowledge = knowledge_base
        self.context_memory = {}  # Memoria de contexto por sesión
    
    def generate_response(self, user_message: str, session_id: str) -> Dict[str, Any]:
        """Generar respuesta del chatbot basada en el mensaje del usuario"""
        message = user_message.lower().strip()
        
        # Actualizar contexto de la sesión
        if session_id not in self.context_memory:
            self.context_memory[session_id] = {'last_topic': None, 'conversation_count': 0}
        
        self.context_memory[session_id]['conversation_count'] += 1
        
        response = self._process_message(message, session_id)
        
        return {
            'text': response['text'],
            'suggestions': response.get('suggestions', []),
            'quick_replies': response.get('quick_replies', [])
        }
    
    def _process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Procesar mensaje y determinar tipo de respuesta"""
        keywords = self.knowledge.get_keywords()
        
        # Verificar saludos
        if self._contains_keywords(message, keywords['saludos']):
            return self._handle_greeting(session_id)
        
        # Verificar despedidas
        if self._contains_keywords(message, keywords['despedidas']):
            return self._handle_farewell()
        
        # Verificar productos populares
        if (self._contains_keywords(message, keywords['populares']) or 
            'populares' in message or 'recomend' in message):
            return self._handle_popular_products()
        
        # Verificar precios
        if self._contains_keywords(message, keywords['precios']):
            return self._handle_prices(message)
        
        # Verificar instalación
        if self._contains_keywords(message, keywords['instalacion']):
            return self._handle_installation()
        
        # Verificar garantía
        if self._contains_keywords(message, keywords['garantia']):
            return self._handle_warranty()
        
        # Verificar envío
        if self._contains_keywords(message, keywords['envio']):
            return self._handle_shipping()
        
        # Verificar contacto
        if self._contains_keywords(message, keywords['contacto']):
            return self._handle_contact()
        
        # Verificar medidas
        if self._contains_keywords(message, keywords['medidas']):
            return self._handle_measurements()
        
        # Verificar productos específicos
        product_response = self._handle_specific_product(message)
        if product_response:
            return product_response
        
        # Respuesta por defecto con sugerencias contextuales
        return self._handle_default_response(session_id)
    
    def _contains_keywords(self, message: str, keyword_list: List[str]) -> bool:
        """Verificar si el mensaje contiene alguna de las palabras clave"""
        return any(keyword in message for keyword in keyword_list)
    
    def _handle_greeting(self, session_id: str) -> Dict[str, Any]:
        """Manejar saludos"""
        responses = self.knowledge.get_responses()['saludos']
        
        # Personalizar saludo según el número de conversaciones
        count = self.context_memory[session_id]['conversation_count']
        if count > 1:
            greeting = "¡Hola de nuevo! 😊 ¿En qué más puedo ayudarte?"
        else:
            greeting = random.choice(responses)
        
        return {
            'text': greeting,
            'quick_replies': [
                '🏆 Productos populares',
                '💰 Ver precios',
                '🔧 Instalaciones',
                '📞 Contacto'
            ]
        }
    
    def _handle_farewell(self) -> Dict[str, Any]:
        """Manejar despedidas"""
        responses = self.knowledge.get_responses()['despedidas']
        return {
            'text': random.choice(responses),
            'quick_replies': []
        }
    
    def _handle_popular_products(self) -> Dict[str, Any]:
        """Manejar consulta sobre productos populares"""
        products = self.knowledge.get_all_products()
        
        # Crear lista de productos populares con descuentos primero
        popular_list = []
        for key, product in products.items():
            if 'descuento' in product and product['descuento'] > 0:
                popular_list.append(f"🏆 **{product['nombre']}** - {product['precio_formateado']} (¡Con {product['descuento']}% de descuento!)")
            else:
                popular_list.append(f"🏆 **{product['nombre']}** - {product['precio_formateado']}")
        
        response_text = "Nuestros productos más populares son:\n\n" + "\n".join(popular_list)
        response_text += "\n\n¿Te interesa alguno en particular?"
        
        return {
            'text': response_text,
            'quick_replies': ['Ver más detalles', 'Precios con instalación', '¿Hacen envíos?']
        }
    
    def _handle_prices(self, message: str) -> Dict[str, Any]:
        """Manejar consultas sobre precios"""
        products = self.knowledge.get_all_products()
        
        # Si menciona un producto específico
        specific_product = self._extract_product_from_message(message)
        if specific_product:
            product = products.get(specific_product)
            if product:
                text = f"💰 **{product['nombre']}**\n"
                text += f"Precio: {product['precio_formateado']}"
                
                if 'descuento' in product:
                    original_price = int(product['precio'] / (1 - product['descuento']/100))
                    text += f"\n~~${original_price:,}~~ (Descuento del {product['descuento']}%)"
                
                text += f"\n\n📋 {product['descripcion']}"
                text += f"\n⏱ Tiempo de entrega: {product.get('tiempo_entrega', '5-7 días hábiles')}"
                text += "\n\n¿Necesitas más información sobre este producto?"
                
                return {
                    'text': text,
                    'quick_replies': ['Ver características', 'Instalación incluida?', 'Otros productos']
                }
        
        # Lista general de precios
        price_list = []
        for key, product in products.items():
            if 'descuento' in product and product['descuento'] > 0:
                price_list.append(f"💰 **{product['nombre']}** - {product['precio_formateado']} (Oferta: -{product['descuento']}%)")
            else:
                price_list.append(f"💰 **{product['nombre']}** - {product['precio_formateado']}")
        
        response_text = "Aquí tienes nuestros precios actuales:\n\n" + "\n".join(price_list)
        response_text += "\n\nTodos los precios incluyen IVA. ¿Te interesa algún producto en particular?"
        
        return {
            'text': response_text,
            'quick_replies': ['¿Incluye instalación?', 'Formas de pago', 'Ver características']
        }
    
    def _handle_installation(self) -> Dict[str, Any]:
        """Manejar consultas sobre instalación"""
        service = self.knowledge.get_service_info('instalacion')
        
        text = "🔧 **Servicio de Instalación**\n\n"
        text += f"{service['descripcion']}\n\n"
        text += "**El servicio incluye:**\n"
        for item in service['incluye']:
            text += f"• {item}\n"
        text += f"\n⏱ **Tiempo promedio:** {service['tiempo']}"
        text += f"\n💰 **Costo:** {service['costo']}"
        text += "\n\n¿Necesitas más detalles sobre la instalación?"
        
        return {
            'text': text,
            'quick_replies': ['Costo de instalación', 'Agendar visita técnica', 'Ver productos']
        }
    
    def _handle_warranty(self) -> Dict[str, Any]:
        """Manejar consultas sobre garantía"""
        service = self.knowledge.get_service_info('garantia')
        
        text = "🛡️ **Garantía y Protección**\n\n"
        text += f"• **Estructura:** {service['estructura']}\n"
        text += f"• **Herrajes y accesorios:** {service['herrajes']}\n"
        text += f"• **Instalación:** {service['instalacion']}\n\n"
        text += "**Nuestra garantía cubre:**\n"
        for item in service['cobertura']:
            text += f"• {item}\n"
        text += "\n¿Tienes alguna duda específica sobre la garantía?"
        
        return {
            'text': text,
            'quick_replies': ['¿Qué no cubre?', 'Proceso de garantía', 'Contactar soporte']
        }
    
    def _handle_shipping(self) -> Dict[str, Any]:
        """Manejar consultas sobre envío"""
        service = self.knowledge.get_service_info('envio')
        
        text = "🚚 **Envíos y Entregas**\n\n"
        text += f"{service['descripcion']}\n"
        text += f"⏱️ **Tiempo de entrega:** {service['tiempo_entrega']}\n\n"
        text += "**El servío incluye:**\n"
        for item in service['incluye']:
            text += f"• {item}\n"
        text += "\n¿En qué zona necesitas la entrega?"
        
        return {
            'text': text,
            'quick_replies': ['Costo de envío', 'Zonas de cobertura', 'Programar entrega']
        }
    
    def _handle_contact(self) -> Dict[str, Any]:
        """Manejar solicitudes de información de contacto"""
        contact = self.knowledge.get_contact_info()
        
        text = "📞 **Información de Contacto**\n\n"
        text += f"**🕐 Horarios:** {contact['horarios']}\n"
        text += f"**📱 Teléfono:** {contact['telefono']}\n"
        text += f"**💬 WhatsApp:** {contact['whatsapp']}\n"
        text += f"**📧 Email:** {contact['email']}\n"
        text += f"**📍 Dirección:** {contact['direccion']}\n\n"
        text += "**Redes sociales:**\n"
        text += f"• Instagram: {contact['redes_sociales']['instagram']}\n"
        text += f"• Facebook: {contact['redes_sociales']['facebook']}\n\n"
        text += "¿Prefieres que te contactemos por algún medio específico?"
        
        return {
            'text': text,
            'quick_replies': ['Llamar por WhatsApp', 'Agendar visita', 'Ver ubicación']
        }
    
    def _handle_measurements(self) -> Dict[str, Any]:
        """Manejar consultas sobre medidas"""
        service = self.knowledge.get_service_info('medidas')
        
        text = "📏 **Servicio de Medición Personalizada**\n\n"
        text += f"{service['descripcion']}\n\n"
        text += "**Nuestro proceso incluye:**\n"
        for step in service['proceso']:
            text += f"• {step}\n"
        text += "\n✅ ¡La visita técnica es completamente GRATUITA!"
        text += "\n\n¿Te gustaría agendar una visita técnica?"
        
        return {
            'text': text,
            'quick_replies': ['Agendar visita', 'Costo del servicio', 'Ver productos']
        }
    
    def _handle_specific_product(self, message: str) -> Dict[str, Any]:
        """Manejar consultas sobre productos específicos"""
        products = self.knowledge.get_all_products()
        
        # Buscar producto mencionado
        for key, product in products.items():
            if product['nombre'].lower() in message or key in message:
                text = f"🛋️ **{product['nombre']}**\n\n"
                text += f"💰 **Precio:** {product['precio_formateado']}"
                
                if 'descuento' in product and product['descuento'] > 0:
                    original_price = int(product['precio'] / (1 - product['descuento']/100))
                    text += f" ~~${original_price:,}~~ (¡{product['descuento']}% de descuento!)"
                
                text += f"\n📋 **Descripción:** {product['descripcion']}"
                text += f"\n **Categoría:** {product['categoria']}"
                text += f"\n⏱ **Tiempo de entrega:** {product['tiempo_entrega']}"
                
                if 'caracteristicas' in product:
                    text += "\n\n✨ **Características destacadas:**\n"
                    for caracteristica in product['caracteristicas']:
                        text += f"• {caracteristica}\n"
                
                text += "\n¿Te gustaría saber más detalles o tienes alguna pregunta específica?"
            
            
                self.context_memory[session_id]['last_topic'] = f"product_{key}"


                
                return {
                    'text': text,
                    'quick_replies': ['Ver instalación', 'Agendar medición', 'Otros productos similares']
                }
        
        return None
    
    def _handle_default_response(self, session_id: str) -> Dict[str, Any]:
        """Manejar respuesta por defecto con sugerencias contextuales"""
        responses = self.knowledge.get_responses()['no_entiendo']
        base_response = random.choice(responses)
        
        text = f"{base_response}\n\nPuedo ayudarte con:\n"
        text += "• 🛋️ Información de productos\n"
        text += "• 💰 Precios y ofertas\n"
        text += "• 🔧 Instalación y servicios\n"
        text += "• 🛡️ Garantías\n"
        text += "• 🚚 Envíos y entregas\n"
        text += "• 📞 Información de contacto"
        
        return {
            'text': text,
            'quick_replies': ['Ver catálogo', 'Productos en oferta', 'Contactar asesor']
        }
    
    def _extract_product_from_message(self, message: str) -> str:
        """Extraer nombre de producto del mensaje"""
        products = self.knowledge.get_all_products()
        
        for key, product in products.items():
            if product['nombre'].lower() in message or key in message:
                return key
        
        return None
    
    def get_contextual_suggestions(self, session_id: str, current_topic: str) -> List[str]:
        """Generar sugerencias contextuales basadas en la conversación"""
        suggestions = []
        
        if session_id in self.context_memory:
            last_topic = self.context_memory[session_id].get('last_topic')
            
            if last_topic and 'product_' in last_topic:
                suggestions.extend(['Ver instalación', 'Comparar precios', 'Agendar visita'])
            elif current_topic == 'prices':
                suggestions.extend(['Formas de pago', 'Financiación', 'Descuentos adicionales'])
            elif current_topic == 'installation':
                suggestions.extend(['Costo adicional', 'Tiempo de instalación', 'Garantía instalación'])
        
        return suggestions
    
    def update_context(self, session_id: str, topic: str, data: Any = None):
        """Actualizar contexto de la conversación"""
        if session_id not in self.context_memory:
            self.context_memory[session_id] = {}
        
        self.context_memory[session_id]['last_topic'] = topic
        self.context_memory[session_id]['last_update'] = datetime.now()
        
        if data:
            self.context_memory[session_id]['data'] = data