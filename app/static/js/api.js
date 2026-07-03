// app/static/js/api.js
// Единый слой для общения с бэкендом

const API_BASE = 'http://localhost:5000/api';

/**
 * Получить список всех установок
 */
export async function getInstallations() {
    const response = await fetch(`${API_BASE}/installations`);
    if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.status}`);
    }
    return response.json();
}

/**
 * Получить одну установку по ID
 */
export async function getInstallation(id) {
    const response = await fetch(`${API_BASE}/installations/${id}`);
    if (!response.ok) {
        throw new Error(`Ошибка загрузки объекта: ${response.status}`);
    }
    return response.json();
}

/**
 * Создать новую установку
 */
export async function createInstallation(data) {
    const response = await fetch(`${API_BASE}/installations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Ошибка создания');
    }
    return response.json();
}

/**
 * Обновить установку
 */
export async function updateInstallation(id, data) {
    const response = await fetch(`${API_BASE}/installations/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Ошибка обновления');
    }
    return response.json();
}

/**
 * Удалить (архивировать) установку
 */
export async function deleteInstallation(id) {
    const response = await fetch(`${API_BASE}/installations/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Ошибка удаления');
    }
    return response.json();
}

/**
 * Получить статистику для дашборда
 */
export async function getDashboardStats() {
    const response = await fetch(`${API_BASE}/dashboard/stats`);
    if (!response.ok) {
        throw new Error(`Ошибка загрузки статистики: ${response.status}`);
    }
    return response.json();
}