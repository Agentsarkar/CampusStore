// =======================================================
// Shared Campus API Client (Centralized Fetch Wrapper)
// =======================================================

window.apiFetch = async function (endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : endpoint;

    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    const token = window.campusAuth ? window.campusAuth.getToken() : localStorage.getItem("campus_access_token");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
        method: options.method || "GET",
        headers,
        ...options
    };

    if (options.body && typeof options.body === "object") {
        config.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json().catch(() => ({}));

        if (response.status === 401 || response.status === 403) {
            console.warn(`Auth Error (${response.status}):`, data.detail || data.message);
        }

        if (!response.ok) {
            return {
                error: true,
                success: false,
                message: data.detail || data.message || `Server HTTP Error ${response.status}`,
                status: response.status,
                data: null
            };
        }

        return data;
    } catch (err) {
        console.error("API Network Error:", err);
        return {
            error: true,
            success: false,
            message: "Unable to reach server. Running in resilient mode.",
            data: null
        };
    }
};
