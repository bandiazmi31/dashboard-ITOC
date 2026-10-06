function createCard(title, value, subtitle = "", statusClass = "") {
    return `
        <div class="card">
            <div class="card-title">${title}</div>
            <div class="card-value">${value}</div>
            ${subtitle ? `<div class="card-subtitle">${subtitle}</div>` : ""}
            ${statusClass ? `<span class="pill ${statusClass}"></span>` : ""}
        </div>
    `;
}

function createPill(text, color = "info") {
    return `<span class="pill pill-${color}">${text}</span>`;
}

function createTable(headers, rows, onAction = null) {
    let html = `
        <table class="table">
            <thead>
                <tr>
    `;
    
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    
    if (onAction) html += `<th>Aksi</th>`;
    
    html += `</tr></thead><tbody>`;
    
    rows.forEach((row, idx) => {
        html += `<tr>`;
        row.forEach(cell => {
            html += `<td>${cell}</td>`;
        });
        if (onAction) {
            html += `<td>
                <button class="btn-sm" onclick="onAction(${idx})">Edit</button>
            </td>`;
        }
        html += `</tr>`;
    });
    
    html += `</tbody></table>`;
    return html;
}

function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add("removing");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createModal(title, content, onConfirm = null, onCancel = null) {
    const modal = document.createElement("div");
    modal.className = "modal active";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">${title}</div>
            <div class="modal-body">${content}</div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal').remove()">Batal</button>
                <button class="btn-primary" onclick="document.querySelector('.modal-confirm-btn') && document.querySelector('.modal-confirm-btn').click()">OK</button>
            </div>
        </div>
    `;
    
    if (onConfirm) {
        const confirmBtn = document.createElement("button");
        confirmBtn.className = "modal-confirm-btn";
        confirmBtn.style.display = "none";
        confirmBtn.onclick = () => {
            onConfirm();
            modal.remove();
        };
        modal.appendChild(confirmBtn);
    }
    
    document.body.appendChild(modal);
    
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.remove();
            onCancel && onCancel();
        }
    });
    
    return modal;
}

function formatDate(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("id-ID", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function formatTime(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleTimeString("id-ID");
}
