// =======================================================
// Shared Campus Theme & Toast Notification Module
// =======================================================

window.toast = {
    show(msg, type = "info") {
        let container = document.getElementById("campus-toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "campus-toast-container";
            container.className = "fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none";
            document.body.appendChild(container);
        }

        const toastEl = document.createElement("div");
        const colors = {
            success: "bg-emerald-950 border-emerald-500/50 text-emerald-200",
            error: "bg-rose-950 border-rose-500/50 text-rose-200",
            info: "bg-cyan-950 border-cyan-500/50 text-cyan-200",
            warning: "bg-amber-950 border-amber-500/50 text-amber-200"
        };

        const icons = {
            success: "fa-circle-check text-emerald-400",
            error: "fa-triangle-exclamation text-rose-400",
            info: "fa-circle-info text-cyan-400",
            warning: "fa-bolt text-amber-400"
        };

        toastEl.className = `pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border text-xs font-bold shadow-2xl transition-all duration-300 transform translate-y-4 opacity-0 ${colors[type] || colors.info}`;
        toastEl.innerHTML = `
            <i class="fa-solid ${icons[type] || icons.info} text-base"></i>
            <span>${msg}</span>
        `;

        container.appendChild(toastEl);
        requestAnimationFrame(() => {
            toastEl.classList.remove("translate-y-4", "opacity-0");
        });

        setTimeout(() => {
            toastEl.classList.add("opacity-0", "translate-y-2");
            setTimeout(() => toastEl.remove(), 300);
        }, 3500);
    },

    success(msg) { this.show(msg, "success"); },
    error(msg) { this.show(msg, "error"); },
    info(msg) { this.show(msg, "info"); },
    warning(msg) { this.show(msg, "warning"); }
};

window.campusTheme = {
    init() {
        const saved = localStorage.getItem("campus_theme") || "dark";
        this.apply(saved);
    },
    apply(theme) {
        if (theme === "light") {
            document.documentElement.classList.add("light");
            document.documentElement.classList.remove("dark");
        } else {
            document.documentElement.classList.add("dark");
            document.documentElement.classList.remove("light");
        }
        localStorage.setItem("campus_theme", theme);
    },
    toggle() {
        const current = localStorage.getItem("campus_theme") === "light" ? "dark" : "light";
        this.apply(current);
        if (window.toast) window.toast.info(`Switched to ${current.toUpperCase()} mode`);
    }
};

document.addEventListener("DOMContentLoaded", () => window.campusTheme.init());
