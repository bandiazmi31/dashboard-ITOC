async function apiCall(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        credentials: 'same-origin'
    });

    if (res.status === 401) {
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    const json = await res.json();

    if (!json.success) {
        throw new Error(json.error || 'Request failed');
    }

    return json.data;
}

async function apiGet(url) {
    return apiCall(url, { method: 'GET' });
}

async function apiPost(url, data) {
    return apiCall(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function apiPut(url, data) {
    return apiCall(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function apiDelete(url) {
    return apiCall(url, { method: 'DELETE' });
}
