#!/usr/bin/env python3
"""
Script para obtener WODs de N8.
"""

import requests
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

# Importar configuración desde archivo externo
try:
    from config import N8_CONFIG, EMAIL_CONFIG
    print("✅ Configuración cargada correctamente")
except ImportError:
    print("❌ ERROR: No se encuentra el archivo config.py")
    print("Por favor, copia config.example.py a config.py y configura tus datos")
    sys.exit(1)

# Lista de palabras que siempre deben aparecer en mayúsculas
PALABRAS_MAYUSCULAS = [
    "wod", "amrap", "emom", "rx", "tabata", "du", "ygig",
    "c2b", "t2b", "sc", "kbsr",
]

# Lista de palabras que identifican un tipo de entrenamiento
TIPOS_ENTRENAMIENTO = [
    "amrap", "emom", "tabata", "for time", "etabata"
]

def limpiar_html(texto):
    """Limpia el texto HTML preservando la estructura."""
    if not texto:
        return ""
    
    texto = texto.replace("<br>", "\n").replace("<br />", "\n").replace("<br/>", "\n")
    texto = texto.replace("<p>", "").replace("</p>", "\n")
    texto = texto.replace("<h1>", "").replace("</h1>", "\n")
    texto = texto.replace("<h2>", "").replace("</h2>", "\n")
    texto = texto.replace("<h3>", "").replace("</h3>", "\n")
    
    texto = texto.replace("<ul>", "").replace("</ul>", "")
    texto = texto.replace("<ol>", "").replace("</ol>", "")
    texto = texto.replace("<li>", "• ").replace("</li>", "\n")
    
    soup = BeautifulSoup(texto, "html.parser")
    texto_limpio = soup.get_text(separator=" ")
    
    texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_limpio)
    texto_limpio = re.sub(r' +', ' ', texto_limpio)
    
    return texto_limpio.strip()

def aplicar_formato(texto, dia_semana="", fecha_formateada=""):
    """Aplica formato al texto del WOD."""
    lineas = texto.split("\n")
    lineas_formateadas = []
    
    if lineas and re.search(r'^wod\s+', lineas[0].lower()):
        lineas = lineas[1:]
    
    seccion_actual = None
    in_seccion = False
    
    for linea in lineas:
        if not linea.strip():
            lineas_formateadas.append("")
            continue
        
        match_seccion = re.match(r'^([a-zA-Z])[)\.]\s*(.*)$', linea.strip())
        if match_seccion:
            letra, resto = match_seccion.groups()
            seccion_actual = letra.upper()
            in_seccion = True
            linea = f"{seccion_actual}) {resto.strip().upper()}"
            lineas_formateadas.append(linea)
            continue
        
        es_lista = False
        if linea.strip().startswith("•") or re.match(r"^\d+[\.\)]", linea.strip()) or linea.strip().startswith("-"):
            es_lista = True
            if linea.strip().startswith("•"):
                linea = "  " + linea
            elif linea.strip().startswith("-"):
                linea = "  • " + linea[1:].strip()
            else:
                linea = "  • " + re.sub(r"^\d+[\.\)]\s*", "", linea.strip())
        
        palabras = linea.split()
        palabras_formateadas = []
        
        for palabra in palabras:
            palabra_minusculas = palabra.lower()
            solo_letras_min = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]', '', palabra_minusculas)
            
            if solo_letras_min in [p.lower() for p in PALABRAS_MAYUSCULAS]:
                palabra_formateada = palabra.upper()
            elif len(solo_letras_min) == 3:
                palabra_formateada = palabra.upper()
            else:
                if solo_letras_min:
                    match = re.search(r'[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]', palabra)
                    if match:
                        pos = match.start()
                        palabra_formateada = palabra[:pos] + palabra[pos].upper() + palabra[pos+1:].lower()
                    else:
                        palabra_formateada = palabra
                else:
                    palabra_formateada = palabra
            
            palabras_formateadas.append(palabra_formateada)
        
        linea_formateada = ' '.join(palabras_formateadas)
        
        if in_seccion and not es_lista and not linea_formateada.strip().startswith(seccion_actual):
            linea_formateada = "    " + linea_formateada
            
        lineas_formateadas.append(linea_formateada)
    
    texto_formateado = '\n'.join(lineas_formateadas)
    texto_formateado = re.sub(r'\n{3,}', '\n\n', texto_formateado)
    
    return texto_formateado

def formatear_wod_para_correo(contenido):
    """Formatea el contenido del WOD para correo HTML."""
    lineas = contenido.split('\n')
    html_resultado = []
    
    en_seccion = False
    en_lista = False
    seccion_actual = None
    tipo_entrenamiento_actual = None
    
    for linea in lineas:
        linea = linea.strip()
        
        if not linea:
            if en_lista:
                html_resultado.append("</ul>")
                en_lista = False
            continue
        
        match_seccion = re.match(r'^([A-Za-z])[)\.]\s*(.*)$', linea)
        if match_seccion:
            if en_lista:
                html_resultado.append("</ul>")
                en_lista = False
                
            letra, resto = match_seccion.groups()
            seccion_actual = letra.upper()
            en_seccion = True
            tipo_entrenamiento_actual = None
            
            html_resultado.append(f'<div class="section-header">{seccion_actual}) {resto}</div>')
            continue
        
        es_tipo_entrenamiento = False
        for tipo in TIPOS_ENTRENAMIENTO:
            if tipo.upper() in linea.upper() and (linea.upper().startswith(tipo.upper()) or len(linea.split()) <= 5):
                es_tipo_entrenamiento = True
                tipo_entrenamiento_actual = tipo.upper()
                html_resultado.append(f'<div class="workout-type">{linea}</div>')
                break
        
        if es_tipo_entrenamiento:
            continue
        
        es_lista = linea.startswith("  • ") or linea.startswith("• ") or re.match(r'^\d+[\.\)]', linea) or linea.startswith("-")
        
        if es_lista:
            if not en_lista:
                html_resultado.append('<ul class="wod-list">')
                en_lista = True
            
            item_texto = re.sub(r'^(\s*)(•|-|\d+[\.\)])\s*', '', linea)
            html_resultado.append(f'<li>{item_texto}</li>')
            continue
        
        if (en_seccion and linea.startswith("    ")) or tipo_entrenamiento_actual:
            texto_subseccion = linea.strip()
            
            if tipo_entrenamiento_actual:
                html_resultado.append(f'<div class="workout-details">{texto_subseccion}</div>')
            else:
                html_resultado.append(f'<div class="subsection">{texto_subseccion}</div>')
            continue
        
        html_resultado.append(f'<p class="wod-paragraph">{linea}</p>')
    
    if en_lista:
        html_resultado.append("</ul>")
    
    return "\n".join(html_resultado)

def enviar_correo_con_wods(todos_wods, lunes_fmt, viernes_fmt):
    """Envía un correo con los WODs formateados."""
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = EMAIL_CONFIG["remitente"]
        mensaje["To"] = EMAIL_CONFIG["destinatario"]
        mensaje["Subject"] = "N8 - " + f"{EMAIL_CONFIG['asunto']} ({lunes_fmt} - {viernes_fmt})"
        
        cuerpo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>WODs de la semana</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
                
                body {{
                    font-family: 'Roboto', Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f7fa;
                }}
                
                h1 {{
                    color: #2c3e50;
                    font-size: 28px;
                    text-align: center;
                    font-weight: 700;
                    margin-bottom: 30px;
                }}
                
                h2 {{
                    margin: 0;
                    padding: 15px 20px;
                    color: white;
                    font-size: 18px;
                    font-weight: 600;
                    background-color: #2980b9;
                    border-radius: 8px 8px 0 0;
                    letter-spacing: 0.5px;
                }}
                
                .wod-card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.08);
                    margin-bottom: 30px;
                    overflow: hidden;
                }}
                
                .wod-content {{
                    padding: 25px;
                }}
                
                .section-header {{
                    font-weight: 700;
                    font-size: 16px;
                    color: #2c3e50;
                    background-color: #ecf0f1;
                    padding: 8px 12px;
                    margin: 15px 0 10px 0;
                    border-radius: 4px;
                    border-left: 4px solid #3498db;
                }}
                
                .workout-type {{
                    font-weight: 700;
                    font-size: 15px;
                    color: white;
                    background-color: #e74c3c;
                    padding: 6px 10px;
                    margin: 12px 0 8px 15px;
                    border-radius: 3px;
                    display: inline-block;
                }}
                
                .workout-details {{
                    margin: 5px 0 5px 25px;
                    color: #34495e;
                    font-weight: 500;
                    font-size: 15px;
                }}
                
                .subsection {{
                    margin: 8px 0 8px 20px;
                    color: #34495e;
                    font-weight: 500;
                }}
                
                .wod-list {{
                    list-style-type: none;
                    padding-left: 10px;
                    margin: 10px 0 15px 15px;
                }}
                
                .wod-list li {{
                    position: relative;
                    padding-left: 20px;
                    margin-bottom: 8px;
                    color: #34495e;
                }}
                
                .wod-list li:before {{
                    content: "•";
                    position: absolute;
                    left: 0;
                    color: #3498db;
                    font-weight: bold;
                }}
                
                .wod-paragraph {{
                    margin: 10px 0;
                    color: #34495e;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    font-size: 13px;
                    color: #7f8c8d;
                }}
                
                .logo {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                
                .logo span {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #2980b9;
                    letter-spacing: 2px;
                }}
            </style>
        </head>
        <body>
            <div class="logo">
                <span>N8 WODs</span>
            </div>
            <h1>WODs de la semana ({lunes_fmt} - {viernes_fmt})</h1>
        """
        
        if todos_wods:
            for wod in todos_wods:
                titulo = wod["fecha_formateada"]
                if wod["dia_semana"]:
                    titulo = f"{wod['dia_semana']} {titulo}"
                
                cuerpo += f'<div class="wod-card">\n<h2>WOD DEL {titulo}</h2>\n<div class="wod-content">'
                contenido = wod["contenido"]
                contenido_html = formatear_wod_para_correo(contenido)
                cuerpo += f"{contenido_html}</div>\n</div>"
        else:
            cuerpo += '<div class="wod-card">\n<h2>Sin WODs disponibles</h2>\n<div class="wod-content"><p>No se encontraron WODs para esta semana.</p></div>\n</div>'
        
        cuerpo += """
            <div class="footer">
                <p>Generado automáticamente — Wodify Box Sync</p>
            </div>
        </body>
        </html>
        """
        
        mensaje.attach(MIMEText(cuerpo, "html"))
        
        servidor = smtplib.SMTP(EMAIL_CONFIG["servidor_smtp"], EMAIL_CONFIG["puerto_smtp"])
        servidor.starttls()
        servidor.login(EMAIL_CONFIG["remitente"], EMAIL_CONFIG["contraseña"])
        
        texto = mensaje.as_string()
        servidor.sendmail(EMAIL_CONFIG["remitente"], EMAIL_CONFIG["destinatario"], texto)
        
        servidor.quit()
        
        print("✅ Correo enviado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")
        return False

def formatear_fecha(fecha_str):
    """Convierte YYYY-MM-DD a DD/MM/YYYY."""
    try:
        año, mes, dia = fecha_str.split('-')
        return f"{dia}/{mes}/{año}"
    except:
        return fecha_str

def extraer_fecha_del_contenido(contenido):
    """Extrae la fecha del contenido del WOD."""
    patron = r'wod\s+(?:(\w+)\s+)?(\d+)\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?'
    match = re.search(patron, contenido, re.IGNORECASE)
    if match:
        dia_semana, dia, mes, año = match.groups()
        if not año:
            año = str(datetime.now().year)
        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        mes_num = meses.get(mes.lower(), '01')
        dia_zfill = dia.zfill(2)
        return f"{dia}/{mes.capitalize()}/{año}", f"{año}-{mes_num}-{dia_zfill}", dia_semana
    return "", "", ""

def obtener_rango_semana_actual():
    """Obtiene el rango de la semana actual (lunes a viernes)."""
    hoy = datetime.now()
    dias_hasta_lunes = hoy.weekday()
    lunes = hoy - timedelta(days=dias_hasta_lunes)
    viernes = lunes + timedelta(days=4)
    return lunes, viernes

def es_fecha_de_esta_semana(dia, mes):
    """Determina si una fecha está en la semana actual."""
    try:
        dia = int(dia)
        mes_num = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }.get(mes.lower(), 0)
        
        if mes_num == 0:
            return False
        
        lunes, viernes = obtener_rango_semana_actual()
        año_actual = datetime.now().year
        
        fecha_wod = datetime(año_actual, mes_num, dia)
        
        return lunes.date() <= fecha_wod.date() <= viernes.date()
    except (ValueError, AttributeError):
        return False

def valor_ordenamiento(dia_semana):
    """Asigna un valor numérico a cada día para ordenamiento."""
    orden_dias = {
        'Lunes': 1, 
        'Martes': 2, 
        'Miércoles': 3, 'Miercoles': 3,
        'Jueves': 4, 
        'Viernes': 5
    }
    return orden_dias.get(dia_semana, 9)

def main():
    """Función principal."""
    # URL de la API
    api_url = "https://boxn8.aimharder.com/api/activity"
    
    # Parámetros de la solicitud
    params = {
        "timeLineFormat": 0,
        "timeLineContent": 7,
        "userID": N8_CONFIG["user_id"],
        "_": int(datetime.now().timestamp() * 1000)
    }
    
    print("🔄 Obteniendo WODs de N8...")
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        lunes, viernes = obtener_rango_semana_actual()
        lunes_fmt = lunes.strftime("%d/%m/%Y")
        viernes_fmt = viernes.strftime("%d/%m/%Y")
        
        todos_wods = []
        
        for elemento in data.get("elements", []):
            if "TIPOWODs" in elemento and elemento["TIPOWODs"]:
                for tipo_wod in elemento["TIPOWODs"]:
                    notes = tipo_wod.get("notes", "")
                    
                    if notes and re.match(r'^wod\s', notes.lower(), re.IGNORECASE):
                        wod_limpio = limpiar_html(notes)
                        fecha_formateada, fecha_iso, dia_semana_texto = extraer_fecha_del_contenido(wod_limpio)
                        
                        if not fecha_formateada:
                            continue
                        
                        partes = fecha_formateada.split('/')
                        if len(partes) >= 3:
                            dia, mes, _ = partes
                            es_esta_semana = es_fecha_de_esta_semana(dia, mes)
                        else:
                            es_esta_semana = False
                        
                        dia_semana = ""
                        
                        if dia_semana_texto:
                            dia_semana = dia_semana_texto.capitalize()
                        else:
                            lineas = wod_limpio.split('\n')
                            primera_linea = lineas[0] if lineas else ""
                            for dia in ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes']:
                                if dia in primera_linea.lower():
                                    dia_semana = dia.capitalize()
                                    break
                        
                        if not dia_semana and fecha_iso:
                            try:
                                fecha_dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
                                weekday = fecha_dt.weekday()
                                dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][weekday]
                            except:
                                pass
                        
                        if es_esta_semana:
                            wod_formateado = aplicar_formato(wod_limpio, dia_semana, fecha_formateada)
                            
                            todos_wods.append({
                                "fecha_iso": fecha_iso,
                                "fecha_formateada": fecha_formateada,
                                "dia_semana": dia_semana,
                                "contenido": wod_formateado,
                                "valor_orden": valor_ordenamiento(dia_semana),
                                "id": tipo_wod.get("id", "")
                            })
        
        todos_wods.sort(key=lambda x: x["valor_orden"])
        
        print(f"✅ Se encontraron {len(todos_wods)} WODs")
        
        if todos_wods:
            enviar_correo_con_wods(todos_wods, lunes_fmt, viernes_fmt)
        else:
            print("❌ No se encontraron WODs para esta semana")
    
    except requests.RequestException as e:
        print(f"❌ Error en la solicitud: {e}")
    except json.JSONDecodeError:
        print("❌ Error al procesar la respuesta JSON")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()