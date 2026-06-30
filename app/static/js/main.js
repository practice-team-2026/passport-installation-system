// Моковые данные для отладки (потом будем заменять на запросы к API)
let installations = [
    {
        id: '1',
        unique_code: 'ПАС-001',
        name: 'Вентиляция ТЦ "Европа"',
        status: 'active',
        city: 'Москва',
        address: 'ул. Тверская, 12',
        next_maintenance: '2026-07-15',
        equipment_count: 4
    },
    {
        id: '2',
        unique_code: 'ПАС-002',
        name: 'Кондиционирование Офис-центра',
        status: 'emergency',
        city: 'Санкт-Петербург',
        address: 'Невский пр., 45',
        next_maintenance: '2026-06-20',
        equipment_count: 2
    },
    {
        id: '3',
        unique_code: 'ПАС-003',
        name: 'Насосная станция "Северная"',
        status: 'active',
        city: 'Казань',
        address: 'ул. Баумана, 78',
        next_maintenance: '2026-08-01',
        equipment_count: 6
    },
    {
        id: '4',
        unique_code: 'ПАС-004',
        name: 'Компрессорная установка',
        status: 'draft',
        city: 'Екатеринбург',
        address: 'ул. Ленина, 34',
        next_maintenance: '—',
        equipment_count: 3
    },
    {
        id: '5',
        unique_code: 'ПАС-005',
        name: 'Вентиляция Логистического центра',
        status: 'archived',
        city: 'Москва',
        address: 'МКАД, 45-й км',
        next_maintenance: '—',
        equipment_count: 5
    }
];

// Функция обновления статистики
function updateStats(data) {
    document.getElementById('totalCount').textContent = data.length;
    document.getElementById('activeCount').textContent = data.filter(item => item.status === 'active').length;
    document.getElementById('overdueCount').textContent = data.filter(item => item.status === 'emergency').length;
}

// Функция рендеринга таблицы
function renderTable(data) {
    const tbody = document.getElementById('installationsBody');
    
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:#6b7280;">📭 Нет объектов для отображения</td></tr>`;
        return;
    }
    
    tbody.innerHTML = data.map(item => `
        <tr>
            <td><strong>${item.unique_code}</strong></td>
            <td>${item.name}</td>
            <td>${item.city}, ${item.address}</td>
            <td><span class="badge badge-${item.status}">${item.status}</span></td>
            <td>${item.next_maintenance}</td>
            <td>${item.equipment_count} шт.</td>
            <td>
                <button class="btn-icon" onclick="viewInstallation('${item.id}')" title="Просмотр">👁️</button>
                <button class="btn-icon" onclick="editInstallation('${item.id}')" title="Редактировать">✏️</button>
                <button class="btn-icon" onclick="deleteInstallation('${item.id}')" title="Удалить">🗑️</button>
            </td>
        </tr>
    `).join('');
    
    updateStats(data);
}

// Фильтрация
function filterTable() {
    const status = document.getElementById('statusFilter').value;
    const query = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = installations;
    
    if (status !== 'all') {
        filtered = filtered.filter(item => item.status === status);
    }
    
    if (query) {
        filtered = filtered.filter(item => 
            item.name.toLowerCase().includes(query) || 
            item.city.toLowerCase().includes(query) ||
            item.address.toLowerCase().includes(query)
        );
    }
    
    renderTable(filtered);
}

// --- Действия с объектами ---

// Добавить
function openAddModal() {
    document.getElementById('modalTitle').textContent = '➕ Добавить объект';
    document.getElementById('editId').value = '';
    document.getElementById('formName').value = '';
    document.getElementById('formCode').value = '';
    document.getElementById('formCity').value = '';
    document.getElementById('formAddress').value = '';
    document.getElementById('formStatus').value = 'active';
    document.getElementById('editModal').style.display = 'flex';
}

// Редактировать
function editInstallation(id) {
    const item = installations.find(i => i.id === id);
    if (!item) return;
    
    document.getElementById('modalTitle').textContent = '✏️ Редактировать объект';
    document.getElementById('editId').value = item.id;
    document.getElementById('formName').value = item.name;
    document.getElementById('formCode').value = item.unique_code;
    document.getElementById('formCity').value = item.city;
    document.getElementById('formAddress').value = item.address;
    document.getElementById('formStatus').value = item.status;
    document.getElementById('editModal').style.display = 'flex';
}

// Сохранить (из модалки)
function saveInstallation(e) {
    e.preventDefault();
    
    const id = document.getElementById('editId').value;
    const data = {
        id: id || String(Date.now()),
        unique_code: document.getElementById('formCode').value,
        name: document.getElementById('formName').value,
        city: document.getElementById('formCity').value,
        address: document.getElementById('formAddress').value,
        status: document.getElementById('formStatus').value,
        equipment_count: 0,
        next_maintenance: '—'
    };
    
    if (id) {
        // Редактирование
        const index = installations.findIndex(i => i.id === id);
        if (index !== -1) {
            installations[index] = { ...installations[index], ...data };
        }
    } else {
        // Создание
        installations.push(data);
    }
    
    closeModal();
    filterTable();
}

// Удалить
function deleteInstallation(id) {
    if (!confirm('Удалить объект?')) return;
    installations = installations.filter(item => item.id !== id);
    filterTable();
}

// Закрыть модалку
function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Просмотр (заглушка)
function viewInstallation(id) {
    alert(`🚧 Карточка объекта ${id}\nБудет реализована после интеграции с бэком`);
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    renderTable(installations);
    
    // Обработчики событий
    document.getElementById('statusFilter').addEventListener('change', filterTable);
    document.getElementById('searchInput').addEventListener('input', filterTable);
    document.getElementById('addBtn').addEventListener('click', openAddModal);
    document.getElementById('installForm').addEventListener('submit', saveInstallation);
    
    // Закрытие модалки по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
});