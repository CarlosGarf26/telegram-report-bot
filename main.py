import datetime
import pytz
import logging
import http.server
import threading
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, Defaults

# 1. Configuración de Logs para monitoreo en la terminal
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. Constantes de Configuración
BOT_TOKEN = "8971854974:AAHvM7H08E3E23Df_hn-jo7MyGM_RMbahwQ"
ZONA_HORARIA = pytz.timezone('America/Mexico_City')

# LISTA DE GRUPOS AUTORIZADOS (12 IDs actualizados)
GRUPOS_REPORTE_IDS = [-1003967031204, -4531438172, -804848077, -1526410573, -5121107658, -4967561577, -4021483068, -4066598135, -867815276, -5126666888, -5173573157, -1775181484, -5504914564, -4021483068] 

# 3. Diccionario con tus frases obligatorias
DICCIONARIO_FRASES = {
    "llegada a sucursal": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_3_2026-07-02_12-06-49.jpg",
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_2026-07-07_16-24-27.jpg"
    ],
    "llegando a sucursal": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_3_2026-07-02_12-06-49.jpg",
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_2026-07-07_16-24-27.jpg"
    ],
    "santander": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_2_2026-07-02_12-06-49.jpg"
    ],
    "con acceso a sucursal": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_4_2026-07-02_12-06-49.jpg",
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_6_2026-07-02_12-06-49.jpg"
    ],
    "adelante": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_7_2026-07-02_12-06-49.jpg",
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/adelante2.jpg"
    ],
    "reporto salida de ": [
        "https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_9_2026-07-02_12-06-49.jpg"
    ],
    "me retiro de ": [
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
# CLASE DEL SERVIDOR WEB MODERNO
# ==========================================
class HandlerBajoConsumo(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot activo en segundo plano de forma exitosa.")

    def log_message(self, format, *args):
        return

def arrancar_servidor_web():
    puerto = int(os.environ.get("PORT", 10000))
    try:
        server = http.server.HTTPServer(("0.0.0.0", puerto), HandlerBajoConsumo)
        logging.info(f"🌍 Servidor de contingencia escuchando en puerto {puerto}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"❌ Error al levantar servidor web: {e}")

# ==========================================
# LÓGICA 1: ESCUCHAR FRASES OBLIGATORIAS (Detección Flexible)
# ==========================================
async def monitor_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto_recibido = update.message.text.lower().strip()
    texto_recibido = texto_recibido.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    for frase_original, urls in DICCIONARIO_FRASES.items():
        frase_normalizada = frase_original.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # AJUSTE INTELIGENTE: Evalúa si la frase clave completa viene adentro del mensaje enviado
        if frase_normalizada in texto_recibido:
            logging.info(f"🎯 Frase detectada en el texto: '{frase_original}'")
            for url_imagen in urls:
                try:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url_imagen)
                except Exception as e:
                    logging.error(f"❌ Error al enviar imagen por frase clave: {e}")
            return

# ==========================================
# LÓGICA 2: ENVÍOS AUTOMÁTICOS PROGRAMADOS (LUNES A VIERNES)
# ==========================================
async def enviar_reporte_0900(context: ContextTypes.DEFAULT_TYPE):
    dia_actual = datetime.datetime.now(ZONA_HORARIA).weekday()
    if dia_actual > 4:
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana.")
        return

    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_1_2026-07-02_12-06-49.jpg",
                caption="📢 **Que tengas un excelente turno**",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1.5)
        except Exception as e:
            logging.error(f"❌ ERROR EN GRUPO {chat_id_actual}: {e}")

async def enviar_reporte_0910(context: ContextTypes.DEFAULT_TYPE):
    dia_actual = datetime.datetime.now(ZONA_HORARIA).weekday()
    if dia_actual > 4:
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana.")
        return

    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/9.10%20am.PNG",
                caption="📢 **Que tengas un excelente turno**",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1.5)
        except Exception as e:
            logging.error(f"❌ ERROR EN GRUPO {chat_id_actual}: {e}")

async def enviar_reporte_1200(context: ContextTypes.DEFAULT_TYPE):
    dia_actual = datetime.datetime.now(ZONA_HORARIA).weekday()
    if dia_actual > 4:
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana.")
        return

    for chat_id_actual in GRUPOS_REPORTE_IDS:
        try:
            await context.bot.send_photo(
                chat_id=chat_id_actual,
                photo="https://raw.githubusercontent.com/CarlosGarf26/bot-telegram-assets/main/photo_8_2026-07-02_12-06-49.jpg",
                caption="📢 **PROHIBIDO**",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1.5)
        except Exception as e:
            logging.error(f"❌ ERROR EN GRUPO {chat_id_actual}: {e}")

# ==========================================
# FUNCIÓN PRINCIPAL DE ARRANQUE
# ==========================================
def main():
    hilo_web = threading.Thread(target=arrancar_servidor_web, daemon=True)
    hilo_web.start()

    # 1. Aplicamos la zona horaria de forma GLOBAL a todo el bot.
    config_defaults = Defaults(tzinfo=ZONA_HORARIA)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(config_defaults).build()

    dias_laborales = (0, 1, 2, 3, 4)
    
    # 2. SOLUCIÓN AL BUG: Declaramos horas limpias sin tzinfo para que hereden el config_defaults correctamente
    time_0900 = datetime.time(hour=9, minute=0, second=0)
    time_0910 = datetime.time(hour=9, minute=10, second=0)
    time_1200 = datetime.time(hour=12, minute=0, second=0)

    # Dejamos el margen saludable de 5 minutos por la carga compartida de CPU en Render
    config_tolerancia = {"misfire_grace_time": 300}

    # Registro final de las tareas diarias en el JobQueue
    app.job_queue.run_daily(enviar_reporte_0900, time=time_0900, days=dias_laborales, job_kwargs=config_tolerancia)
    app.job_queue.run_daily(enviar_reporte_0910, time=time_0910, days=dias_laborales, job_kwargs=config_tolerancia)
    app.job_queue.run_daily(enviar_reporte_1200, time=time_1200, days=dias_laborales, job_kwargs=config_tolerancia)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_mensajes))

    logging.info("🤖 Iniciando Polling con sincronización horaria absoluta...")
    app.run_polling()

if __name__ == '__main__':
    main()
