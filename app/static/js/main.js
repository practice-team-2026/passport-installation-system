// app/static/js/main.js
import {
    getInstallations,
    createInstallation,
    updateInstallation,
    deleteInstallation
} from './api.js';

// ---------- СОСТОЯНИЕ ----------
let installations = [];
let editingId = null;

// ---------- ЗАГРУЗКА ДАННЫХ ----------
async function loadInstallations() {
    try {
        showLoading(true);
        installations = await getInstallations();
        updateKPICards(installations);
        renderTable(installations);
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Не удалось загрузить данные. Проверьте, что сервер запущен (python run.py).');
        installations = [];
        renderTable(installations);
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

// ---------- ОТРИСОВКА ТАБЛИЦЫ ----------
function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    
    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="loading">Нет данных для отображения</td></tr>`;
        return;
    }
    
    tbody.innerHTML = data.map(item => `
        <tr>
            <td data-label="Код"><strong>${escapeHtml(item.unique_code)}</strong></td>
            <td data-label="Название">${escapeHtml(item.name)}</td>
            <td data-label="Город">${escapeHtml(item.city || '—')}</td>
            <td data-label="Адрес">${escapeHtml(item.address || '—')}</td>
            <td data-label="Статус"><span class="status-badge status-${item.status}">${getStatusText(item.status)}</span></td>
            <td data-label="Дата ТО">${item.next_maintenance || '—'}</td>
            <td data-label="Действия">
                <button class="btn btn-primary btn-small" onclick="editObject('${item.id}')" title="Редактировать">✏️</button>
                <button class="btn btn-danger btn-small" onclick="deleteObject('${item.id}')" title="Архивировать">🗑️</button>
            </td>
        </tr>
    `).join('');
}

// ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
function getStatusText(status) {
    const map = {
        'active': '🟢 Активный',
        'draft': '⚪️ Черновик',
        'emergency': '🔴 Аварийный',
        'archived': '⚫️ Архивный'
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
            (i.address && i.address.toLowerCase().includes(searchTerm))
        );
    }
    
    if (statusFilter) {
        filtered = filtered.filter(i => i.status === statusFilter);
    }
    
    renderTable(filtered);
}

// ---------- МОДАЛКА: ОТКРЫТИЕ ----------
window.openCreateModal = function() {
    editingId = null;
    document.getElementById('modalTitle').textContent = '➕ Новый объект';
    document.getElementById('objectForm').reset();
    document.getElementById('objectId').value = '';
    document.getElementById('uniqueCode').value = '';
    document.getElementById('status').value = 'draft';
    document.getElementById('objectModal').classList.add('active');
};

window.editObject = async function(id) {
    try {
        const item = installations.find(i => i.id === id);
        if (!item) {
            // Если нет в кэше — загружаем с сервера
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
    document.getElementById('objectModal').classList.add('active');
}

// ---------- МОДАЛКА: ЗАКРЫТИЕ ----------
window.closeModal = function() {
    document.getElementById('objectModal').classList.remove('active');
    editingId = null;
};

// ---------- МОДАЛКА: ОТПРАВКА ФОРМЫ ----------
window.handleSubmit = async function(event) {
    event.preventDefault();
    
    const formData = {
        unique_code: document.getElementById('uniqueCode').value.trim(),
        name: document.getElementById('name').value.trim(),
        city: document.getElementById('city').value.trim(),
        address: document.getElementById('address').value.trim(),
        status: document.getElementById('status').value
    };
    
    // Простая валидация
    if (!formData.unique_code || !formData.name) {
        showError('Уникальный код и название обязательны для заполнения');
        return;
    }
    
    try {
        let result;
        if (editingId) {
            await updateInstallation(editingId, formData);
        } else {
            await createInstallation(formData);
        }
        
        closeModal();
        await loadInstallations(); // Перезагружаем список
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Не удалось сохранить объект');
    }
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
    const tbody = document.getElementById('tableBody');
    if (isLoading) {
        tbody.innerHTML = `<tr><td colspan="7" class="loading">⏳ Загрузка данных...</td></tr>`;
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
    
    // Обработчики событий
    document.getElementById('searchInput').addEventListener('input', filterInstallations);
    document.getElementById('statusFilter').addEventListener('change', filterInstallations);
    
    // Закрытие модалки по клику на оверлей
    document.getElementById('objectModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('objectModal')) {
            closeModal();
        }
    });
    
    // Закрытие модалки по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
});