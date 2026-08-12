// =======================================================
// Shared Campus Auth & Session Management Module
// =======================================================

window.campusAuth = {
    TOKEN_KEY: "campus_access_token",
    USER_KEY: "campus_user_data",

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY) || "";
    },

    setToken(token) {
        if (token) localStorage.setItem(this.TOKEN_KEY, token);
    },

    getUser() {
        try {
            const raw = localStorage.getItem(this.USER_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    },

    setUser(userData) {
        if (userData) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(userData));
        }
    },

    logout(redirectUrl) {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        const target = redirectUrl || (window.location.pathname.includes("/admin/") ? "login.html" : "login.html");
        window.location.href = target;
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    isAdmin() {
        const user = this.getUser();
        return user && user.role === "ADMIN";
    },

    requireStudentAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "login.html";
            return false;
        }
        return true;
    },

    requireAdminAuth() {
        if (!this.isLoggedIn() || !this.isAdmin()) {
            window.location.href = "login.html";
            return false;
        }
        return true;
    }
};
