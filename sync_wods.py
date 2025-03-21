#!/usr/bin/env python3
"""
Script unificado para obtener WODs de CrossfitDB y N8.
"""

import sys
import os
from datetime import datetime
import traceback

def ejecutar_script(nombre_script):
    """Ejecuta un script Python y maneja sus errores."""
    try:
        print(f"\n🔄 Ejecutando {nombre_script}...")
        __import__(nombre_script.replace(".py", ""))
        return True
    except Exception as e:
        print(f"❌ Error al ejecutar {nombre_script}: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Función principal."""
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Lista de scripts a ejecutar
    scripts = ["crossfitdb.py", "n8.py"]
    
    # Ejecutar cada script
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ No se encuentra el script {script}")
            continue
        
        ejecutar_script(script)
        print("-" * 50)

if __name__ == "__main__":
    main()