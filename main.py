import logging
import time
from modules.processing import Processor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

def main():
    logger.info("Iniciando KODA Core...")
    
    # Inicializar el puente de procesamiento
    processor = Processor()
    processor.start()
    
    try:
        # Simulación del flujo de entrada de Nicolás
        # Aquí Nicolás pondría sus frames:
        # processor.input_queue.put({'frame': dummy_frame, 'ocr_text': "Hola"})
        
        logger.info("Sistema corriendo. Presiona Ctrl+C para detener.")
        
        # Bucle principal de la demo
        while True:
            # Aquí esperaríamos a que Thomas consuma de processor.output_queue
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Deteniendo sistema...")
        processor.stop()

if __name__ == "__main__":
    main()
