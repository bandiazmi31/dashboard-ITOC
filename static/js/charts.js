let charts = {};

function createLineChart(canvasId, labels, datasets, title = "") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets.map((ds, idx) => ({
                label: ds.label,
                data: ds.data,
                borderColor: ds.color || ['#0066cc', '#28a745', '#dc3545', '#ffc107'][idx],
                backgroundColor: (ds.color || ['#0066cc', '#28a745', '#dc3545', '#ffc107'][idx]) + '20',
                tension: 0.3,
                fill: false
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: !!title, text: title },
                legend: { display: true, position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
    
    return charts[canvasId];
}

function createBarChart(canvasId, labels, datasets, title = "") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets.map((ds, idx) => ({
                label: ds.label,
                data: ds.data,
                backgroundColor: ds.color || ['#0066cc', '#28a745', '#dc3545', '#ffc107'][idx]
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: !!title, text: title },
                legend: { display: true, position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
    
    return charts[canvasId];
}

function createDoughnutChart(canvasId, labels, data, title = "") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    const colors = ['#28a745', '#ffc107', '#dc3545', '#0066cc', '#6f42c1'];
    
    charts[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: !!title, text: title },
                legend: { display: true, position: 'right' }
            }
        }
    });
    
    return charts[canvasId];
}

function updateChart(chartId, newData) {
    if (charts[chartId]) {
        charts[chartId].data = newData;
        charts[chartId].update();
    }
}

function destroyChart(chartId) {
    if (charts[chartId]) {
        charts[chartId].destroy();
        delete charts[chartId];
    }
}
