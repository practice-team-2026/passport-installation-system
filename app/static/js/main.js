import {
    getInstallations,
    createInstallation,
    updateInstallation,
    deleteInstallation
} from './api.js';

// ---------- СОСТОЯНИЕ ----------
let installations = [];
let editingId = null;
let currentDetailsId = null; // ID объекта, который сейчас просматривается

// ---------- ЗАГРУЗКА ДАННЫХ ----------
async function loadInstallations() {
    try {
        showLoading(true);
        installations = await getInstallations();
        updateKPICards(installations);
        renderCards(installations);
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Не удалось загрузить данные. Проверьте, что сервер запущен (python run.py).');
        installations = [];
        renderCards(installations);
    } finally {
        showLoading(false);
    }
}

// ---------- ОБНОВЛЕНИЕ KPI ----------
function updateKPICards(data) {
    const total = data.length;
    const active = data.filter(i => i.status === 'active').length;
    const today = new Date();
    const overdue = data.filter(i => {
        if (i.next_maintenance && i.next_maintenance !== '—') {
            const maintDate = new Date(i.next_maintenance);
            return maintDate < today;
        }
        return false;
    }).length;
    
    document.getElementById('totalCount').textContent = total;
    document.getElementById('activeCount').textContent = active;
    document.getElementById('overdueCount').textContent = overdue;
}

// ---------- ОТРИСОВКА КАРТОЧЕК С ФОТО ----------
function renderCards(data) {
    const grid = document.getElementById('installationsGrid');
    
    if (!data || data.length === 0) {
        grid.innerHTML = `<div class="loading-placeholder">Нет данных для отображения</div>`;
        return;
    }
    
    grid.innerHTML = data.map(item => `
        <div class="card" onclick="viewDetails('${item.id}')">
            <div class="card-layout">
                <!-- Левая часть: фото -->
                <div class="card-image-wrapper">
                    <img src="${item.photo_url || '/static/img/default-installation.jpg'}" 
                         alt="${escapeHtml(item.name)}" 
                         class="card-image"
                         onerror="this.src='/static/img/default-installation.jpg'">
                    <span class="card-status-badge status-${item.status}">${getStatusText(item.status)}</span>
                </div>
                <!-- Правая часть: информация -->
                <div class="card-info-wrapper">
                    <div class="card-header-text">
                        <span class="card-title">${escapeHtml(item.name)}</span>
                        <span class="card-code">${escapeHtml(item.unique_code)}</span>
                    </div>
                    <div class="card-details">
                        <div class="card-info-item">
                            <span class="card-info-icon">📍</span>
                            <span>${escapeHtml(item.city || '—')}, ${escapeHtml(item.address || '—')}</span>
                        </div>
                        <div class="card-info-item">
                            <span class="card-info-icon">📅</span>
                            <span>ТО: ${item.next_maintenance || 'Не назначено'}</span>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); editObject('${item.id}')" title="Редактировать">
                            ✏️
                        </button>
                        <button class="btn btn-danger btn-small" onclick="event.stopPropagation(); deleteObject('${item.id}')" title="Архивировать">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
function getStatusText(status) {
    const map = {
        'active': 'Активный',
        'draft': 'Черновик',
        'emergency': 'Аварийный',
        'archived': 'Архивный'
    };
    return map[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---------- ФИЛЬТРАЦИЯ ----------
function filterInstallations() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    let filtered = installations;
    
    if (searchTerm) {
        filtered = filtered.filter(i =>
            i.name.toLowerCase().includes(searchTerm) ||
            (i.address && i.address.toLowerCase().includes(searchTerm)) ||
            (i.city && i.city.toLowerCase().includes(searchTerm)) ||
            i.unique_code.toLowerCase().includes(searchTerm)
        );
    }
    
    if (statusFilter) {
        filtered = filtered.filter(i => i.status === statusFilter);
    }
    
    renderCards(filtered);
}

// ---------- МОДАЛКА: СОЗДАНИЕ/РЕДАКТИРОВАНИЕ ----------
window.openCreateModal = function() {
    editingId = null;
    document.getElementById('modalTitle').textContent = '➕ Новый объект';
    document.getElementById('objectForm').reset();
    document.getElementById('objectId').value = '';
    document.getElementById('uniqueCode').value = '';
    document.getElementById('status').value = 'draft';
    document.getElementById('nextMaintenance').value = '';
    document.getElementById('objectModal').classList.add('active');
};

window.editObject = async function(id) {
    try {
        const item = installations.find(i => i.id === id);
        if (!item) {
            const response = await fetch(`http://localhost:5000/api/installations/${id}`);
            if (!response.ok) throw new Error('Ошибка загрузки');
            const data = await response.json();
            fillEditForm(data);
        } else {
            fillEditForm(item);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Не удалось загрузить данные объекта');
    }
};

function fillEditForm(data) {
    editingId = data.id;
    document.getElementById('modalTitle').textContent = '✏️ Редактировать объект';
    document.getElementById('objectId').value = data.id;
    document.getElementById('uniqueCode').value = data.unique_code || '';
    document.getElementById('name').value = data.name || '';
    document.getElementById('city').value = data.city || '';
    document.getElementById('address').value = data.address || '';
    document.getElementById('status').value = data.status || 'draft';
    document.getElementById('nextMaintenance').value = data.next_maintenance || '';
    document.getElementById('objectModal').classList.add('active');
}

window.closeModal = function() {
    document.getElementById('objectModal').classList.remove('active');
    editingId = null;
};

window.handleSubmit = async function(event) {
    event.preventDefault();
    
    const formData = {
        unique_code: document.getElementById('uniqueCode').value.trim(),
        name: document.getElementById('name').value.trim(),
        city: document.getElementById('city').value.trim(),
        address: document.getElementById('address').value.trim(),
        status: document.getElementById('status').value,
        next_maintenance_date: document.getElementById('nextMaintenance').value || null
    };
    
    if (!formData.unique_code || !formData.name) {
        showError('Уникальный код и название обязательны для заполнения');
        return;
    }
    
    try {
        if (editingId) {
            await updateInstallation(editingId, formData);
        } else {
            await createInstallation(formData);
        }
        
        closeModal();
        await loadInstallations();
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Не удалось сохранить объект');
    }
};

// ---------- МОДАЛКА: ДЕТАЛИ ОБЪЕКТА ----------
window.viewDetails = function(id) {
    const item = installations.find(i => i.id === id);
    if (!item) return;

    // Сохраняем ID текущего просматриваемого объекта
    currentDetailsId = id;

    // Обновляем заголовок
    document.getElementById('detailsTitle').textContent = item.name;
    
    // Обновляем фото
    const photoElement = document.getElementById('detailsPhoto');
    photoElement.src = item.photo_url || '/static/img/default-installation.jpg';
    photoElement.alt = item.name;
    
    // Обновляем статус на фото
    const statusBadge = document.getElementById('detailsStatus');
    statusBadge.textContent = getStatusText(item.status);
    statusBadge.className = `status-badge-large status-${item.status}`;
    
    // Заполняем информацию в сетке
    const content = document.getElementById('detailsContent');
    content.innerHTML = `
        <div class="details-info-item">
            <div class="details-info-label">Уникальный код</div>
            <div class="details-info-value"><strong>${escapeHtml(item.unique_code)}</strong></div>
        </div>
        
        <div class="details-info-item">
            <div class="details-info-label">Статус</div>
            <div class="details-info-value">
                <span class="status-badge status-${item.status}">${getStatusText(item.status)}</span>
            </div>
        </div>
        
        <div class="details-info-item">
            <div class="details-info-label">Город</div>
            <div class="details-info-value">${escapeHtml(item.city || 'Не указан')}</div>
        </div>
        
        <div class="details-info-item">
            <div class="details-info-label">Адрес</div>
            <div class="details-info-value">${escapeHtml(item.address || 'Не указан')}</div>
        </div>
        
        <div class="details-info-item">
            <div class="details-info-label">Дата следующего ТО</div>
            <div class="details-info-value">
                ${item.next_maintenance ? new Date(item.next_maintenance).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' }) : 'Не назначено'}
            </div>
        </div>
        
        <div class="details-info-item">
            <div class="details-info-label">Дата создания</div>
            <div class="details-info-value">
                ${item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' }) : '—'}
            </div>
        </div>
    `;
    
    // Показываем модальное окно
    document.getElementById('detailsModal').classList.add('active');
    
    // Блокируем скролл на body
    document.body.style.overflow = 'hidden';
};

// Функция для редактирования из модального окна деталей
window.editFromDetails = function() {
    if (currentDetailsId) {
        closeDetailsModal();
        editObject(currentDetailsId);
    }
};

window.closeDetailsModal = function() {
    document.getElementById('detailsModal').classList.remove('active');
    document.body.style.overflow = '';
    currentDetailsId = null;
};

// ---------- УДАЛЕНИЕ ----------
window.deleteObject = async function(id) {
    if (!confirm('Вы уверены, что хотите архивировать этот объект?')) {
        return;
    }
    
    try {
        await deleteInstallation(id);
        await loadInstallations();
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Не удалось удалить объект');
    }
};

// ---------- УПРАВЛЕНИЕ СОСТОЯНИЕМ ----------
function showLoading(isLoading) {
    const grid = document.getElementById('installationsGrid');
    if (isLoading) {
        grid.innerHTML = `<div class="loading-placeholder">⏳ Загрузка данных...</div>`;
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

// ---------- ИНИЦИАЛИЗАЦИЯ ----------
document.addEventListener('DOMContentLoaded', () => {
    loadInstallations();
    
    document.getElementById('searchInput').addEventListener('input', filterInstallations);
    document.getElementById('statusFilter').addEventListener('change', filterInstallations);
    
    // Закрытие модалок по клику на оверлей
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('active');
            document.body.style.overflow = '';
            if (e.target.id === 'detailsModal') {
                currentDetailsId = null;
            }
        }
    });
    
    // Закрытие модалок по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(m => {
                m.classList.remove('active');
                document.body.style.overflow = '';
                if (m.id === 'detailsModal') {
                    currentDetailsId = null;
                }
            });
        }
    });
});