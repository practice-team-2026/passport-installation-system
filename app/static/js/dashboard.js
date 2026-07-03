// app/static/js/dashboard.js
import { getDashboardStats } from './api.js';

let maintenanceChart = null;

async function loadDashboard() {
    try {
        const data = await getDashboardStats();
        updateKPICards(data);
        renderChart(data.chart);
        hideError();
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Не удалось загрузить данные дашборда. Проверьте, что сервер запущен (python run.py).');
    }
}

function updateKPICards(data) {
    document.getElementById('totalStats').textContent = data.total || 0;
    document.getElementById('activeStats').textContent = data.active || 0;
    document.getElementById('overdueStats').textContent = data.overdue || 0;
}

function renderChart(chartData) {
    const ctx = document.getElementById('maintenanceChart').getContext('2d');
    
    if (maintenanceChart) {
        maintenanceChart.destroy();
    }
    
    if (!chartData || !chartData.labels || chartData.labels.length === 0) {
        // Показываем заглушку, если данных нет
        maintenanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Нет данных'],
                datasets: [{
                    label: 'Запланировано ТО',
                    data: [0],
                    backgroundColor: '#e0e0e0',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Нет данных для отображения',
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });
        return;
    }
    
    maintenanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Запланировано ТО',
                data: chartData.values,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.7)',
                    'rgba(118, 75, 162, 0.7)',
                    'rgba(39, 174, 96, 0.7)',
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(241, 196, 15, 0.7)',
                    'rgba(52, 152, 219, 0.7)'
                ],
                borderColor: [
                    'rgba(102, 126, 234, 1)',
                    'rgba(118, 75, 162, 1)',
                    'rgba(39, 174, 96, 1)',
                    'rgba(231, 76, 60, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(52, 152, 219, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 14 },
                        padding: 20
                    }
                },
                title: {
                    display: true,
                    text: '📈 График технического обслуживания по месяцам',
                    font: { size: 18, weight: 'bold' },
                    padding: 20
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.08)'
                    }
                },
                x: {
                    ticks: {
                        font: { size: 12 }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function showError(message) {
    const errorDiv = document.getElementById('dashboardError');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('dashboardError').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', loadDashboard);