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
GRUPOS_REPORTE_IDS = [-1003967031204, -4531438172, -804848077, -1526410573, -5121107658, -4967561577, -4021483068, -4066598135, -867815276, -5126666888, -5173573157, -1775181484, -5504914564, -1895852913] 

# ID ESPECIAL CON LÍMITE DE UN ENVÍO AL DÍA
ID_LIMITADO = -4030049034

# Registro en memoria para el grupo limitado
REGISTRO_ENVIOS_DIARIOS = set()

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
    "salida de sucursal": [
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
# LÓGICA 1: ESCUCHAR FRASES OBLIGATORIAS
# ==========================================
async def monitor_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    texto_recibido = update.message.text.lower().strip()
    texto_recibido = texto_recibido.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    for frase_original, urls in DICCIONARIO_FRASES.items():
        frase_normalizada = frase_original.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        if frase_normalizada in texto_recibido:
            # 🛡️ FILTRO DE LÍMITE DIARIO PARA EL ID ESPECIAL
            if chat_id == ID_LIMITADO:
                fecha_hoy = datetime.datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d")
                if fecha_hoy in REGISTRO_ENVIOS_DIARIOS:
                    logging.info(f"🔒 Bloqueado: El grupo especial {ID_LIMITADO} ya usó su envío del día ({fecha_hoy}).")
                    return
                else:
                    REGISTRO_ENVIOS_DIARIOS.add(fecha_hoy)

            logging.info(f"🎯 Frase detectada en chat {chat_id}: '{frase_original}'")
            for url_imagen in urls:
                try:
                    await context.bot.send_photo(chat_id=chat_id, photo=url_imagen)
                except Exception as e:
                    logging.error(f"❌ Error al enviar imagen por frase clave: {e}")
            return

# ==========================================
# LÓGICA 2: ENVÍOS AUTOMÁTICOS PROGRAMADOS (VALIDACIÓN DE CDMX)
# ==========================================
async def enviar_reporte_0900(context: ContextTypes.DEFAULT_TYPE):
    dia_actual = datetime.datetime.now(ZONA_HORARIA).weekday()
    if dia_actual > 4: # 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana en CDMX.")
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
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana en CDMX.")
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
        logging.info("🛡️ Candado activado: Bloqueando envío por ser fin de semana en CDMX.")
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

    config_defaults = Defaults(tzinfo=ZONA_HORARIA)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(config_defaults).build()

    todos_los_dias = (0, 1, 2, 3, 4, 5, 6)
    
    # HORARIOS OFICIALES RESTABLECIDOS (09:00, 09:10, 12:00)
    time_0900 = datetime.time(hour=9, minute=0, second=0)
    time_0910 = datetime.time(hour=9, minute=10, second=0)
    time_1200 = datetime.time(hour=12, minute=0, second=0)

    config_tolerancia = {"misfire_grace_time": 300}

    # Registro en la cola de tareas diarias
    app.job_queue.run_daily(enviar_reporte_0900, time=time_0900, days=todos_los_dias, job_kwargs=config_tolerancia)
    app.job_queue.run_daily(enviar_reporte_0910, time=time_0910, days=todos_los_dias, job_kwargs=config_tolerancia)
    app.job_queue.run_daily(enviar_reporte_1200, time=time_1200, days=todos_los_dias, job_kwargs=config_tolerancia)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_mensajes))

    logging.info("🤖 Iniciando Polling con filtro diario estricto de CDMX...")
    app.run_polling()

if __name__ == '__main__':
    main()
