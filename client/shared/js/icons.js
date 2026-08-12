// =======================================================
// CampusStore — Shared Custom SVG Icon System
// Minimal, single-color, clean geometric outline icons
// =======================================================

window.CampusIcons = {
    Clock(size = 18, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/></svg>`;
    },
    Delivery(size = 18, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="13" height="11" rx="2"/><polygon points="14 7 18 7 21 11 21 15 14 15"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/></svg>`;
    },
    Discount(size = 18, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 2.4 3.4-.5.5 3.4 2.4 2.4-1.5 3.1 1.5 3.1-2.4 2.4-.5 3.4-3.4-.5-2.4 2.4-3.1-1.5-3.1 1.5-2.4-2.4-3.4.5-.5-3.4-2.4-2.4 1.5-3.1-1.5-3.1 2.4-2.4.5-3.4 3.4.5z"/><line x1="9" y1="15" x2="15" y2="9"/><circle cx="9.5" cy="9.5" r=".5" fill="currentColor"/><circle cx="14.5" cy="14.5" r=".5" fill="currentColor"/></svg>`;
    },
    Cart(size = 18, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>`;
    },
    Location(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>`;
    },
    Flash(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
    },
    Search(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;
    },
    Snack(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3L2 19h20L12 3z"/><path d="M7 19c2.5-3 7.5-3 10 0"/></svg>`;
    },
    Roll(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11a8 8 0 0016 0H4z"/><path d="M4 11V7a2 2 0 012-2h12a2 2 0 012 2v4"/></svg>`;
    },
    Coffee(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8h1a4 4 0 010 8h-1"/><path d="M3 8h14v9a4 4 0 01-4 4H7a4 4 0 01-4-4V8z"/><line x1="6" y1="2" x2="6" y2="4"/><line x1="10" y1="2" x2="10" y2="4"/><line x1="14" y1="2" x2="14" y2="4"/></svg>`;
    },
    Burger(size = 16, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11a8 8 0 0116 0H4z"/><rect x="3" y="16" width="18" height="3" rx="1.5"/><line x1="4" y1="13.5" x2="20" y2="13.5"/></svg>`;
    },
    Outlet(size = 18, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/><line x1="3" y1="5" x2="3" y2="19"/><line x1="21" y1="5" x2="21" y2="19"/></svg>`;
    },
    VegDot(size = 14, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="12" cy="12" r="4" fill="#16a34a"/></svg>`;
    },
    NonVegTriangle(size = 14, cls = "") {
        return `<svg class="inline-block align-middle ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><polygon points="12 7 17 16 7 16" fill="#dc2626"/></svg>`;
    }
};
