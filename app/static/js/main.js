import {
    getInstallations,
    createInstallation,
    updateInstallation,
    deleteInstallation
} from './api.js';

// ---------- СОСТОЯНИЕ ----------
let installations = [];
let editingId = null;
let currentDetailsId = null;
let isSubmitting = false; // Флаг для предотвращения двойной отправки

// ---------- ЗАГРУЗКА ДАННЫХ ----------
async function loadInstallations() {
    // Проверяем, что мы на главной странице
    if (!document.getElementById('installationsGrid')) {
        console.log('ℹ️ Главная страница не активна, пропускаем загрузку');
        return;
    }
    
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
    
    const totalEl = document.getElementById('totalCount');
    const activeEl = document.getElementById('activeCount');
    const overdueEl = document.getElementById('overdueCount');
    
    if (totalEl) totalEl.textContent = total;
    if (activeEl) activeEl.textContent = active;
    if (overdueEl) overdueEl.textContent = overdue;
}

// ---------- ОТРИСОВКА КАРТОЧЕК ----------
function renderCards(data) {
    const grid = document.getElementById('installationsGrid');
    if (!grid) return;
    
    if (!data || data.length === 0) {
        grid.innerHTML = `<div class="loading-placeholder">Нет данных для отображения</div>`;
        return;
    }
    
    grid.innerHTML = data.map(item => `
        <div class="card" onclick="viewDetails('${item.id}')">
            <div class="card-layout">
                <div class="card-image-wrapper">
                    <img src="${item.photo_url || '/static/img/default-installation.jpg'}" 
                         alt="${escapeHtml(item.name)}" 
                         class="card-image"
                         onerror="this.src='/static/img/default-installation.jpg'">
                    <span class="card-status-badge status-${item.status}">${getStatusText(item.status)}</span>
                </div>
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
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
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

// ---------- МОДАЛКА: СОЗДАНИЕ ----------
window.openCreateModal = function() {
    editingId = null;
    document.getElementById('modalTitle').textContent = '➕ Новый объект';
    document.getElementById('objectForm').reset();
    document.getElementById('objectId').value = '';
    document.getElementById('uniqueCode').value = '';
    document.getElementById('status').value = 'draft';
    document.getElementById('nextMaintenance').value = '';
    document.getElementById('photoFile').value = '';
    document.getElementById('currentPhotoUrl').value = '';
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtn').textContent = 'Сохранить';
    document.getElementById('objectModal').classList.add('active');
};

// ---------- МОДАЛКА: РЕДАКТИРОВАНИЕ ----------
window.editObject = async function(id) {
    try {
        const item = installations.find(i => i.id === id);
        if (!item) {
            const response = await fetch(`/api/installations/${id}`);
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
    document.getElementById('currentPhotoUrl').value = data.photo_url || '';
    document.getElementById('photoFile').value = '';
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtn').textContent = 'Сохранить';
    document.getElementById('objectModal').classList.add('active');
}

window.closeModal = function() {
    document.getElementById('objectModal').classList.remove('active');
    editingId = null;
    isSubmitting = false;
};

// ---------- МОДАЛКА: ОТПРАВКА ФОРМЫ ----------
window.handleSubmit = async function(event) {
    event.preventDefault();
    
    // Защита от двойной отправки
    if (isSubmitting) return;
    isSubmitting = true;
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Сохранение...';
    
    try {
        // 1. Сначала загружаем фото (если выбрано)
        const fileInput = document.getElementById('photoFile');
        let photoUrl = document.getElementById('currentPhotoUrl').value || null;
        
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            // Проверка размера файла (16 MB)
            if (file.size > 16 * 1024 * 1024) {
                throw new Error('Файл слишком большой. Максимальный размер — 16 МБ.');
            }
            
            const uploadFormData = new FormData();
            uploadFormData.append('photo', file);
            
            const uploadResponse = await fetch('/api/upload-photo', {
                method: 'POST',
                body: uploadFormData
            });
            
            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json();
                throw new Error(errorData.error || 'Ошибка загрузки фото');
            }
            
            const uploadResult = await uploadResponse.json();
            photoUrl = uploadResult.photo_url;
        }
        
        // 2. Собираем данные объекта
        const formData = {
            unique_code: document.getElementById('uniqueCode').value.trim(),
            name: document.getElementById('name').value.trim(),
            city: document.getElementById('city').value.trim(),
            address: document.getElementById('address').value.trim(),
            status: document.getElementById('status').value,
            next_maintenance_date: document.getElementById('nextMaintenance').value || null,
            photo_url: photoUrl
        };
        
        if (!formData.unique_code || !formData.name) {
            throw new Error('Уникальный код и название обязательны для заполнения');
        }
        
        // 3. Создаём или обновляем объект
        if (editingId) {
            await updateInstallation(editingId, formData);
        } else {
            await createInstallation(formData);
        }
        
        closeModal();
        await loadInstallations();
        hideError();
        showSuccess('Объект успешно сохранён!');
        
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Не удалось сохранить объект');
    } finally {
        isSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Сохранить';
    }
};

// ---------- МОДАЛКА: ДЕТАЛИ ОБЪЕКТА ----------
window.viewDetails = function(id) {
    const item = installations.find(i => i.id === id);
    if (!item) return;

    currentDetailsId = id;
    document.getElementById('detailsTitle').textContent = item.name;
    
    const photoElement = document.getElementById('detailsPhoto');
    if (photoElement) {
        photoElement.src = item.photo_url || '/static/img/default-installation.jpg';
        photoElement.alt = item.name;
    }
    
    const statusBadge = document.getElementById('detailsStatus');
    if (statusBadge) {
        statusBadge.textContent = getStatusText(item.status);
        statusBadge.className = `status-badge-large status-${item.status}`;
    }
    
    const content = document.getElementById('detailsContent');
    if (content) {
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
    }
    
    document.getElementById('detailsModal').classList.add('active');
    document.body.style.overflow = 'hidden';
};

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
        showSuccess('Объект успешно архивирован');
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Не удалось удалить объект');
    }
};

// ---------- УПРАВЛЕНИЕ СОСТОЯНИЕМ ----------
function showLoading(isLoading) {
    const grid = document.getElementById('installationsGrid');
    if (!grid) return;
    if (isLoading) {
        grid.innerHTML = `<div class="loading-placeholder">⏳ Загрузка данных...</div>`;
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) return;
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.style.display = 'block';
    errorDiv.className = 'error-message';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) return;
    errorDiv.textContent = `✅ ${message}`;
    errorDiv.style.display = 'block';
    errorDiv.className = 'success-message';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) return;
    errorDiv.style.display = 'none';
}

// ---------- СТИЛИ ДЛЯ УСПЕШНЫХ СООБЩЕНИЙ ----------
(function addSuccessStyles() {
    if (document.getElementById('success-style')) return;
    const style = document.createElement('style');
    style.id = 'success-style';
    style.textContent = `
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            border: 2px solid #c3e6cb;
            animation: shake 0.5s;
            font-weight: 500;
        }
    `;
    document.head.appendChild(style);
})();

// ---------- ИНИЦИАЛИЗАЦИЯ ----------
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, что мы на главной странице
    const grid = document.getElementById('installationsGrid');
    if (!grid) {
        console.log('ℹ️ Главная страница не активна, пропускаем инициализацию main.js');
        return;
    }
    
    // Загружаем данные
    loadInstallations();
    
    // Обработчики событий с проверками
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterInstallations);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterInstallations);
    }
    
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