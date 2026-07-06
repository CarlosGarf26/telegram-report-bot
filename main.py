import datetime
import pytz
import logging
import http.server
import socketserver
import threading
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, Defaults

# 1. Configuración de Logs para monitoreo en la terminal
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. Constantes de Configuración
BOT_TOKEN = "8971854974:AAHvM7H08E3E23Df_hn-jo7MyGM_RMbahwQ"
ZONA_HORARIA = pytz.timezone('America/Mexico_City')

# LISTA DE GRUPOS AUTORIZADOS
GRUPOS_REPORTE_IDS = [-1003967031204, -4531438172, -804848077] 

# 3. Diccionario con tus frases obligatorias
DICCIONARIO_FRASES = {
    "llegada a sucursal": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_3_2026-07-02_12-06-49.jpg"
    ],
    "santander": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_2_2026-07-02_12-06-49.jpg"
    ],
    "con acceso a sucursal": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_4_2026-07-02_12-06-49.jpg",
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_6_2026-07-02_12-06-49.jpg"
    ],
    "adelante": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_7_2026-07-02_12-06-49.jpg"
    ],
    "reporto salida de ": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_9_2026-07-02_12-06-49.jpg"
    ],
    "09:00 am": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_1_2026-07-02_12-06-49.jpg"
    ],
    "09:10 am": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/9.10%20am.PNG"
    ],
    "12:00 hrs": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_8_2026-07-02_12-06-49.jpg"
    ]
}

# ==========================================
# CLASE DEL SERVIDOR WEB (FUERA DE FUNCIONES)
# ==========================================
class HandlerBajoConsumo(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot activo en segundo plano.")

def arrancar_servidor_web():
    puerto = int(os.environ.get("PORT", 8080))
    try:
        server = socketserver.TCPServer(("0.0.0.0", puerto), HandlerBajoConsumo)
        logging.info(f"🌍 Servidor web de contingencia escuchando en puerto {puerto}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"❌ Error al levantar servidor web: {e}")

# ==========================================
# LÓGICA 1: ESCUCHAR FRASES OBLIGATORIAS
# ==========================================
async def monitor_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto_recibido = update.message.text.lower().strip()
    # Normalización completa de acentos
    texto_recibido = texto_recibido.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    for frase_original, urls in DICCIONARIO_FRASES.items():
        frase_normalizada = frase_original.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        if frase_normalizada in texto_recibido:
            logging.info(f"🎯 Frase detectada con éxito: '{frase_original}'")
            for url_imagen in urls:
                try:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url_imagen)
                except Exception as e:
                    logging.error(f"❌ Error al enviar imagen por frase clave: {e}")
            return

# ==========================================
# LÓGICA 2: ENVÍOS AUTOMÁTICOS PROGRAMADOS
# ==========================================
async def enviar_reporte_0900(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_1_2026-07-02_12-06-49.jpg",
                caption="📢 **Que tengas un excelente turno**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ ERROR 09:00: {e}")

async def enviar_reporte_0910(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/9.10%20am.PNG",
                caption="📢 **Que tengas un excelente turno**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ ERROR 09:10: {e}")

async def enviar_reporte_1200(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_8_2026-07-02_12-06-49.jpg",
                caption="📢 **PROHIBIDO**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ ERROR 12:00: {e}")

# ==========================================
# FUNCIÓN PRINCIPAL DE ARRANQUE
# ==========================================
def main():
    # Lanzar el servidor web en un hilo limpio e independiente antes que nada
    hilo_web = threading.Thread(target=arrancar_servidor_web, daemon=True)
    hilo_web.start()

    config_defaults = Defaults(tzinfo=ZONA_HORARIA)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(config_defaults).build()

    # Configuración oficial para producción de lunes a viernes (1 al 5) 0 al 6 (l a d)
    dias_laborales = (0, 1, 2, 3, 4)
    time_0900 = datetime.time(hour=9, minute=00, second=0)
    time_0910 = datetime.time(hour=9, minute=10, second=0)
    time_1200 = datetime.time(hour=12, minute=00, second=0)

    app.job_queue.run_daily(enviar_reporte_0900, time=time_0900, days=dias_laborales)
    app.job_queue.run_daily(enviar_reporte_0910, time=time_0910, days=dias_laborales)
    app.job_queue.run_daily(enviar_reporte_1200, time=time_1200, days=dias_laborales)

    # Manejador de texto sin interferencias
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_mensajes))

    print("🚀 Bot listo con servidor web independiente. Monitoreando...")
    app.run_polling()

if __name__ == '__main__':
    main()
