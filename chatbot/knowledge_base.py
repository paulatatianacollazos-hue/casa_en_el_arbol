import json
from typing import Dict, List, Any

class ChatbotKnowledge:
    """Base de conocimientos del chatbot de Casa en el Árbol"""
    
    def __init__(self):
        self.productos = {
            "closet": {
                "nombre": "Closet",
                "precio": 2400000,
                "precio_formateado": "$2,400,000",
                "descripcion": "Closet grande a la medida para familia",
                "categoria": "Muebles de dormitorio",
                "descuento": 20,
                "caracteristicas": [
                    "Diseño a la medida",
                    "Materiales de alta calidad",
                    "Múltiples compartimientos",
                    "Acabados personalizables"
                ],
                "tiempo_entrega": "5-7 días hábiles"
            },
            "cocina": {
                "nombre": "Cocina",
                "precio": 15000000,
                "precio_formateado": "$15,000,000",
                "descripcion": "Cocina grande familiar con buen espacio",
                "categoria": "Muebles de cocina",
                "caracteristicas": [
                    "Diseño ergonómico",
                    "Amplio espacio de almacenamiento",
                    "Mesón en granito incluido",
                    "Sistema de gavetas con cierre suave"
                ],
                "tiempo_entrega": "10-15 días hábiles"
            },
            "closet_armario": {
                "nombre": "Closet Armario",
                "precio": 4250000,
                "precio_formateado": "$4,250,000",
                "descripcion": "Doble closet armario familiar",
                "categoria": "Muebles de dormitorio",
                "descuento": 15,
                "caracteristicas": [
                    "Doble compartimiento",
                    "Ideal para familias",
                    "Espejo incluido",
                    "Barras de colgar reforzadas"
                ],
                "tiempo_entrega": "7-10 días hábiles"
            },
            "repisas": {
                "nombre": "Repisas",
                "precio": 1850000,
                "precio_formateado": "$1,850,000",
                "descripcion": "Repisas con puerta incluida",
                "categoria": "Organización",
                "caracteristicas": [
                    "Puertas con bisagras de alta calidad",
                    "Múltiples niveles ajustables",
                    "Fácil instalación",
                    "Acabado resistente"
                ],
                "tiempo_entrega": "3-5 días hábiles"
            }
        }
        
        self.servicios = {
            "instalacion": {
                "descripcion": "Ofrecemos servicio de instalación profesional a domicilio",
                "incluye": [
                    "Medición previa",
                    "Transporte del producto",
                    "Montaje completo",
                    "Limpieza del área de trabajo",
                    "Garantía de instalación"
                ],
                "costo": "Varía según tamaño y complejidad",
                "tiempo": "2-4 horas promedio"
            },
            "garantia": {
                "estructura": "2 años",
                "herrajes": "1 año",
                "instalacion": "6 meses",
                "cobertura": [
                    "Defectos de fabricación",
                    "Problemas de estructura",
                    "Desgaste prematuro de herrajes",
                    "Errores de instalación"
                ]
            },
            "envio": {
                "descripcion": "Realizamos envíos a toda la ciudad",
                "tiempo_entrega": "3-7 días hábiles",
                "incluye": [
                    "Seguro de transporte",
                    "Programación flexible",
                    "Notificación de entrega",
                    "Carga y descarga"
                ]
            },
            "medidas": {
                "descripcion": "Servicio de medición personalizada",
                "proceso": [
                    "Visita técnica gratuita",
                    "Toma de medidas exactas",
                    "Diseño 3D del proyecto",
                    "Cotización detallada"
                ]
            }
        }
        
        self.contacto = {
            "horarios": "Lunes a Viernes: 8:00 AM - 6:00 PM, Sábados: 9:00 AM - 4:00 PM",
            "telefono": "+57 300 123 4567",
            "whatsapp": "+57 300 123 4567",
            "email": "info@casaenelarbol.com",
            "direccion": "Calle 123 #45-67, Barrio Los Pinos, Bogotá",
            "redes_sociales": {
                "instagram": "@casaenelarbol",
                "facebook": "Casa en el Árbol Muebles"
            }
        }
        
        self.respuestas_automaticas = {
            "saludos": [
                "¡Hola! 😊 ¿En qué puedo ayudarte hoy?",
                "¡Buen día! Estoy aquí para resolver todas tus dudas sobre nuestros productos.",
                "¡Hola! Me alegra que te pongas en contacto. ¿Qué información necesitas?"
            ],
            "despedidas": [
                "¡Gracias por contactarnos! Que tengas un excelente día. 🌟",
                "Ha sido un placer ayudarte. ¡Esperamos verte pronto! 👋",
                "¡Hasta luego! No dudes en escribirnos cuando necesites algo más."
            ],
            "no_entiendo": [
                "Disculpa, no estoy seguro de entender tu pregunta. ¿Podrías ser más específico?",
                "Me gustaría ayudarte mejor. ¿Puedes reformular tu pregunta?",
                "No he comprendido completamente. ¿Te refieres a información sobre productos, precios, instalación o garantías?"
            ]
        }
        
        self.palabras_clave = {
            "saludos": ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hey', 'saludos', 'buen dia'],
            "despedidas": ['adiós', 'hasta luego', 'chao', 'nos vemos', 'gracias', 'bye', 'adios'],
            "productos": ['producto', 'mueble', 'closet', 'cocina', 'repisa', 'armario', 'catálogo', 'catalogo'],
            "precios": ['precio', 'costo', 'cuanto', 'valor', 'cuánto cuesta', 'cuanto cuesta'],
            "instalacion": ['instalación', 'instalar', 'montar', 'montaje', 'servicio', 'instalacion'],
            "garantia": ['garantía', 'garantias', 'seguridad', 'protección', 'garantia'],
            "envio": ['envío', 'entrega', 'transporte', 'domicilio', 'envio'],
            "populares": ['popular', 'recomendado', 'mejor', 'favorito', 'más vendido', 'mas vendido'],
            "contacto": ['contacto', 'teléfono', 'dirección', 'telefono', 'direccion', 'horario', 'whatsapp'],
            "medidas": ['medida', 'medir', 'dimensión', 'tamaño', 'dimension', 'tamano']
        }
    
    def get_product_info(self, product_name: str) -> Dict:
        """Obtener información de un producto específico"""
        product_key = product_name.lower().replace(' ', '_').replace('ó', 'o')
        return self.productos.get(product_key, {})
    
    def get_all_products(self) -> Dict:
        """Obtener todos los productos"""
        return self.productos
    
    def get_service_info(self, service_name: str) -> Dict:
        """Obtener información de un servicio específico"""
        return self.servicios.get(service_name, {})
    
    def get_all_services(self) -> Dict:
        """Obtener todos los servicios"""
        return self.servicios
    
    def get_contact_info(self) -> Dict:
        """Obtener información de contacto"""
        return self.contacto
    
    def get_keywords(self) -> Dict:
        """Obtener palabras clave para procesamiento"""
        return self.palabras_clave
    
    def get_responses(self) -> Dict:
        """Obtener respuestas automáticas"""
        return self.respuestas_automaticas
    
    def search_products(self, query: str) -> List[Dict]:
        """Buscar productos por término"""
        query = query.lower()
        results = []
        
        for key, product in self.productos.items():
            if (query in product['nombre'].lower() or 
                query in product['descripcion'].lower() or 
                query in product['categoria'].lower()):
                results.append(product)
        
        return results
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Obtener productos por categoría"""
        results = []
        
        for key, product in self.productos.items():
            if category.lower() in product['categoria'].lower():
                results.append(product)
        
        return results
    
    def get_discounted_products(self) -> List[Dict]:
        """Obtener productos con descuento"""
        results = []
        
        for key, product in self.productos.items():
            if 'descuento' in product and product['descuento'] > 0:
                results.append(product)
        
        return results