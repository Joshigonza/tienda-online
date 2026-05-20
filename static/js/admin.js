/**
 * admin.js — Panel Administrativo
 * Tienda Online Internacional
 * ============================
 * Funciones: sidebar móvil, confirmaciones de borrado,
 * auto-dismiss de alertas, preview de imágenes, tabs.
 */

// ─── Inicialización ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initFlashMessages();
  initDeleteConfirmations();
  initImagePreviews();
  initFormEnhancements();
  initTableSearch();
  initStatusColors();
});

// ─── Sidebar Móvil ──────────────────────────────────────────────────────────
function initSidebar() {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.querySelector('.admin-sidebar');
  const overlay   = document.getElementById('sidebarOverlay');

  if (!toggleBtn || !sidebar) return;

  // Crear overlay si no existe
  let ov = overlay;
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'sidebarOverlay';
    ov.className = 'sidebar-overlay';
    document.body.appendChild(ov);
  }

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    ov.classList.toggle('active');
    document.body.classList.toggle('sidebar-open');
  });

  ov.addEventListener('click', () => {
    sidebar.classList.remove('open');
    ov.classList.remove('active');
    document.body.classList.remove('sidebar-open');
  });

  // Cerrar sidebar al redimensionar a desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('open');
      ov.classList.remove('active');
      document.body.classList.remove('sidebar-open');
    }
  });
}

// ─── Flash Messages Auto-Dismiss ────────────────────────────────────────────
function initFlashMessages() {
  const alerts = document.querySelectorAll('.admin-alert');

  alerts.forEach(alert => {
    // Auto-dismiss después de 5 segundos
    setTimeout(() => dismissAlert(alert), 5000);

    // Botón de cierre manual
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => dismissAlert(alert));
    }
  });
}

function dismissAlert(alert) {
  alert.style.opacity = '0';
  alert.style.transform = 'translateX(100%)';
  alert.style.transition = 'all 0.3s ease';
  setTimeout(() => alert.remove(), 300);
}

// ─── Confirmaciones de Borrado ───────────────────────────────────────────────
function initDeleteConfirmations() {
  // Links/botones con data-confirm
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function(e) {
      const msg = this.dataset.confirm || '¿Estás seguro de que deseas eliminar este elemento?';
      if (!confirm(msg)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

  // Formularios de borrado con clase delete-form
  document.querySelectorAll('.delete-form').forEach(form => {
    form.addEventListener('submit', function(e) {
      const msg = this.dataset.confirm || '¿Eliminar este elemento? Esta acción no se puede deshacer.';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
}

// ─── Preview de Imágenes ─────────────────────────────────────────────────────
function initImagePreviews() {
  // Input de imagen único
  document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
    input.addEventListener('change', function() {
      const previewId = this.dataset.preview;
      const preview   = document.getElementById(previewId);
      if (!preview) return;

      const file = this.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = e => {
          preview.src = e.target.result;
          preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // Múltiples imágenes de producto
  const multiInput = document.getElementById('productImages');
  const previewGrid = document.getElementById('newImagesPreview');

  if (multiInput && previewGrid) {
    multiInput.addEventListener('change', function() {
      previewGrid.innerHTML = '';
      Array.from(this.files).forEach((file, idx) => {
        if (!file.type.startsWith('image/')) return;

        const reader = new FileReader();
        reader.onload = e => {
          const wrap = document.createElement('div');
          wrap.className = 'preview-thumb';
          wrap.innerHTML = `
            <img src="${e.target.result}" alt="Preview ${idx + 1}">
            <span class="preview-num">${idx + 1}</span>
          `;
          previewGrid.appendChild(wrap);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Drag & drop para áreas de upload
  document.querySelectorAll('.upload-area').forEach(area => {
    const input = area.querySelector('input[type="file"]');
    if (!input) return;

    area.addEventListener('dragover', e => {
      e.preventDefault();
      area.classList.add('drag-over');
    });

    area.addEventListener('dragleave', () => area.classList.remove('drag-over'));

    area.addEventListener('drop', e => {
      e.preventDefault();
      area.classList.remove('drag-over');
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        input.dispatchEvent(new Event('change'));
      }
    });

    area.addEventListener('click', () => input.click());
  });
}

// ─── Mejoras de Formularios ──────────────────────────────────────────────────
function initFormEnhancements() {
  // Auto-generar slug desde nombre
  const nameInput = document.getElementById('productName') || document.getElementById('categoryName');
  const slugInput = document.getElementById('slug');

  if (nameInput && slugInput && !slugInput.value) {
    nameInput.addEventListener('input', function() {
      // Solo si el slug no ha sido modificado manualmente
      if (!slugInput.dataset.manual) {
        slugInput.value = generateSlug(this.value);
      }
    });

    slugInput.addEventListener('input', function() {
      this.dataset.manual = 'true';
    });
  }

  // Contador de caracteres para textareas
  document.querySelectorAll('textarea[maxlength], input[maxlength]').forEach(el => {
    const max     = parseInt(el.getAttribute('maxlength'));
    const counter = document.createElement('small');
    counter.className = 'char-counter';
    counter.textContent = `0 / ${max}`;
    el.parentNode.insertBefore(counter, el.nextSibling);

    el.addEventListener('input', function() {
      counter.textContent = `${this.value.length} / ${max}`;
      counter.style.color = this.value.length > max * 0.9 ? 'var(--danger)' : 'var(--text-muted)';
    });
  });

  // Formateo de precios en tiempo real
  document.querySelectorAll('input[data-currency]').forEach(input => {
    input.addEventListener('blur', function() {
      const val = parseFloat(this.value);
      if (!isNaN(val)) {
        this.value = val.toFixed(2);
      }
    });
  });

  // Submit con loading state
  document.querySelectorAll('form.admin-form').forEach(form => {
    form.addEventListener('submit', function() {
      const btn = this.querySelector('[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-sm"></span> Guardando...`;
      }
    });
  });
}

// ─── Búsqueda en tablas ──────────────────────────────────────────────────────
function initTableSearch() {
  const searchInput = document.getElementById('tableSearch');
  if (!searchInput) return;

  searchInput.addEventListener('input', function() {
    const term  = this.value.toLowerCase().trim();
    const tbody = document.querySelector('.admin-table tbody');
    if (!tbody) return;

    Array.from(tbody.rows).forEach(row => {
      const text  = row.textContent.toLowerCase();
      row.style.display = term === '' || text.includes(term) ? '' : 'none';
    });

    // Mensaje de vacío
    const empty = document.getElementById('tableEmpty');
    if (empty) {
      const visible = Array.from(tbody.rows).filter(r => r.style.display !== 'none');
      empty.style.display = visible.length === 0 ? 'block' : 'none';
    }
  });
}

// ─── Colores de Estado ───────────────────────────────────────────────────────
function initStatusColors() {
  // Status select — cambiar color al cambiar valor
  document.querySelectorAll('select.status-select').forEach(sel => {
    updateSelectColor(sel);
    sel.addEventListener('change', function() {
      updateSelectColor(this);
      // Auto-submit si tiene data-autosubmit
      if (this.dataset.autosubmit) {
        this.closest('form')?.submit();
      }
    });
  });
}

function updateSelectColor(sel) {
  sel.className = sel.className.replace(/\bstatus-\S+/g, '');
  sel.classList.add(`status-${sel.value}`);
}

// ─── Utilidades ─────────────────────────────────────────────────────────────
function generateSlug(text) {
  const map = {
    'á':'a','é':'e','í':'i','ó':'o','ú':'u',
    'Á':'a','É':'e','Í':'i','Ó':'o','Ú':'u',
    'ñ':'n','Ñ':'n','ü':'u','Ü':'u'
  };
  return text
    .toLowerCase()
    .replace(/[áéíóúÁÉÍÓÚñÑüÜ]/g, c => map[c] || c)
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// ─── Funciones globales (llamadas desde HTML) ────────────────────────────────

/** Eliminar imagen existente de producto */
window.removeExistingImage = function(btn, filename) {
  if (!confirm('¿Eliminar esta imagen del producto?')) return;

  const card = btn.closest('.img-card');

  fetch('/admin/products/remove-image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename,
      product_id: document.getElementById('productId')?.value
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      card.style.opacity = '0';
      card.style.transform = 'scale(0.8)';
      setTimeout(() => card.remove(), 300);
      showToast('Imagen eliminada', 'success');
    } else {
      showToast(data.error || 'Error al eliminar imagen', 'error');
    }
  })
  .catch(() => showToast('Error de conexión', 'error'));
};

/** Toast notification */
window.showToast = function(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
      position:fixed; top:1rem; right:1rem; z-index:9999;
      display:flex; flex-direction:column; gap:.5rem;
    `;
    document.body.appendChild(container);
  }

  const colors = {
    success: '#10b981',
    error:   '#ef4444',
    warning: '#f59e0b',
    info:    '#3b82f6'
  };

  const toast = document.createElement('div');
  toast.style.cssText = `
    background:${colors[type] || colors.info};
    color:#fff; padding:.75rem 1.25rem; border-radius:.5rem;
    font-size:.875rem; font-weight:500; box-shadow:0 4px 12px rgba(0,0,0,.2);
    opacity:0; transform:translateX(100%);
    transition:all .3s ease; max-width:300px;
  `;
  toast.textContent = message;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity  = '1';
    toast.style.transform = 'translateX(0)';
  });

  setTimeout(() => {
    toast.style.opacity   = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
};

/** Confirmar acción crítica con input de texto */
window.confirmDelete = function(message, confirmText) {
  if (confirmText) {
    const input = prompt(`${message}\n\nEscribe "${confirmText}" para confirmar:`);
    return input === confirmText;
  }
  return confirm(message);
};
