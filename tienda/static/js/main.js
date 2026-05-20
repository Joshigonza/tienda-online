/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║        TIENDA GLOBAL – JAVASCRIPT PRINCIPAL                     ║
 * ║  Incluye: Carrito, Slider, Modo Oscuro, Navbar, Animaciones     ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

'use strict';

// ════════════════════════════════════════════════════════════════════
//  ESTADO GLOBAL DEL CARRITO (localStorage)
// ════════════════════════════════════════════════════════════════════

const Cart = {
    /**
     * Retorna el carrito actual desde localStorage.
     * Estructura: [ { id, name, price, image, qty } ]
     */
    get() {
        try {
            return JSON.parse(localStorage.getItem('cart') || '[]');
        } catch {
            return [];
        }
    },

    /** Guarda el carrito en localStorage y actualiza la UI */
    save(items) {
        localStorage.setItem('cart', JSON.stringify(items));
        this.updateBadge();
        this.renderPanel();
    },

    /** Agrega o incrementa un producto */
    add(id, name, price, image, qty = 1) {
        const items = this.get();
        const existing = items.find(i => i.id === id);
        if (existing) {
            existing.qty += qty;
        } else {
            items.push({ id, name, price: parseFloat(price), image, qty });
        }
        this.save(items);

        // Feedback visual
        showToast(`✅ "${name}" agregado al carrito`);
        this.animateBadge();
    },

    /** Elimina un producto del carrito */
    remove(id) {
        const items = this.get().filter(i => i.id !== id);
        this.save(items);
    },

    /** Cambia la cantidad de un producto */
    setQty(id, qty) {
        if (qty <= 0) { this.remove(id); return; }
        const items = this.get();
        const item = items.find(i => i.id === id);
        if (item) { item.qty = qty; this.save(items); }
    },

    /** Total del carrito */
    total() {
        return this.get().reduce((acc, i) => acc + i.price * i.qty, 0);
    },

    /** Número total de ítems */
    count() {
        return this.get().reduce((acc, i) => acc + i.qty, 0);
    },

    /** Actualiza el badge del ícono del carrito */
    updateBadge() {
        const badge = document.getElementById('cartBadge');
        if (badge) {
            const count = this.count();
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    },

    /** Anima el badge al agregar un ítem */
    animateBadge() {
        const badge = document.getElementById('cartBadge');
        if (badge) {
            badge.style.transform = 'scale(1.4)';
            setTimeout(() => { badge.style.transform = 'scale(1)'; }, 200);
        }
    },

    /** Renderiza los ítems en el panel lateral */
    renderPanel() {
        const container = document.getElementById('cartItems');
        const footer = document.getElementById('cartFooter');
        const totalEl = document.getElementById('cartTotal');
        if (!container) return;

        const items = this.get();

        if (items.length === 0) {
            container.innerHTML = `
                <div class="cart-empty">
                    <div class="cart-empty-icon">🛍️</div>
                    <p>Tu carrito está vacío</p>
                    <a href="/productos" class="btn btn-primary btn-sm">Ver Productos</a>
                </div>`;
            if (footer) footer.style.display = 'none';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="cart-item" id="cart-item-${item.id}">
                <div class="cart-item-img">
                    ${item.image
                        ? `<img src="/uploads/${item.image}" alt="${escapeHtml(item.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:8px">`
                        : '📦'
                    }
                </div>
                <div class="cart-item-info">
                    <div class="cart-item-name">${escapeHtml(item.name)}</div>
                    <div class="cart-item-price">${formatCurrency(item.price)}</div>
                    <div class="cart-item-controls">
                        <button class="cart-qty-btn" onclick="Cart.setQty(${item.id}, ${item.qty - 1})">−</button>
                        <span class="cart-qty">${item.qty}</span>
                        <button class="cart-qty-btn" onclick="Cart.setQty(${item.id}, ${item.qty + 1})">+</button>
                        <button class="cart-remove" onclick="Cart.remove(${item.id})">Eliminar</button>
                    </div>
                </div>
            </div>
        `).join('');

        if (footer) footer.style.display = 'flex';
        if (totalEl) totalEl.textContent = formatCurrency(this.total());
    }
};

// Funciones globales (llamadas desde HTML con onclick)
function addToCart(id, name, price, image) {
    Cart.add(id, name, price, image);
}

function checkout() {
    const items = Cart.get();
    if (items.length === 0) {
        showToast('Tu carrito está vacío', 'warning');
        return;
    }
    // TODO: Conectar con pasarela de pago (Stripe, PayU, MercadoPago, etc.)
    // Por ahora, redirige a WhatsApp con el resumen del pedido
    sendCartWhatsApp();
}

function sendCartWhatsApp() {
    const items = Cart.get();
    if (items.length === 0) {
        showToast('Tu carrito está vacío', 'warning');
        return;
    }

    // Obtener número de WhatsApp del DOM
    const waLink = document.querySelector('.whatsapp-float');
    if (!waLink) return;

    const waNumber = waLink.href.match(/wa\.me\/(\d+)/)?.[1] || '';
    const itemsList = items.map(i => `• ${i.name} x${i.qty} = ${formatCurrency(i.price * i.qty)}`).join('\n');
    const total = formatCurrency(Cart.total());
    const message = `¡Hola! Quiero hacer el siguiente pedido:\n\n${itemsList}\n\nTotal: ${total}\n\n¿Pueden ayudarme a procesar la compra?`;

    const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
}


// ════════════════════════════════════════════════════════════════════
//  PANEL DEL CARRITO
// ════════════════════════════════════════════════════════════════════

function openCart() {
    document.getElementById('cartPanel')?.classList.add('open');
    document.getElementById('cartOverlay')?.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeCart() {
    document.getElementById('cartPanel')?.classList.remove('open');
    document.getElementById('cartOverlay')?.classList.remove('open');
    document.body.style.overflow = '';
}


// ════════════════════════════════════════════════════════════════════
//  HERO SLIDER
// ════════════════════════════════════════════════════════════════════

let sliderIndex = 0;
let sliderTimer = null;
let sliderTotal = 0;

function initHeroSlider() {
    const slides = document.querySelectorAll('.hero-slide');
    const dots   = document.querySelectorAll('.hero-dot');
    sliderTotal  = slides.length;

    if (sliderTotal < 2) return;

    function goTo(index) {
        slides[sliderIndex].classList.remove('active');
        dots[sliderIndex]?.classList.remove('active');
        sliderIndex = (index + sliderTotal) % sliderTotal;
        slides[sliderIndex].classList.add('active');
        dots[sliderIndex]?.classList.add('active');

        // Re-animar textos del slide
        slides[sliderIndex].querySelectorAll('.animate-fade-up').forEach(el => {
            el.style.animation = 'none';
            el.offsetHeight; // reflow
            el.style.animation = '';
        });
    }

    function next() { goTo(sliderIndex + 1); }
    function prev() { goTo(sliderIndex - 1); }

    function startAuto() {
        stopAuto();
        sliderTimer = setInterval(next, 5000);
    }
    function stopAuto() { clearInterval(sliderTimer); }

    document.getElementById('heroNext')?.addEventListener('click', () => { next(); startAuto(); });
    document.getElementById('heroPrev')?.addEventListener('click', () => { prev(); startAuto(); });

    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            goTo(parseInt(dot.dataset.index));
            startAuto();
        });
    });

    // Pausar al pasar el mouse
    document.getElementById('heroSlider')?.addEventListener('mouseenter', stopAuto);
    document.getElementById('heroSlider')?.addEventListener('mouseleave', startAuto);

    // Soporte táctil
    let touchStartX = 0;
    const slider = document.getElementById('heroSlider');
    slider?.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
    slider?.addEventListener('touchend', e => {
        const diff = touchStartX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 50) { diff > 0 ? next() : prev(); }
        startAuto();
    }, { passive: true });

    startAuto();
}


// ════════════════════════════════════════════════════════════════════
//  MODO OSCURO
// ════════════════════════════════════════════════════════════════════

function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    applyTheme(saved);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    const lightIcon = document.querySelector('.theme-icon-light');
    const darkIcon  = document.querySelector('.theme-icon-dark');
    if (lightIcon) lightIcon.style.display = theme === 'dark' ? 'none' : 'inline';
    if (darkIcon)  darkIcon.style.display  = theme === 'dark' ? 'inline' : 'none';
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
}


// ════════════════════════════════════════════════════════════════════
//  NAVBAR
// ════════════════════════════════════════════════════════════════════

function initNavbar() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navMenu   = document.getElementById('navMenu');

    // Sombra al hacer scroll
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 10);
        }, { passive: true });
    }

    // Menú hamburger (mobile)
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('open');
            navMenu.classList.toggle('open');
        });

        // Cerrar al hacer clic en un link
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('open');
                navMenu.classList.remove('open');
            });
        });
    }

    // Toggle buscador
    const searchToggle = document.getElementById('searchToggle');
    const searchBar    = document.getElementById('searchBar');
    if (searchToggle && searchBar) {
        searchToggle.addEventListener('click', () => {
            searchBar.classList.toggle('open');
            if (searchBar.classList.contains('open')) {
                searchBar.querySelector('input')?.focus();
            }
        });
    }
}


// ════════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ════════════════════════════════════════════════════════════════════

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer') || (() => {
        const el = document.createElement('div');
        el.id = 'toastContainer';
        el.style.cssText = `
            position:fixed; bottom:80px; left:50%; transform:translateX(-50%);
            z-index:500; display:flex; flex-direction:column; align-items:center; gap:8px;
            pointer-events:none;
        `;
        document.body.appendChild(el);
        return el;
    })();

    const toast = document.createElement('div');
    toast.style.cssText = `
        background: ${type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#0f2557'};
        color: white;
        padding: 10px 20px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
        font-family: 'DM Sans', sans-serif;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        animation: fadeUp 0.3s ease;
        pointer-events: auto;
        max-width: 320px;
        text-align: center;
    `;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2800);
}


// ════════════════════════════════════════════════════════════════════
//  ANIMACIONES DE ENTRADA POR SCROLL
// ════════════════════════════════════════════════════════════════════

function initScrollAnimations() {
    const elements = document.querySelectorAll(
        '.product-card, .category-card, .testimonial-card, .stat-card, .import-route-card'
    );

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeUp 0.5s ease forwards';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    elements.forEach((el, i) => {
        el.style.opacity = '0';
        el.style.animationDelay = `${(i % 4) * 0.08}s`;
        observer.observe(el);
    });
}


// ════════════════════════════════════════════════════════════════════
//  GALERÍA DE IMÁGENES EN DETALLE DE PRODUCTO
// ════════════════════════════════════════════════════════════════════

function initProductGallery() {
    const mainImg   = document.getElementById('galleryMain');
    const thumbs    = document.querySelectorAll('.gallery-thumb');

    if (!mainImg || thumbs.length === 0) return;

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
            const src = thumb.dataset.src;
            if (src) {
                mainImg.src = src;
                thumbs.forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            }
        });
    });
}


// ════════════════════════════════════════════════════════════════════
//  SELECTOR DE CANTIDAD EN DETALLE DE PRODUCTO
// ════════════════════════════════════════════════════════════════════

function initQtySelector() {
    const qtyValue = document.getElementById('qtyValue');
    const qtyPlus  = document.getElementById('qtyPlus');
    const qtyMinus = document.getElementById('qtyMinus');

    if (!qtyValue) return;

    let qty = 1;
    const maxStock = parseInt(qtyValue.dataset.max || '99');

    qtyPlus?.addEventListener('click', () => {
        if (qty < maxStock) { qty++; qtyValue.textContent = qty; }
    });

    qtyMinus?.addEventListener('click', () => {
        if (qty > 1) { qty--; qtyValue.textContent = qty; }
    });

    // Botón "Agregar al carrito" con la cantidad seleccionada
    document.getElementById('addToCartBtn')?.addEventListener('click', () => {
        const { productId, productName, productPrice, productImage } = document.getElementById('addToCartBtn').dataset;
        Cart.add(parseInt(productId), productName, parseFloat(productPrice), productImage, qty);
        openCart();
    });
}


// ════════════════════════════════════════════════════════════════════
//  UPLOAD DE IMÁGENES EN ADMIN (preview)
// ════════════════════════════════════════════════════════════════════

function initImageUpload() {
    const uploadAreas = document.querySelectorAll('.upload-area');

    uploadAreas.forEach(area => {
        const input   = area.querySelector('input[type="file"]');
        const preview = area.closest('.form-group')?.querySelector('.image-preview-grid');

        if (!input) return;

        // Click en el área
        area.addEventListener('click', () => input.click());

        // Drag & Drop
        area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('dragover'); });
        area.addEventListener('dragleave', () => area.classList.remove('dragover'));
        area.addEventListener('drop', e => {
            e.preventDefault();
            area.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
            if (files.length > 0) showImagePreviews(files, preview);
        });

        // Selección de archivos
        input.addEventListener('change', () => {
            const files = Array.from(input.files).filter(f => f.type.startsWith('image/'));
            showImagePreviews(files, preview);
        });
    });
}

function showImagePreviews(files, container) {
    if (!container) return;

    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = e => {
            const item = document.createElement('div');
            item.className = 'image-preview-item';
            item.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="image-preview-remove" onclick="this.closest('.image-preview-item').remove()">×</button>
            `;
            container.appendChild(item);
        };
        reader.readAsDataURL(file);
    });
}


// ════════════════════════════════════════════════════════════════════
//  FLASH MESSAGES – Auto-dismiss
// ════════════════════════════════════════════════════════════════════

function initFlashMessages() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach((flash, i) => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.4s ease';
            setTimeout(() => flash.remove(), 400);
        }, 4000 + i * 500);
    });
}


// ════════════════════════════════════════════════════════════════════
//  UTILIDADES
// ════════════════════════════════════════════════════════════════════

function formatCurrency(amount, symbol = '$') {
    return `${symbol}${parseFloat(amount).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}


// ════════════════════════════════════════════════════════════════════
//  FORMULARIO DE IMPORTACIÓN – validación y UX
// ════════════════════════════════════════════════════════════════════

function initImportForm() {
    const form = document.getElementById('importForm');
    if (!form) return;

    form.addEventListener('submit', e => {
        const required = form.querySelectorAll('[required]');
        let valid = true;

        required.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = 'var(--color-error)';
                valid = false;
            } else {
                field.style.borderColor = '';
            }
        });

        if (!valid) {
            e.preventDefault();
            showToast('Por favor completa todos los campos requeridos', 'error');
        }
    });
}


// ════════════════════════════════════════════════════════════════════
//  CONFIRMACIÓN DE BORRADO EN ADMIN
// ════════════════════════════════════════════════════════════════════

function confirmDelete(message) {
    return confirm(message || '¿Estás seguro de que deseas eliminar este elemento? Esta acción no se puede deshacer.');
}

// Aplicar confirmación a todos los formularios de eliminación
function initDeleteConfirmations() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', e => {
            if (!confirmDelete()) e.preventDefault();
        });
    });
}


// ════════════════════════════════════════════════════════════════════
//  TABS EN DETALLE DE PRODUCTO
// ════════════════════════════════════════════════════════════════════

function initProductTabs() {
    const tabs    = document.querySelectorAll('.product-tab-btn');
    const panels  = document.querySelectorAll('.product-tab-panel');

    if (tabs.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.target)?.classList.add('active');
        });
    });
}


// ════════════════════════════════════════════════════════════════════
//  INICIALIZACIÓN PRINCIPAL
// ════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Core
    initTheme();
    initNavbar();
    initFlashMessages();
    Cart.updateBadge();
    Cart.renderPanel();

    // Carrito lateral
    document.getElementById('cartToggle')?.addEventListener('click', openCart);
    document.getElementById('cartClose')?.addEventListener('click',  closeCart);
    document.getElementById('cartOverlay')?.addEventListener('click', closeCart);

    // Modo oscuro
    document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);

    // Slider del hero
    initHeroSlider();

    // Animaciones de scroll
    if ('IntersectionObserver' in window) {
        initScrollAnimations();
    }

    // Páginas específicas
    initProductGallery();
    initQtySelector();
    initImageUpload();
    initImportForm();
    initDeleteConfirmations();
    initProductTabs();

    console.log('🛍️ Tienda Global – JS inicializado correctamente');
});

// Exportar para uso en templates inline
window.Cart      = Cart;
window.addToCart = addToCart;
window.checkout  = checkout;
window.sendCartWhatsApp = sendCartWhatsApp;
window.openCart  = openCart;
window.closeCart = closeCart;
window.showToast = showToast;
window.confirmDelete = confirmDelete;
