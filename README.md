# 🛍️ Tienda Online Internacional

Tienda e-commerce profesional con Flask — Colombia · USA · España

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![SQLite](https://img.shields.io/badge/DB-SQLite%20→%20PostgreSQL-orange)

---

## ✨ Características

- 🎨 Diseño premium dark/light mode
- 🛒 Carrito con localStorage
- 📦 Panel admin completo
- 🌍 Servicio de importación Colombia ↔ USA ↔ España
- 📱 100% responsive
- 💬 WhatsApp flotante integrado
- 🔍 SEO básico
- 🚀 Listo para producción

---

## 🚀 Instalación Local

### 1. Clonar el proyecto
```bash
git clone https://github.com/tuusuario/tienda-online.git
cd tienda-online
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus datos
```

### 5. Ejecutar
```bash
python app.py
```

Abre `http://localhost:5000` en tu navegador.

**Admin:** `http://localhost:5000/admin`
- Usuario: `admin` (o el que definas en `.env`)
- Contraseña: `admin123`

---

## 📁 Estructura del Proyecto

```
tienda/
├── app.py                  # Aplicación Flask principal
├── requirements.txt        # Dependencias Python
├── .env                    # Variables de entorno (no subir a git)
├── .env.example            # Plantilla pública
├── Procfile                # Para Railway/Render
├── runtime.txt             # Versión de Python
├── README.md               # Esta documentación
│
├── static/
│   ├── css/
│   │   ├── main.css        # Estilos del frontend
│   │   └── admin.css       # Estilos del panel admin
│   ├── js/
│   │   ├── main.js         # JavaScript del frontend
│   │   └── admin.js        # JavaScript del admin
│   └── images/             # Imágenes estáticas del sitio
│
├── templates/
│   ├── base.html           # Layout base
│   ├── index.html          # Página principal
│   ├── products.html       # Catálogo
│   ├── product_detail.html # Detalle de producto
│   ├── imports.html        # Servicio de importación
│   ├── about.html          # Quiénes somos
│   ├── contact.html        # Contacto
│   └── admin/
│       ├── base.html       # Layout admin
│       ├── login.html      # Login admin
│       ├── dashboard.html  # Dashboard
│       ├── products.html   # Listado productos
│       ├── product_form.html  # Crear/editar producto
│       ├── categories.html    # Categorías
│       ├── category_form.html
│       ├── orders.html
│       ├── order_detail.html
│       ├── imports.html    # Solicitudes de importación
│       ├── banners.html
│       ├── banner_form.html
│       └── settings.html
│
├── uploads/                # Imágenes subidas (auto-creado)
│   ├── products/
│   ├── categories/
│   ├── banners/
│   └── import_requests/
│
└── database/               # Base de datos (auto-creado)
    └── tienda.db
```

---

## ⚙️ Configuración (.env)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta Flask | cadena aleatoria larga |
| `ADMIN_USERNAME` | Usuario admin | admin |
| `ADMIN_PASSWORD` | Contraseña admin | tu_password |
| `DATABASE_URL` | URL de base de datos | sqlite:///database/tienda.db |
| `WHATSAPP_NUMBER` | Número WhatsApp | 573001234567 |
| `SITE_NAME` | Nombre del sitio | Mi Tienda |

---

## 🌐 Despliegue en Producción

### Railway (recomendado — gratis)
1. Sube el proyecto a GitHub
2. Ve a [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Agrega las variables de entorno desde `.env.example`
4. Railway detecta el `Procfile` automáticamente

### Render
1. [render.com](https://render.com) → New Web Service
2. Conecta tu repositorio GitHub
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Agrega variables de entorno

### PythonAnywhere
1. Sube archivos via SFTP o git
2. Crea Web App → Flask
3. Apunta WSGI a `app.py`
4. Instala dependencias en el bash

### VPS Linux (DigitalOcean / Hostinger)
```bash
# Instalar Nginx + Gunicorn
sudo apt update && sudo apt install nginx python3-pip

# Clonar y configurar
git clone ... && cd tienda
pip install -r requirements.txt
cp .env.example .env && nano .env

# Ejecutar con Gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app

# Configurar Nginx como proxy reverso
# (ver guía en /docs/nginx.conf.example)
```

---

## 🗄️ Migrar a PostgreSQL

1. Instalar driver: `pip install psycopg2-binary`
2. En `.env` cambiar:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```
3. El app detecta automáticamente el tipo de DB

---

## 🛠️ Agregar Pasarelas de Pago

El sistema está preparado para integrar:
- **Stripe** — Internacional (tarjetas)
- **PayPal** — Internacional
- **Wompi** — Colombia
- **Nequi** — Colombia
- **Bizum** — España

Busca los comentarios `# TODO: PAGO` en `app.py` para los puntos de integración.

---

## 📋 Personalización Rápida

### Cambiar colores
Editar las variables CSS en `static/css/main.css`:
```css
:root {
  --primary: #0f2557;    /* Azul oscuro */
  --accent:  #1d4ed8;    /* Azul eléctrico */
  --gold:    #c9a84c;    /* Dorado */
}
```

### Cambiar fuentes
En `templates/base.html`, edita el import de Google Fonts.

### Agregar categorías
Desde el panel admin → Categorías → Nueva categoría.

---

## 🔒 Seguridad

- [x] CSRF protection en formularios
- [x] Sesiones seguras con SECRET_KEY
- [x] Validación de tipos de archivo en uploads
- [x] Nombres de archivo saneados con Werkzeug
- [ ] Rate limiting (añadir Flask-Limiter en producción)
- [ ] HTTPS (configurar en el hosting)

---

## 📄 Licencia

MIT — Libre para uso personal y comercial.

---

**Hecho con ❤️ para comerciantes entre Colombia 🇨🇴 · USA 🇺🇸 · España 🇪🇸**
