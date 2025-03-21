# Configuración del correo electrónico
EMAIL_CONFIG = {
    "remitente": "tu_email@gmail.com",    # Tu correo Gmail
    "contraseña": "xxxx xxxx xxxx xxxx",  # Contraseña de aplicación de Gmail
    "destinatario": "destino@email.com",  # Correo que recibirá los WODs
    "servidor_smtp": "smtp.gmail.com",     # Servidor SMTP (Gmail)
    "puerto_smtp": 587,                    # Puerto SMTP (TLS)
    "asunto": "WODs de la semana"         # Asunto del correo
}

# Configuración para CrossfitDB
CROSSFITDB_CONFIG = {
    "username": "tu_usuario",             # Tu usuario de CrossfitDB
    "password": "tu_contraseña",          # Tu contraseña de CrossfitDB
    "id_user": "123456",                  # Tu ID de usuario
    "id_application": "123456"            # ID de la aplicación
}

# Configuración para N8
N8_CONFIG = {
    "user_id": 123456                     # Tu ID de usuario en N8
}