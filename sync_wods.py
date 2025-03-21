#!/usr/bin/env python3
"""
Script principal que ejecuta los scrapers de CrossfitDB y N8.
"""

import subprocess
import sys
from datetime import datetime

def main():
    print("🏋️ Wodify Box Sync")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)

    # Ejecutar N8 scraper
    print("\n📦 Ejecutando N8 scraper...")
    result_n8 = subprocess.run([sys.executable, "n8.py"], capture_output=True, text=True)
    if result_n8.returncode != 0:
        print("❌ Error al ejecutar N8 scraper:")
        print(result_n8.stderr)
    else:
        print("✅ N8 scraper completado")
        if result_n8.stdout:
            print(result_n8.stdout)

    # Ejecutar CrossfitDB scraper
    print("\n📦 Ejecutando CrossfitDB scraper...")
    result_crossfit = subprocess.run(
        [sys.executable, "crossfitdb.py", "--semana"],
        capture_output=True,
        text=True
    )
    if result_crossfit.returncode != 0:
        print("❌ Error al ejecutar CrossfitDB scraper:")
        print(result_crossfit.stderr)
    else:
        print("✅ CrossfitDB scraper completado")
        if result_crossfit.stdout:
            print(result_crossfit.stdout)

    print("\n" + "=" * 50)
    print("✨ Proceso completado")
    print("=" * 50)

if __name__ == "__main__":
    main()