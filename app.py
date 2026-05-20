"""
╔══════════════════════════════════════════════════════════════════╗
║          TIENDA ONLINE INTERNACIONAL - FLASK APP                ║
║    Colombia · Estados Unidos · España                           ║
║    Versión 1.0 | Preparado para producción                      ║
╚══════════════════════════════════════════════════════════════════╝

CÓMO EJECUTAR:
    pip install -r requirements.txt
    python app.py

PANEL ADMIN:
    URL: /admin
    Usuario: admin
    Contraseña: admin123  (CAMBIAR en .env antes de producción)

ESTRUCTURA:
    app.py              → Aplicación principal Flask
    models.py           → Modelos de base de datos (SQLAlchemy)
    templates/          → Plantillas HTML (Jinja2)
    static/             → CSS, JS, imágenes estáticas
    uploads/            → Imágenes subidas por admin/usuarios
    database/           → Archivo SQLite (desarrollo)
"""

import os
import uuid
import json
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ─── Cargar variables de entorno ────────────────────────────────────────────
load_dotenv()

# ─── Inicializar Flask ───────────────────────────────────────────────────────
app = Flask(__name__)

# ─── Configuración principal ─────────────────────────────────────────────────
app.config.update(
    # Seguridad
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),

    # Base de datos: SQLite en desarrollo, fácil migrar a PostgreSQL/MySQL
    # Para PostgreSQL: postgresql://user:pass@host/dbname
    # Para MySQL:      mysql+pymysql://user:pass@host/dbname
    SQLALCHEMY_DATABASE_URI=os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'tienda.db')}"
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,

    # Subida de archivos
    UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB máximo
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'webp'},

    # Admin
    ADMIN_USERNAME=os.getenv('ADMIN_USERNAME', 'admin'),
    ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD', 'admin123'),
)

# ─── Inicializar base de datos ───────────────────────────────────────────────
db = SQLAlchemy(app)

# ─── Asegurar que existan las carpetas necesarias ───────────────────────────
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════
#                           MODELOS DE BASE DE DATOS
# ════════════════════════════════════════════════════════════════════════════

class Category(db.Model):
    """Categorías de productos (Hogar, Tecnología, Moda, etc.)"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    icon = db.Column(db.String(50))       # Emoji o clase de icono
    color = db.Column(db.String(20))      # Color de acento para la categoría
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'slug': self.slug,
            'description': self.description, 'image': self.image,
            'icon': self.icon, 'color': self.color,
            'product_count': len([p for p in self.products if p.is_active])
        }


class Product(db.Model):
    """Productos de la tienda con soporte para múltiples imágenes"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)    # Precio tachado / oferta
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_on_sale = db.Column(db.Boolean, default=False)

    # Imágenes: guardadas como JSON array → ["img1.jpg", "img2.jpg"]
    images_json = db.Column(db.Text, default='[]')

    # SEO
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(300))

    # Origen / envío
    origin_country = db.Column(db.String(50))   # CO, US, ES
    weight = db.Column(db.Float)                  # kg

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def images(self):
        try:
            return json.loads(self.images_json or '[]')
        except Exception:
            return []

    @images.setter
    def images(self, value):
        self.images_json = json.dumps(value)

    @property
    def main_image(self):
        imgs = self.images
        return imgs[0] if imgs else None

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int((1 - self.price / self.original_price) * 100)
        return 0

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'slug': self.slug,
            'description': self.description,
            'short_description': self.short_description,
            'price': self.price, 'original_price': self.original_price,
            'stock': self.stock, 'images': self.images,
            'main_image': self.main_image, 'is_active': self.is_active,
            'is_featured': self.is_featured, 'discount_percent': self.discount_percent,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None
        }


class Banner(db.Model):
    """Banners del hero de la página principal"""
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(300))
    button_text = db.Column(db.String(50))
    button_url = db.Column(db.String(200))
    image = db.Column(db.String(255))
    bg_color = db.Column(db.String(20), default='#0a0a0f')
    text_color = db.Column(db.String(20), default='#ffffff')
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class ImportRequest(db.Model):
    """Solicitudes de importación internacional"""
    __tablename__ = 'import_requests'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    origin_country = db.Column(db.String(5))    # CO, US, ES
    destination_country = db.Column(db.String(5))
    product_url = db.Column(db.String(500))
    product_description = db.Column(db.Text)
    budget = db.Column(db.String(100))
    image = db.Column(db.String(255))           # Foto del producto deseado
    status = db.Column(db.String(50), default='pending')   # pending, quoted, accepted, rejected
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    """Pedidos de la tienda (preparado para pasarela de pago)"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True)
    customer_name = db.Column(db.String(200))
    customer_email = db.Column(db.String(200))
    customer_phone = db.Column(db.String(50))
    shipping_address = db.Column(db.Text)
    items_json = db.Column(db.Text, default='[]')   # [{product_id, name, price, qty}]
    subtotal = db.Column(db.Float, default=0)
    shipping_cost = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def items(self):
        try:
            return json.loads(self.items_json or '[]')
        except Exception:
            return []


class SiteSettings(db.Model):
    """Configuración global del sitio (textos, redes sociales, etc.)"""
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))

    @staticmethod
    def get(key, default=''):
        s = SiteSettings.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = SiteSettings.query.filter_by(key=key).first()
        if s:
            s.value = value
        else:
            s = SiteSettings(key=key, value=value)
            db.session.add(s)
        db.session.commit()


# ════════════════════════════════════════════════════════════════════════════
#                           UTILIDADES
# ════════════════════════════════════════════════════════════════════════════

def allowed_file(filename):
    """Verifica que el archivo sea una imagen válida"""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])


def save_uploaded_file(file, subfolder='products'):
    """Guarda un archivo subido y retorna el nombre único generado"""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        return f"{subfolder}/{filename}"
    return None


def login_required(f):
    """Decorador para rutas protegidas del panel admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Por favor inicia sesión para acceder al panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def slugify(text):
    """Genera un slug limpio a partir de texto"""
    import re
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ════════════════════════════════════════════════════════════════════════════
#                           RUTAS PÚBLICAS
# ════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Página principal de la tienda"""
    featured_products = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    sale_products = Product.query.filter_by(is_active=True, is_on_sale=True).limit(6).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.sort_order).all()

    # Si no hay banners, crear uno por defecto
    if not banners:
        default_banners = [
            {'title': 'Descubre el Mundo', 'subtitle': 'Importaciones desde Colombia, USA y España con garantía total', 'button_text': 'Ver Colección', 'button_url': '/productos'},
            {'title': 'Tecnología Premium', 'subtitle': 'Los mejores gadgets y accesorios tech a tu alcance', 'button_text': 'Explorar Tech', 'button_url': '/categoria/tecnologia'},
            {'title': 'Importación Fácil', 'subtitle': 'Trae cualquier producto del mundo directamente a tu puerta', 'button_text': 'Solicitar Importación', 'button_url': '/importaciones'},
        ]
        banners = [type('Banner', (), b)() for b in default_banners]

    return render_template('index.html',
        featured_products=featured_products,
        sale_products=sale_products,
        categories=categories,
        banners=banners,
        settings=get_site_settings()
    )


@app.route('/productos')
def products():
    """Listado de todos los productos con filtros"""
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('categoria')
    search = request.args.get('q', '').strip()
    sort = request.args.get('orden', 'newest')

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search:
        query = query.filter(
            Product.name.ilike(f'%{search}%') |
            Product.description.ilike(f'%{search}%')
        )

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    products_page = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    active_category = Category.query.filter_by(slug=category_slug).first() if category_slug else None

    return render_template('products.html',
        products=products_page,
        categories=categories,
        active_category=active_category,
        search=search,
        sort=sort,
        settings=get_site_settings()
    )


@app.route('/producto/<slug>')
def product_detail(slug):
    """Detalle de un producto"""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter_by(
        category_id=product.category_id, is_active=True
    ).filter(Product.id != product.id).limit(4).all()

    return render_template('product_detail.html',
        product=product,
        related_products=related,
        settings=get_site_settings()
    )


@app.route('/categoria/<slug>')
def category(slug):
    """Página de categoría"""
    return redirect(url_for('products', categoria=slug))


@app.route('/importaciones')
def imports():
    """Página de servicio de importación internacional"""
    return render_template('imports.html', settings=get_site_settings())


@app.route('/importaciones/solicitar', methods=['POST'])
def submit_import():
    """Procesa formulario de solicitud de importación"""
    try:
        image_path = None
        if 'product_image' in request.files:
            f = request.files['product_image']
            image_path = save_uploaded_file(f, 'import_requests')

        req = ImportRequest(
            full_name=request.form.get('full_name', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            origin_country=request.form.get('origin_country', ''),
            destination_country=request.form.get('destination_country', ''),
            product_url=request.form.get('product_url', '').strip(),
            product_description=request.form.get('product_description', '').strip(),
            budget=request.form.get('budget', '').strip(),
            image=image_path,
        )
        db.session.add(req)
        db.session.commit()
        flash('✅ Tu solicitud fue enviada. Te contactaremos en 24-48 horas.', 'success')
    except Exception as e:
        flash(f'❌ Error al enviar la solicitud: {str(e)}', 'error')

    return redirect(url_for('imports'))


@app.route('/nosotros')
def about():
    return render_template('about.html', settings=get_site_settings())


@app.route('/contacto')
def contact():
    return render_template('contact.html', settings=get_site_settings())


# ─── Servir archivos subidos ─────────────────────────────────────────────────
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── API para carrito (JavaScript) ───────────────────────────────────────────
@app.route('/api/products')
def api_products():
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([p.to_dict() for p in products])


@app.route('/api/product/<int:product_id>')
def api_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


# ════════════════════════════════════════════════════════════════════════════
#                           PANEL ADMINISTRATIVO
# ════════════════════════════════════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if (username == app.config['ADMIN_USERNAME'] and
                password == app.config['ADMIN_PASSWORD']):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('¡Bienvenido al panel de administración!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    stats = {
        'total_products': Product.query.count(),
        'active_products': Product.query.filter_by(is_active=True).count(),
        'total_categories': Category.query.count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'import_requests': ImportRequest.query.filter_by(status='pending').count(),
        'recent_orders': Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        'recent_imports': ImportRequest.query.order_by(ImportRequest.created_at.desc()).limit(5).all(),
    }
    return render_template('admin/dashboard.html', stats=stats)


# ─── Gestión de Productos ─────────────────────────────────────────────────────

@app.route('/admin/productos')
@login_required
def admin_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/products.html', products=products)


@app.route('/admin/productos/nuevo', methods=['GET', 'POST'])
@login_required
def admin_product_new():
    categories = Category.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            slug = slugify(name)

            # Asegurar slug único
            base_slug = slug
            counter = 1
            while Product.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            product = Product(
                name=name,
                slug=slug,
                description=request.form.get('description', ''),
                short_description=request.form.get('short_description', ''),
                price=float(request.form.get('price', 0)),
                original_price=float(request.form.get('original_price') or 0) or None,
                stock=int(request.form.get('stock', 0)),
                sku=request.form.get('sku', '').strip(),
                category_id=int(request.form.get('category_id') or 0) or None,
                is_active=request.form.get('is_active') == 'on',
                is_featured=request.form.get('is_featured') == 'on',
                is_on_sale=request.form.get('is_on_sale') == 'on',
                origin_country=request.form.get('origin_country', ''),
                meta_title=request.form.get('meta_title', ''),
                meta_description=request.form.get('meta_description', ''),
            )

            # Procesar múltiples imágenes subidas
            images = []
            files = request.files.getlist('images')
            for f in files:
                path = save_uploaded_file(f, 'products')
                if path:
                    images.append(path)
            product.images = images

            db.session.add(product)
            db.session.commit()
            flash(f'✅ Producto "{name}" creado exitosamente.', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')

    return render_template('admin/product_form.html', product=None, categories=categories)


@app.route('/admin/productos/<int:product_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        try:
            product.name = request.form.get('name', '').strip()
            product.description = request.form.get('description', '')
            product.short_description = request.form.get('short_description', '')
            product.price = float(request.form.get('price', 0))
            product.original_price = float(request.form.get('original_price') or 0) or None
            product.stock = int(request.form.get('stock', 0))
            product.sku = request.form.get('sku', '').strip()
            product.category_id = int(request.form.get('category_id') or 0) or None
            product.is_active = request.form.get('is_active') == 'on'
            product.is_featured = request.form.get('is_featured') == 'on'
            product.is_on_sale = request.form.get('is_on_sale') == 'on'
            product.origin_country = request.form.get('origin_country', '')
            product.meta_title = request.form.get('meta_title', '')
            product.meta_description = request.form.get('meta_description', '')

            # Agregar nuevas imágenes
            current_images = product.images
            files = request.files.getlist('images')
            for f in files:
                path = save_uploaded_file(f, 'products')
                if path:
                    current_images.append(path)

            # Eliminar imágenes marcadas
            remove_images = request.form.getlist('remove_images')
            current_images = [img for img in current_images if img not in remove_images]
            product.images = current_images

            db.session.commit()
            flash(f'✅ Producto actualizado correctamente.', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')

    return render_template('admin/product_form.html', product=product, categories=categories)


@app.route('/admin/productos/<int:product_id>/eliminar', methods=['POST'])
@login_required
def admin_product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'🗑️ Producto "{name}" eliminado.', 'info')
    return redirect(url_for('admin_products'))


# ─── Gestión de Categorías ───────────────────────────────────────────────────

@app.route('/admin/categorias')
@login_required
def admin_categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categorias/nueva', methods=['GET', 'POST'])
@login_required
def admin_category_new():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            image_path = None
            if 'image' in request.files:
                image_path = save_uploaded_file(request.files['image'], 'categories')

            cat = Category(
                name=name,
                slug=slugify(name),
                description=request.form.get('description', ''),
                icon=request.form.get('icon', ''),
                color=request.form.get('color', '#1a3a6b'),
                image=image_path,
                is_active=request.form.get('is_active') == 'on',
                sort_order=int(request.form.get('sort_order', 0)),
            )
            db.session.add(cat)
            db.session.commit()
            flash(f'✅ Categoría "{name}" creada.', 'success')
            return redirect(url_for('admin_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')

    return render_template('admin/category_form.html', category=None)


@app.route('/admin/categorias/<int:cat_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_category_edit(cat_id):
    cat = Category.query.get_or_404(cat_id)

    if request.method == 'POST':
        try:
            cat.name = request.form.get('name', '').strip()
            cat.description = request.form.get('description', '')
            cat.icon = request.form.get('icon', '')
            cat.color = request.form.get('color', '#1a3a6b')
            cat.is_active = request.form.get('is_active') == 'on'
            cat.sort_order = int(request.form.get('sort_order', 0))

            if 'image' in request.files and request.files['image'].filename:
                image_path = save_uploaded_file(request.files['image'], 'categories')
                if image_path:
                    cat.image = image_path

            db.session.commit()
            flash(f'✅ Categoría actualizada.', 'success')
            return redirect(url_for('admin_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')

    return render_template('admin/category_form.html', category=cat)


@app.route('/admin/categorias/<int:cat_id>/eliminar', methods=['POST'])
@login_required
def admin_category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f'🗑️ Categoría "{name}" eliminada.', 'info')
    return redirect(url_for('admin_categories'))


# ─── Gestión de Pedidos ──────────────────────────────────────────────────────

@app.route('/admin/pedidos')
@login_required
def admin_orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    orders = query.paginate(page=page, per_page=20)
    return render_template('admin/orders.html', orders=orders, current_status=status)


@app.route('/admin/pedidos/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@app.route('/admin/pedidos/<int:order_id>/estado', methods=['POST'])
@login_required
def admin_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status', order.status)
    db.session.commit()
    flash('Estado del pedido actualizado.', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))


# ─── Gestión de Importaciones ────────────────────────────────────────────────

@app.route('/admin/importaciones')
@login_required
def admin_imports():
    page = request.args.get('page', 1, type=int)
    imports = ImportRequest.query.order_by(ImportRequest.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/imports.html', imports=imports)


@app.route('/admin/importaciones/<int:req_id>/estado', methods=['POST'])
@login_required
def admin_import_status(req_id):
    req = ImportRequest.query.get_or_404(req_id)
    req.status = request.form.get('status', req.status)
    req.admin_notes = request.form.get('admin_notes', '')
    db.session.commit()
    flash('Solicitud actualizada.', 'success')
    return redirect(url_for('admin_imports'))


# ─── Gestión de Banners ──────────────────────────────────────────────────────

@app.route('/admin/banners')
@login_required
def admin_banners():
    banners = Banner.query.order_by(Banner.sort_order).all()
    return render_template('admin/banners.html', banners=banners)


@app.route('/admin/banners/nuevo', methods=['GET', 'POST'])
@login_required
def admin_banner_new():
    if request.method == 'POST':
        try:
            image_path = None
            if 'image' in request.files:
                image_path = save_uploaded_file(request.files['image'], 'banners')

            banner = Banner(
                title=request.form.get('title', ''),
                subtitle=request.form.get('subtitle', ''),
                button_text=request.form.get('button_text', ''),
                button_url=request.form.get('button_url', '/'),
                bg_color=request.form.get('bg_color', '#0a0a0f'),
                text_color=request.form.get('text_color', '#ffffff'),
                is_active=request.form.get('is_active') == 'on',
                sort_order=int(request.form.get('sort_order', 0)),
                image=image_path,
            )
            db.session.add(banner)
            db.session.commit()
            flash('✅ Banner creado.', 'success')
            return redirect(url_for('admin_banners'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')

    return render_template('admin/banner_form.html', banner=None)


@app.route('/admin/banners/<int:banner_id>/eliminar', methods=['POST'])
@login_required
def admin_banner_delete(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash('Banner eliminado.', 'info')
    return redirect(url_for('admin_banners'))


# ─── Configuración del Sitio ─────────────────────────────────────────────────

@app.route('/admin/configuracion', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        settings_keys = [
            'site_name', 'site_tagline', 'site_email', 'site_phone',
            'whatsapp_number', 'instagram_url', 'facebook_url', 'tiktok_url',
            'youtube_url', 'address_co', 'address_us', 'address_es',
            'footer_text', 'shipping_info', 'return_policy',
        ]
        for key in settings_keys:
            value = request.form.get(key, '')
            SiteSettings.set(key, value)
        flash('✅ Configuración guardada.', 'success')

    current = {
        'site_name': SiteSettings.get('site_name', 'Tienda Global'),
        'site_tagline': SiteSettings.get('site_tagline', 'Tu tienda de confianza'),
        'site_email': SiteSettings.get('site_email', 'info@tienda.com'),
        'site_phone': SiteSettings.get('site_phone', ''),
        'whatsapp_number': SiteSettings.get('whatsapp_number', ''),
        'instagram_url': SiteSettings.get('instagram_url', '#'),
        'facebook_url': SiteSettings.get('facebook_url', '#'),
        'tiktok_url': SiteSettings.get('tiktok_url', '#'),
        'youtube_url': SiteSettings.get('youtube_url', '#'),
        'address_co': SiteSettings.get('address_co', ''),
        'address_us': SiteSettings.get('address_us', ''),
        'address_es': SiteSettings.get('address_es', ''),
        'footer_text': SiteSettings.get('footer_text', ''),
        'shipping_info': SiteSettings.get('shipping_info', ''),
        'return_policy': SiteSettings.get('return_policy', ''),
    }
    return render_template('admin/settings.html', settings=current)


# ════════════════════════════════════════════════════════════════════════════
#                           HELPERS & CONTEXT PROCESSORS
# ════════════════════════════════════════════════════════════════════════════

def get_site_settings():
    """Retorna dict con configuración global del sitio"""
    return {
        'site_name': SiteSettings.get('site_name', 'Tienda Global'),
        'site_tagline': SiteSettings.get('site_tagline', 'Importaciones Colombia · USA · España'),
        'site_email': SiteSettings.get('site_email', 'info@tienda.com'),
        'site_phone': SiteSettings.get('site_phone', '+57 300 000 0000'),
        'whatsapp_number': SiteSettings.get('whatsapp_number', '573000000000'),
        'instagram_url': SiteSettings.get('instagram_url', '#'),
        'facebook_url': SiteSettings.get('facebook_url', '#'),
        'tiktok_url': SiteSettings.get('tiktok_url', '#'),
        'youtube_url': SiteSettings.get('youtube_url', '#'),
        'footer_text': SiteSettings.get('footer_text', '© 2025 Tienda Global. Todos los derechos reservados.'),
    }


@app.context_processor
def inject_globals():
    """Variables disponibles en todos los templates"""
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    settings = get_site_settings()
    cart_count = 0  # El carrito se maneja en localStorage (JavaScript)
    return dict(
        nav_categories=categories,
        site_settings=settings,
        cart_count=cart_count,
        current_year=datetime.now().year,
    )


@app.template_filter('currency')
def currency_filter(value, symbol='$'):
    """Formatea precios → $1,234.99"""
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


@app.template_filter('date_format')
def date_format_filter(value, fmt='%d/%m/%Y'):
    if value:
        return value.strftime(fmt)
    return ''


# ════════════════════════════════════════════════════════════════════════════
#                           INICIALIZACIÓN DE DATOS
# ════════════════════════════════════════════════════════════════════════════

def init_database():
    """Crea las tablas y datos de ejemplo si no existen"""
    db.create_all()

    # Crear categorías de ejemplo si no hay ninguna
    if Category.query.count() == 0:
        categories_data = [
            {'name': 'Hogar', 'slug': 'hogar', 'icon': '🏠', 'color': '#2563eb', 'sort_order': 1,
             'description': 'Todo para tu hogar y decoración'},
            {'name': 'Tecnología', 'slug': 'tecnologia', 'icon': '💻', 'color': '#7c3aed', 'sort_order': 2,
             'description': 'Gadgets, electrónicos y accesorios tech'},
            {'name': 'Cuidado Personal', 'slug': 'cuidado-personal', 'icon': '✨', 'color': '#db2777', 'sort_order': 3,
             'description': 'Belleza, salud y bienestar personal'},
            {'name': 'Moda', 'slug': 'moda', 'icon': '👗', 'color': '#d97706', 'sort_order': 4,
             'description': 'Ropa, calzado y moda internacional'},
            {'name': 'Vitaminas y Bienestar', 'slug': 'vitaminas', 'icon': '💊', 'color': '#059669', 'sort_order': 5,
             'description': 'Suplementos y productos de bienestar'},
            {'name': 'Juguetería', 'slug': 'jugueteria', 'icon': '🎮', 'color': '#dc2626', 'sort_order': 6,
             'description': 'Juguetes y entretenimiento para toda la familia'},
            {'name': 'Accesorios', 'slug': 'accesorios', 'icon': '👜', 'color': '#0891b2', 'sort_order': 7,
             'description': 'Accesorios premium importados'},
            {'name': 'Ofertas', 'slug': 'ofertas', 'icon': '🔥', 'color': '#ea580c', 'sort_order': 8,
             'description': 'Los mejores precios y descuentos'},
        ]
        for cat_data in categories_data:
            cat = Category(**cat_data)
            db.session.add(cat)
        db.session.commit()
        print("✅ Categorías de ejemplo creadas")

    # Crear configuración inicial del sitio
    default_settings = [
        ('site_name', 'Tienda Global', 'Nombre del sitio'),
        ('site_tagline', 'Importaciones Colombia · USA · España', 'Eslogan'),
        ('site_email', 'info@tiendaglobal.com', 'Email de contacto'),
        ('site_phone', '+57 300 000 0000', 'Teléfono principal'),
        ('whatsapp_number', '573000000000', 'Número WhatsApp (sin + ni espacios)'),
        ('instagram_url', 'https://instagram.com/tiendaglobal', 'URL Instagram'),
        ('facebook_url', 'https://facebook.com/tiendaglobal', 'URL Facebook'),
        ('tiktok_url', 'https://tiktok.com/@tiendaglobal', 'URL TikTok'),
        ('youtube_url', 'https://youtube.com/@tiendaglobal', 'URL YouTube'),
        ('footer_text', '© 2025 Tienda Global. Importaciones internacionales de calidad.', 'Texto del footer'),
        ('address_co', 'Bogotá, Colombia', 'Dirección en Colombia'),
        ('address_us', 'Miami, Florida, USA', 'Dirección en USA'),
        ('address_es', 'Madrid, España', 'Dirección en España'),
    ]
    for key, value, desc in default_settings:
        if not SiteSettings.query.filter_by(key=key).first():
            db.session.add(SiteSettings(key=key, value=value, description=desc))
    db.session.commit()
    print("✅ Configuración inicial del sitio creada")


# ════════════════════════════════════════════════════════════════════════════
#                           PUNTO DE ENTRADA
# ════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        init_database()

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║          🛍️  TIENDA GLOBAL - SERVIDOR INICIADO                   ║
╠══════════════════════════════════════════════════════════════════╣
║  URL:           http://localhost:{port}                          ║
║  Panel Admin:   http://localhost:{port}/admin                    ║
║  Usuario:       admin                                            ║
║  Contraseña:    admin123  (cambiar en .env)                      ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
