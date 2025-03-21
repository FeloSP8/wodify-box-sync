#!/usr/bin/env python3
"""
Script para obtener WODs de CrossfitDB.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Importar configuración desde archivo externo
try:
    from config import CROSSFITDB_CONFIG, EMAIL_CONFIG
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
    
    lineas = []
    for linea in texto_limpio.split('\n'):
        linea = linea.strip()
        if linea:
            linea = re.sub(r'^[•·-]|\d+[\.\)]|\s*[-–—]\s*', '', linea).strip()
            if linea:
                lineas.append(linea)
    
    texto_limpio = '\n'.join(lineas)
    texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_limpio)
    texto_limpio = re.sub(r' +', ' ', texto_limpio)
    
    return texto_limpio.strip()

def es_tipo_entrenamiento(linea):
    """Determina si una línea indica un tipo de entrenamiento."""
    linea_lower = linea.lower()
    
    # Lista de tipos de entrenamiento exactos
    tipos_exactos = [
        "amrap", "emom", "tabata", "etabata", "for time",
        "buy in", "cash out", "strength", "skill", "metcon",
        "wod", "warm up", "core", "accessory"
    ]
    
    # Lista de frases que indican tipo de entrenamiento
    frases_tipo = [
        "for time", "every", "rounds", "reps", "minutes",
        "complete", "perform", "work", "rest"
    ]
    
    # Verificar tipos exactos
    for tipo in tipos_exactos:
        if linea_lower == tipo:
            return True
    
    # Verificar frases
    for frase in frases_tipo:
        if frase in linea_lower and len(linea.split()) <= 5:
            return True
    
    return False

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
        
        es_tipo_entrenamiento = es_tipo_entrenamiento(linea)
        if es_tipo_entrenamiento:
            tipo_entrenamiento_actual = linea.upper()
            html_resultado.append(f'<div class="workout-type">{linea}</div>')
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
        mensaje["Subject"] = "CrossfitDB - " + f"{EMAIL_CONFIG['asunto']} ({lunes_fmt} - {viernes_fmt})"
        
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
                <span>CrossfitDB WODs</span>
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

def obtener_rango_semana_actual():
    """Obtiene el rango de la semana actual (lunes a viernes)."""
    hoy = datetime.now()
    dias_hasta_lunes = hoy.weekday()
    lunes = hoy - timedelta(days=dias_hasta_lunes)
    viernes = lunes + timedelta(days=4)
    return lunes, viernes

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
    api_url = "https://crossfitdb.com/api/v1/wods"
    
    # Obtener el rango de fechas de la semana actual
    lunes, viernes = obtener_rango_semana_actual()
    lunes_fmt = lunes.strftime("%d/%m/%Y")
    viernes_fmt = viernes.strftime("%d/%m/%Y")
    
    # Parámetros de la solicitud
    params = {
        "username": CROSSFITDB_CONFIG["username"],
        "password": CROSSFITDB_CONFIG["password"],
        "user_id": CROSSFITDB_CONFIG["user_id"],
        "app_id": CROSSFITDB_CONFIG["app_id"],
        "start_date": lunes.strftime("%Y-%m-%d"),
        "end_date": viernes.strftime("%Y-%m-%d")
    }
    
    print("🔄 Obteniendo WODs de CrossfitDB...")
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        todos_wods = []
        
        for wod in data.get("wods", []):
            fecha_iso = wod.get("date", "")
            fecha_formateada = formatear_fecha(fecha_iso)
            
            try:
                fecha_dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
                weekday = fecha_dt.weekday()
                dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][weekday]
            except:
                dia_semana = ""
            
            contenido = wod.get("content", "")
            if contenido:
                contenido_limpio = limpiar_html(contenido)
                
                todos_wods.append({
                    "fecha_iso": fecha_iso,
                    "fecha_formateada": fecha_formateada,
                    "dia_semana": dia_semana,
                    "contenido": contenido_limpio,
                    "valor_orden": valor_ordenamiento(dia_semana),
                    "id": wod.get("id", "")
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