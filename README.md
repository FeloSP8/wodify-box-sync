# 🏋️‍♂️ Wodify Box Sync

Sincronizador automático de WODs para múltiples boxes de CrossFit. Obtiene, formatea y envía por correo los entrenamientos diarios.

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Características

- 📦 **Multi-Box**: Obtiene WODs de múltiples fuentes:
  - CrossfitDB (API oficial)
  - N8 (API oficial)
- 🎨 **Formato Elegante**: Estilo consistente y profesional
- 📧 **Envío Automático**: Correos separados para cada box
- 📅 **Flexible**: Obtención por día o semana completa
- 🔒 **Seguro**: Manejo seguro de credenciales

## 🚀 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/FeloSP8/wodify-box-sync.git
cd wodify-box-sync
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura tus credenciales:
```bash
cp config.example.py config.py
# Edita config.py con tus datos
```

## 💻 Uso

### Todos los Boxes
```bash
python sync_wods.py
```

### Solo CrossfitDB
```bash
python crossfitdb.py --semana
```

### Solo N8
```bash
python n8.py
```

## 📁 Estructura

```
wodify-box-sync/
├── sync_wods.py     # Script principal
├── crossfitdb.py    # Módulo CrossfitDB
├── n8.py           # Módulo N8
├── config.example.py # Configuración ejemplo
└── requirements.txt  # Dependencias
```

## ⚙️ Configuración

Ejemplo de `config.py`:

```python
# Email
EMAIL_CONFIG = {
    "remitente": "tu_email@gmail.com",
    "contraseña": "tu_contraseña_app",
    "destinatario": "destino@email.com",
    "servidor_smtp": "smtp.gmail.com",
    "puerto_smtp": 587,
    "asunto": "WODs de la semana"
}

# CrossfitDB
CROSSFITDB_CONFIG = {
    "username": "usuario",
    "password": "contraseña",
    "id_user": "123456",
    "id_application": "123456"
}

# N8
N8_CONFIG = {
    "user_id": 123456
}
```

## 📦 Dependencias

- requests>=2.25.1
- beautifulsoup4>=4.9.3
- python-dateutil>=2.8.2

## 🤝 Contribuir

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea tu Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'feat: añadir nueva característica'`)
4. Push al Branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 🙏 Agradecimientos

- CrossfitDB por su API
- N8 por su API
- La comunidad CrossFit