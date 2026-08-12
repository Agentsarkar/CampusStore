// =======================================================
// CampusStore — Student Frontend Engine
// Visual Identity: Warm Canvas (#FAF9F3), Forest Green (#004D2B), Lime Accent (#D7F000)
// Clean Custom SVG Iconography System & Real-World Floating Cart Bar
// =======================================================

const API_BASE_URL = ""; // Frontend served from same origin as API (port 8000)


// Global Application State
window.appState = {
    user: null,
    addresses: [],
    activeAddress: null,
    cart: JSON.parse(localStorage.getItem("guest_cart") || "[]"),
    categories: [],
    products: [],
    activeOrders: [],
    activeStore: "flash", // 'flash' or 'canteen'
    searchQuery: ""
};

// =======================================================
// HTML Escaper Utility
// =======================================================
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
window.escapeHtml = escapeHtml;

// =======================================================
// Campus Outlets & Fallback Catalog (Using Clean SVG Icons)
// =======================================================
window.dummyOutlets = [
    { id: "outlet_1", name: "Main Canteen", status: "Open · ~10 min", iconType: "Outlet" },
    { id: "outlet_2", name: "Nescafé Corner", status: "Open · ~10 min", iconType: "Coffee" },
    { id: "outlet_3", name: "Hostel Mess", status: "Open · ~10 min", iconType: "Roll" },
    { id: "outlet_4", name: "Quick Bite Kiosk", status: "Open · ~10 min", iconType: "Burger" }
];

window.dummyCategories = [
    { _id: "cat_flash_1", name: "Late-night munchies", subtitle: "Snacks, chips & midnight cravings", section: "flash", iconType: "Snack" },
    { _id: "cat_flash_2", name: "Instant Food & Noodles", subtitle: "Quick meals for study breaks", section: "flash", iconType: "Roll" },
    { _id: "cat_flash_3", name: "Groceries & Drinks", subtitle: "Fruits, dairy, snacks & daily essentials", section: "flash", iconType: "Burger" },
    { _id: "cat_flash_4", name: "Hostel Essentials", subtitle: "Personal care & room basics", section: "flash", iconType: "Outlet" },
    { _id: "cat_canteen_1", name: "Quick Snacks", subtitle: "Samosas, kachoris & warm snacks", section: "canteen", iconType: "Snack" },
    { _id: "cat_canteen_2", name: "Meals & Rolls", subtitle: "Kathi rolls, thalis & bowls", section: "canteen", iconType: "Roll" },
    { _id: "cat_canteen_3", name: "Chai & Coffee", subtitle: "Freshly brewed hot teas & coffees", section: "canteen", iconType: "Coffee" },
    { _id: "cat_canteen_4", name: "Fast Food", subtitle: "Burgers, fries & quick bites", section: "canteen", iconType: "Burger" }
];

window.dummyProducts = [
    {
        _id: "prod_f1",
        name: "Maggi 2-Minute Masala Noodles",
        image: ["https://images.unsplash.com/photo-1612927601601-6638404737ce?w=400&auto=format&fit=crop&q=80"],
        unit: "4-Pack · 280g",
        stock: 50,
        price: 56,
        discount: 0,
        description: "Classic 2-minute masala noodles for late-night study sessions.",
        category_id: "cat_flash_2",
        section: "flash"
    },
    {
        _id: "prod_f2",
        name: "Red Bull Energy Drink",
        image: ["https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&auto=format&fit=crop&q=80"],
        unit: "250ml Can",
        stock: 35,
        price: 125,
        discount: 0,
        description: "Vitalizes body and mind during exam review nights.",
        category_id: "cat_flash_3",
        section: "flash"
    },
    {
        _id: "prod_f3",
        name: "Lays Potato Chips - Cream & Onion",
        image: ["https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&auto=format&fit=crop&q=80"],
        unit: "90g Pack",
        stock: 40,
        price: 30,
        discount: 0,
        description: "Crispy American style cream & onion flavor potato chips.",
        category_id: "cat_flash_1",
        section: "flash"
    },
    {
        _id: "prod_f4",
        name: "Robusta Banana Pack",
        image: ["https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&auto=format&fit=crop&q=80"],
        unit: "500g",
        stock: 25,
        price: 49,
        discount: 0,
        description: "Fresh campus store bananas.",
        category_id: "cat_flash_3",
        section: "flash"
    },
    {
        _id: "prod_f5",
        name: "Toned Milk Pouch",
        image: ["https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&auto=format&fit=crop&q=80"],
        unit: "500ml",
        stock: 30,
        price: 32,
        discount: 0,
        description: "Fresh daily pasteurized milk.",
        category_id: "cat_flash_3",
        section: "flash"
    },
    {
        _id: "prod_c1",
        name: "Paneer Kathi Roll",
        image: ["https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400&auto=format&fit=crop&q=80"],
        unit: "1 Roll",
        stock: 30,
        price: 79,
        discount: 0,
        description: "Smoky grilled paneer tikka wrapped in a crisp paratha.",
        category_id: "cat_canteen_2",
        section: "canteen",
        food_type: "veg",
        outlet: "Quick Bite Kiosk"
    },
    {
        _id: "prod_c2",
        name: "Veg Samosa (2 pcs)",
        image: ["https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&auto=format&fit=crop&q=80"],
        unit: "Plate of 2",
        stock: 45,
        price: 25,
        discount: 0,
        description: "Crispy spiced potato samosas served hot with mint chutney.",
        category_id: "cat_canteen_1",
        section: "canteen",
        food_type: "veg",
        outlet: "Main Canteen"
    },
    {
        _id: "prod_c3",
        name: "Masala Chai",
        image: ["https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400&auto=format&fit=crop&q=80"],
        unit: "150ml Cup",
        stock: 60,
        price: 15,
        discount: 0,
        description: "Freshly brewed ginger cardamom tea.",
        category_id: "cat_canteen_3",
        section: "canteen",
        food_type: "veg",
        outlet: "Nescafé Corner"
    },
    {
        _id: "prod_c4",
        name: "Cheese Burger + Fries",
        image: ["https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&auto=format&fit=crop&q=80"],
        unit: "1 Meal",
        stock: 25,
        price: 119,
        discount: 0,
        description: "Classic cheese burger with a side of crispy fries.",
        category_id: "cat_canteen_4",
        section: "canteen",
        food_type: "veg",
        outlet: "Quick Bite Kiosk"
    }
];

// Base64 SVG Placeholder
window.getBrandedPlaceholderSvg = function(title = "Campus Item") {
    const cleanTitle = escapeHtml(String(title).substring(0, 25));
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200" fill="none"><rect width="300" height="200" fill="#F4F3EB"/><path d="M120 70L150 110L180 70" stroke="#8A988E" stroke-width="3" stroke-linecap="round"/><text x="50%" y="75%" dominant-baseline="middle" text-anchor="middle" fill="#526056" font-family="sans-serif" font-size="13">${cleanTitle}</text></svg>`;
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
};

// Toast Notification
window.toast = {
    show(message, type = "success") {
        const container = document.getElementById("toast-container") || (() => {
            const el = document.createElement("div");
            el.id = "toast-container";
            el.className = "fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none";
            document.body.appendChild(el);
            return el;
        })();

        const toastEl = document.createElement("div");
        toastEl.className = `px-4 py-2.5 rounded-xl shadow-lg text-white font-medium text-xs transition-all duration-200 transform translate-x-full ${
            type === "success" ? "bg-[#004D2B]" : type === "error" ? "bg-rose-700" : "bg-slate-800"
        }`;
        toastEl.innerText = message;
        container.appendChild(toastEl);

        setTimeout(() => toastEl.classList.remove("translate-x-full"), 10);
        setTimeout(() => {
            toastEl.classList.add("translate-x-full");
            setTimeout(() => toastEl.remove(), 250);
        }, 2500);
    },
    success(msg) { this.show(msg, "success"); },
    error(msg) { this.show(msg, "error"); },
    info(msg) { this.show(msg, "info"); }
};

// API Fetch Interceptor Wrapper
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    options.headers = options.headers || {};
    
    const accessToken = localStorage.getItem("campus_access_token");
    if (accessToken) {
        options.headers["Authorization"] = `Bearer ${accessToken}`;
    }
    
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }

    try {
        let response = await fetch(url, options);

        if (response.status === 401) {
            const refreshToken = localStorage.getItem("refreshToken");
            if (refreshToken) {
                const refreshRes = await fetch(`${API_BASE_URL}/api/user/refresh-token`, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${refreshToken}` }
                });
                
                if (refreshRes.ok) {
                    const data = await refreshRes.json();
                    if (data.success) {
                        localStorage.setItem("campus_access_token", data.data.accessToken);
                        options.headers["Authorization"] = `Bearer ${data.data.accessToken}`;
                        response = await fetch(url, options);
                    }
                } else {
                    localStorage.removeItem("campus_access_token");
                    localStorage.removeItem("refreshToken");
                    window.appState.user = null;
                    window.dispatchEvent(new CustomEvent("authStateChanged"));
                }
            }
        }

        // Handle non-JSON responses (e.g. 500 Internal Server Error plain text)
        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
            return { success: false, message: `Server error (${response.status})` };
        }

        const data = await response.json();
        
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
        console.warn("apiFetch error:", err.message);
        return { success: false, message: "Server unreachable" };
    }
}
window.apiFetch = apiFetch;

// User Profile & Address
async function fetchUserDetails() {
    const token = localStorage.getItem("campus_access_token");
    if (!token) {
        // No token — ensure header shows Login immediately
        window.dispatchEvent(new CustomEvent("authStateChanged"));
        return null;
    }
    
    const res = await apiFetch("/api/user/user-details");
    if (res.success && res.data) {
        window.appState.user = res.data;
        window.dispatchEvent(new CustomEvent("authStateChanged"));
        await fetchUserAddresses();
        await fetchUserOrders();
        return res.data;
    } else {
        // Token present but invalid/expired — clear it and show Login
        if (res.message && res.message.includes("401")) {
            localStorage.removeItem("campus_access_token");
            localStorage.removeItem("refreshToken");
        }
        window.appState.user = null;
        window.dispatchEvent(new CustomEvent("authStateChanged"));
        return null;
    }
}

async function fetchUserAddresses() {
    const token = localStorage.getItem("campus_access_token");
    if (!token) return [];

    const res = await apiFetch("/api/address/get");
    if (res.success && Array.isArray(res.data)) {
        window.appState.addresses = res.data;
        if (res.data.length > 0) {
            window.appState.activeAddress = res.data[0];
        }
        updateLocationDisplay();
        return res.data;
    }
    return [];
}

async function fetchUserOrders() {
    const token = localStorage.getItem("campus_access_token");
    if (!token) return [];

    const res = await apiFetch("/api/order/order-list");
    if (res.success && Array.isArray(res.data)) {
        window.appState.activeOrders = res.data.filter(o => {
            const st = o.order_status || o.delivery_status;
            return st !== "DELIVERED" && st !== "COMPLETED" && st !== "CANCELLED";
        });
        window.dispatchEvent(new CustomEvent("ordersUpdated"));
        return res.data;
    }
    return [];
}

async function logoutUser() {
    await apiFetch("/api/user/logout");
    localStorage.removeItem("campus_access_token");
    localStorage.removeItem("refreshToken");
    window.appState.user = null;
    window.appState.addresses = [];
    window.appState.activeAddress = null;
    window.appState.cart = [];
    localStorage.removeItem("guest_cart");
    window.toast.success("Logged out");
    window.dispatchEvent(new CustomEvent("authStateChanged"));
    updateCartUI();
    setTimeout(() => { window.location.href = "login.html"; }, 300);
}

function updateLocationDisplay() {
    const locTextEl = document.getElementById("header-location-text");
    const dropdownList = document.getElementById("location-dropdown-list");
    if (!locTextEl) return;

    if (window.appState.activeAddress) {
        const addr = window.appState.activeAddress;
        locTextEl.innerHTML = `<span>${addr.building_name} · Room ${addr.room_number}</span> <i class="fa-solid fa-chevron-down text-[8px] text-[#8A988E]"></i>`;
        locTextEl.className = "font-bold text-[#111713] text-xs truncate flex items-center gap-1 justify-end";
    } else {
        locTextEl.innerHTML = `<span>Select Location</span> <i class="fa-solid fa-chevron-down text-[8px] text-[#8A988E]"></i>`;
        locTextEl.className = "font-bold text-[#111713] text-xs truncate flex items-center gap-1 justify-end";
    }

    if (dropdownList) {
        if (!window.appState.addresses || window.appState.addresses.length === 0) {
            dropdownList.innerHTML = `<span class="text-[10px] text-[#8A988E] px-3 py-2 text-center">No locations saved</span>`;
        } else {
            dropdownList.innerHTML = window.appState.addresses.map((addr) => {
                const isActive = window.appState.activeAddress && window.appState.activeAddress._id === addr._id;
                return `
                    <div onclick="window.selectAddress('${addr._id}')" class="px-3 py-2 rounded-xl cursor-pointer hover:bg-[#FAF9F3] transition flex justify-between items-center ${isActive ? 'bg-[#FAF9F3] border border-[#004D2B]/20' : ''}">
                        <div class="flex flex-col">
                            <span class="font-bold text-[#111713] text-xs">${addr.building_name}</span>
                            <span class="text-[10px] text-[#526056]">Room ${addr.room_number}</span>
                        </div>
                        ${isActive ? '<i class="fa-solid fa-circle-check text-[#004D2B] text-xs"></i>' : ''}
                    </div>
                `;
            }).join("");
        }
    }
}

window.selectAddress = function(addrId) {
    const addr = window.appState.addresses.find(a => a._id === addrId);
    if (addr) {
        window.appState.activeAddress = addr;
        updateLocationDisplay();
        document.getElementById("location-dropdown-panel")?.classList.add("hidden");
    }
};

// Shopping Cart Actions
async function fetchCart() {
    if (localStorage.getItem("campus_access_token")) {
        const res = await apiFetch("/api/cart/get");
        if (res.success && Array.isArray(res.data)) {
            window.appState.cart = res.data;
            updateCartUI();
            return;
        }
    }
    const localCart = JSON.parse(localStorage.getItem("guest_cart") || "[]");
    window.appState.cart = localCart;
    updateCartUI();
}

async function addToCart(productId) {
    const product = window.dummyProducts.find(p => p._id === productId) || window.appState.products.find(p => p._id === productId);
    if (!product) return;
    
    // Determine product category
    const productCat = product.category_id || (product.category && product.category.length > 0 ? product.category[0]._id : null);

    // Enforce single-outlet orders
    if (window.appState.cart.length > 0) {
        const firstCartItem = window.appState.cart[0];
        const prodIdObj = firstCartItem.productId || {};
        const existingCat = prodIdObj.category_id || (prodIdObj.category && prodIdObj.category.length > 0 ? prodIdObj.category[0]._id : null);
        
        if (existingCat && productCat && existingCat !== productCat) {
            window.toast.error("You can only order from one outlet at a time! Please clear your cart first.");
            return;
        }
    }

    if (localStorage.getItem("campus_access_token")) {
        const res = await apiFetch("/api/cart/create", {
            method: "POST",
            body: { productId }
        });
        if (res.success) {
            window.toast.success(`Added ${product.name}`);
            await fetchCart();
            return;
        }
    }

    let localCart = JSON.parse(localStorage.getItem("guest_cart") || "[]");
    const existingIndex = localCart.findIndex(item => item.productId && (item.productId._id === productId || item.productId === productId));
    
    if (existingIndex > -1) {
        localCart[existingIndex].quantity += 1;
    } else {
        localCart.push({
            _id: "cart_item_" + Date.now(),
            productId: product,
            quantity: 1
        });
    }

    localStorage.setItem("guest_cart", JSON.stringify(localCart));
    window.appState.cart = localCart;
    window.toast.success(`Added ${product.name}`);
    updateCartUI();
}

async function updateCartQty(cartId, newQty) {
    if (localStorage.getItem("campus_access_token")) {
        const res = await apiFetch("/api/cart/update-qty", {
            method: "PUT",
            body: { id: cartId, qty: newQty }
        });
        if (res.success) {
            await fetchCart();
            return;
        }
    }

    let localCart = JSON.parse(localStorage.getItem("guest_cart") || "[]");
    if (newQty <= 0) {
        localCart = localCart.filter(item => item._id !== cartId);
    } else {
        const idx = localCart.findIndex(item => item._id === cartId);
        if (idx > -1) localCart[idx].quantity = newQty;
    }

    localStorage.setItem("guest_cart", JSON.stringify(localCart));
    window.appState.cart = localCart;
    updateCartUI();
}

async function removeCartItem(cartId) {
    await updateCartQty(cartId, 0);
    window.toast.info("Item removed");
}

window.addToCart = addToCart;
window.updateCartQty = updateCartQty;
window.removeCartItem = removeCartItem;

// Categories & Products Data Fetchers
async function fetchCategories() {
    const res = await apiFetch("/api/category/get");
    if (res.success && res.data && res.data.length > 0) {
        window.appState.categories = res.data;
    } else {
        window.appState.categories = window.dummyCategories;
    }
    window.dispatchEvent(new CustomEvent("categoriesLoaded"));
}

async function fetchProducts() {
    const res = await apiFetch("/api/product/get", {
        method: "POST",
        body: { page: 1, limit: 50, search: "" }
    });
    if (res.success && res.data && res.data.length > 0) {
        window.appState.products = res.data;
    } else {
        window.appState.products = window.dummyProducts;
    }
    window.dispatchEvent(new CustomEvent("productsLoaded"));
}

window.getCategoriesBySection = function(section) {
    const cats = window.appState.categories.length > 0 ? window.appState.categories : window.dummyCategories;
    return cats.filter(c => (c.section || "flash") === section);
};

window.getProductsBySection = function(section) {
    const prods = window.appState.products.length > 0 ? window.appState.products : window.dummyProducts;
    return prods.filter(p => (p.section || "flash") === section);
};

// Compact Product Card Renderer
window.renderProductCardHtml = function(product) {
    const name = escapeHtml(product.name || 'Campus Item');
    const unit = escapeHtml(product.unit || (product.section === 'canteen' ? 'Serves 1' : '1 Unit'));
    const outletName = escapeHtml(product.outlet || (product.section === 'canteen' ? 'Main Canteen' : 'Campus Hub'));
    const price = Number(product.price) || 0;
    const discount = Number(product.discount) || 0;
    const discountedPrice = Math.max(0, Math.ceil(price - (price * discount) / 100));

    const cartItem = window.appState.cart.find(item => {
        const pId = (item.productId && typeof item.productId === "object") ? item.productId._id : item.productId;
        return pId === product._id;
    });

    const inCart = !!cartItem;
    const qty = inCart ? cartItem.quantity : 0;
    const cartId = inCart ? cartItem._id : "";

    const placeholder = window.getBrandedPlaceholderSvg(product.name);
    let rawImgUrl = (product.image && product.image.length > 0 && typeof product.image[0] === 'string' && product.image[0].trim()) 
        ? product.image[0].trim() 
        : '';

    const mainImg = rawImgUrl ? escapeHtml(rawImgUrl) : placeholder;

    let actionBtnHtml = "";
    if (product.stock === 0) {
        actionBtnHtml = `<span class="text-rose-600 text-[11px] font-medium block text-center py-1 bg-rose-50 rounded-lg">Sold out</span>`;
    } else if (inCart) {
        actionBtnHtml = `
            <div class="flex items-center justify-between w-full border border-[#004D2B] bg-[#004D2B] rounded-lg text-white font-semibold text-xs overflow-hidden">
                <button onclick="event.preventDefault(); event.stopPropagation(); window.updateCartQty('${escapeHtml(cartId)}', ${qty - 1})" class="px-2.5 py-1 hover:bg-[#003B21] transition">
                    -
                </button>
                <span class="px-1 text-xs">${qty}</span>
                <button onclick="event.preventDefault(); event.stopPropagation(); window.updateCartQty('${escapeHtml(cartId)}', ${qty + 1})" class="px-2.5 py-1 hover:bg-[#003B21] transition">
                    +
                </button>
            </div>
        `;
    } else {
        actionBtnHtml = `
            <button onclick="event.preventDefault(); event.stopPropagation(); window.addToCart('${escapeHtml(product._id)}')" 
                class="w-full bg-[#FAF9F3] hover:bg-[#004D2B] hover:text-white border border-[#E8E7DF] text-[#004D2B] font-bold py-1 px-2.5 rounded-lg transition text-xs text-center">
                + ADD
            </button>
        `;
    }

    const flashSpeedBadge = window.CampusIcons ? window.CampusIcons.Flash(12, 'text-[#004D2B] mr-0.5') : '';

    return `
        <div onclick="window.location.href='product.html?id=${escapeHtml(product._id)}'" class="campus-card group flex flex-col overflow-hidden cursor-pointer p-3 gap-2">
            <div class="relative h-36 w-full bg-[#FFFFFF] rounded-xl overflow-hidden flex items-center justify-center p-2">
                <img src="${mainImg}" onerror="this.onerror=null; this.src='${placeholder}';" class="max-h-full max-w-full object-contain group-hover:scale-105 transition-transform duration-200" loading="lazy" alt="${name}">
            </div>
            <div class="flex flex-col flex-1 gap-1 min-w-0">
                <div class="flex items-center gap-1 text-[10px] font-bold text-[#004D2B] uppercase tracking-wider">
                    ${flashSpeedBadge}
                    <span>10 MINS</span>
                </div>
                <h4 class="font-bold text-xs leading-snug line-clamp-2 text-[#111713]">${name}</h4>
                <p class="text-[11px] text-[#526056] font-normal line-clamp-1">${outletName}</p>
                <div class="flex items-center justify-between gap-2 mt-auto pt-2 border-t border-[#E8E7DF]">
                    <span class="font-bold text-sm text-[#111713]">₹${discountedPrice}</span>
                    <div class="w-18">${actionBtnHtml}</div>
                </div>
            </div>
        </div>
    `;
};

function getCartTotals() {
    let totalQty = 0;
    let totalPrice = 0;
    window.appState.cart.forEach(item => {
        const prod = item.productId;
        if (prod && typeof prod === "object") {
            const price = Number(prod.price) || 0;
            const discount = Number(prod.discount) || 0;
            const discountedPrice = Math.max(0, Math.ceil(price - (price * discount) / 100));
            totalQty += item.quantity;
            totalPrice += discountedPrice * item.quantity;
        }
    });
    return { totalQty, totalPrice };
}

function updateFloatingCartBar(totalQty, totalPrice) {
    let bar = document.getElementById("floating-bottom-cart-bar");
    if (!bar) {
        bar = document.createElement("div");
        bar.id = "floating-bottom-cart-bar";
        bar.className = "fixed bottom-5 left-1/2 transform -translate-x-1/2 z-50 w-[92%] max-w-md bg-[#004D2B] text-white shadow-2xl rounded-2xl p-3 flex items-center justify-between transition-all duration-300 pointer-events-auto border border-white/10 hidden";
        document.body.appendChild(bar);
    }

    if (totalQty > 0) {
        const cartIconSvg = window.CampusIcons ? window.CampusIcons.Cart(16, 'text-white') : '';
        bar.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-white/15 flex items-center justify-center font-bold text-xs">
                    ${cartIconSvg}
                </div>
                <div>
                    <span class="font-extrabold text-xs text-white">${totalQty} ${totalQty === 1 ? 'Item' : 'Items'} · ₹${totalPrice}</span>
                    <p class="text-[10px] text-[#E6F0EB] font-normal">Hostel block delivery ready</p>
                </div>
            </div>
            <button onclick="toggleCartDrawer(true)" class="bg-[#D7F000] hover:bg-[#c2d800] text-[#111713] font-extrabold text-xs px-4 py-2 rounded-xl transition flex items-center gap-1 active:scale-95 shadow-sm">
                View Cart &rarr;
            </button>
        `;
        const drawer = document.getElementById("cart-drawer");
        const isDrawerOpen = drawer && !drawer.classList.contains("translate-x-full");
        if (!isDrawerOpen) {
            bar.classList.remove("hidden", "translate-y-10", "opacity-0", "pointer-events-none");
            bar.classList.add("translate-y-0", "opacity-100");
        } else {
            bar.classList.add("opacity-0", "pointer-events-none");
        }
    } else {
        bar.classList.add("hidden", "translate-y-10", "opacity-0", "pointer-events-none");
        bar.classList.remove("translate-y-0", "opacity-100");
    }
}

function updateCartUI() {
    const { totalQty, totalPrice } = getCartTotals();
    const cartCountBadge = document.getElementById("cart-count-badge");
    const cartTextDesc = document.getElementById("cart-text-desc");
    
    if (cartCountBadge) {
        cartCountBadge.innerText = totalQty;
        cartCountBadge.classList.toggle("hidden", totalQty === 0);
    }
    if (cartTextDesc) {
        if (totalQty > 0) {
            cartTextDesc.innerHTML = `<span class="block text-xs font-bold text-[#004D2B]">₹${totalPrice}</span>`;
        } else {
            cartTextDesc.innerHTML = `<span class="block text-xs font-semibold text-[#111713]">Cart</span>`;
        }
    }

    updateFloatingCartBar(totalQty, totalPrice);

    window.dispatchEvent(new CustomEvent("cartUpdated", { detail: { cart: window.appState.cart, totalQty, totalPrice } }));
}

// =======================================================
// Premium Header Layout
// =======================================================
function injectLayouts() {
    const locIcon = window.CampusIcons ? window.CampusIcons.Location(14, 'text-[#004D2B] inline-block mr-1') : '';
    const cartIcon = window.CampusIcons ? window.CampusIcons.Cart(18, 'text-[#004D2B] inline-block mr-1') : '';
    const searchIcon = window.CampusIcons ? window.CampusIcons.Search(14, 'text-[#8A988E]') : '';

    const headerHTML = `
        <header class="sticky top-0 z-40 bg-[#FAF9F3]/95 backdrop-blur-md border-b border-[#E8E7DF]" id="main-app-header">
            <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
                <!-- Brand Wordmark -->
                <a href="/student/index.html" class="flex items-center gap-1.5 flex-shrink-0">
                    <span class="font-extrabold text-lg tracking-tight text-[#111713]">Campus<span class="text-[#004D2B]">Store</span></span>
                </a>

                <!-- Desktop Search Field -->
                <div class="hidden md:block flex-1 max-w-lg mx-2">
                    <form id="desktop-search-form" class="relative flex items-center">
                        <div class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none flex items-center justify-center">${searchIcon}</div>
                        <input type="text" id="desktop-search-input" placeholder="Search Maggi, milk, cold coffee, stationery..." 
                            class="w-full bg-[#FFFFFF] border border-[#E8E7DF] py-2 pl-10 pr-4 rounded-xl text-xs text-[#111713] placeholder-[#8A988E] focus:outline-none focus:border-[#004D2B] transition shadow-2xs">
                    </form>
                </div>

                <!-- Right Delivery Location & Account / Cart -->
                <div class="flex items-center gap-4 text-xs flex-shrink-0">
                    <!-- Delivery Location -->
                    <!-- Delivery Location -->
                    <div class="relative hidden sm:flex items-center gap-1.5 border-r border-[#E8E7DF] pr-4 cursor-pointer select-none" id="location-menu-root">
                        ${locIcon}
                        <div class="flex flex-col text-right leading-tight">
                            <span class="text-[10px] uppercase font-semibold tracking-wider text-[#8A988E]">Delivering to</span>
                            <span class="font-bold text-[#111713] flex items-center gap-1" id="header-location-text">
                                <span>Hostel Block B · Room 304</span>
                                <i class="fa-solid fa-chevron-down text-[8px] text-[#8A988E]"></i>
                            </span>
                        </div>
                        <div id="location-dropdown-panel" class="hidden absolute left-0 top-11 bg-white shadow-xl rounded-2xl border border-[#E8E7DF] p-2 min-w-[220px] z-50">
                            <div class="px-3 py-2 border-b border-[#E8E7DF] mb-1">
                                <span class="text-[10px] font-black uppercase text-[#8A988E]">Saved Locations</span>
                            </div>
                            <div id="location-dropdown-list" class="flex flex-col gap-1 max-h-48 overflow-y-auto no-scrollbar">
                                <!-- Populated dynamically -->
                            </div>
                            <a href="dashboard.html?tab=address" class="block w-full text-center mt-2 pt-2 border-t border-[#E8E7DF] text-xs font-bold text-[#004D2B] hover:underline">Manage Locations</a>
                        </div>
                    </div>

                    <!-- User Profile -->
                    <div class="relative" id="user-menu-root">
                        <a href="/student/login.html" id="guest-login-btn" class="hidden font-bold text-[#004D2B] hover:underline">Log in</a>
                        
                        <div id="user-profile-dropdown" class="hidden flex items-center gap-1 cursor-pointer select-none border border-[#E8E7DF] bg-[#FFFFFF] px-3 py-1.5 rounded-xl hover:bg-white transition shadow-2xs">
                            <span class="font-semibold text-[#111713]" id="header-user-name">Account</span>
                        </div>
                        
                        <div id="user-dropdown-panel" class="hidden absolute right-0 top-11 bg-white shadow-xl rounded-2xl border border-[#E8E7DF] p-2 min-w-[160px] z-50">
                            <div class="flex flex-col text-xs font-medium text-[#111713]" id="user-dropdown-links">
                                <a href="/admin/index.html" id="admin-dashboard-link" class="hidden hover:bg-amber-50 px-3 py-2 rounded-xl text-amber-700 font-bold mb-1"><i class="fa-solid fa-sliders mr-1"></i> Admin Console</a>
                                <a href="/canteen/canteenpanel.html" id="operator-dashboard-link" class="hidden hover:bg-emerald-50 px-3 py-2 rounded-xl text-emerald-700 font-bold mb-1"><i class="fa-solid fa-store mr-1"></i> Operator Panel</a>
                                <a href="/print-operator.html" id="print-operator-dashboard-link" class="hidden hover:bg-blue-50 px-3 py-2 rounded-xl text-blue-700 font-bold mb-1"><i class="fa-solid fa-print mr-1"></i> Print Operator Panel</a>
                                <a href="/student/dashboard.html?tab=orders" class="hover:bg-[#FAF9F3] px-3 py-2 rounded-xl">My Orders</a>
                                <a href="/student/dashboard.html?tab=address" class="hover:bg-[#FAF9F3] px-3 py-2 rounded-xl">Locations</a>
                                <a href="/student/dashboard.html?tab=profile" class="hover:bg-[#FAF9F3] px-3 py-2 rounded-xl">Profile</a>
                                <div class="border-t border-[#E8E7DF] my-1"></div>
                                <button onclick="logoutUser()" class="text-left w-full hover:bg-rose-50 px-3 py-2 rounded-xl text-rose-600 font-bold">Logout</button>
                            </div>
                        </div>
                    </div>

                    <!-- Cart Drawer Trigger Button -->
                    <button onclick="toggleCartDrawer(true)" class="flex items-center gap-1.5 border border-[#E8E7DF] bg-[#FFFFFF] hover:border-[#004D2B] px-3.5 py-1.5 rounded-xl font-bold text-xs transition shadow-2xs">
                        ${cartIcon}
                        <div class="relative">
                            <span class="text-[#111713]">Cart</span>
                            <span id="cart-count-badge" class="absolute -top-2.5 -right-3 bg-[#004D2B] text-white rounded-full text-[9px] w-4 h-4 flex items-center justify-center font-bold hidden">0</span>
                        </div>
                        <div id="cart-text-desc" class="hidden sm:block"></div>
                    </button>
                </div>
            </div>

            <!-- Mobile Search Bar -->
            <div class="px-4 pb-2.5 md:hidden">
                <form id="mobile-search-form" class="relative flex items-center">
                    <div class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none flex items-center justify-center">${searchIcon}</div>
                    <input type="text" id="mobile-search-input" placeholder="Search Maggi, milk, cold coffee..." 
                        class="w-full bg-[#FFFFFF] border border-[#E8E7DF] py-2 pl-10 pr-3.5 rounded-xl text-xs text-[#111713] placeholder-[#8A988E] focus:outline-none focus:border-[#004D2B]">
                </form>
            </div>
        </header>

        <!-- Cart Drawer Panel -->
        <div id="cart-drawer-backdrop" class="fixed inset-0 bg-[#111713]/40 z-[70] transition-opacity duration-200 opacity-0 pointer-events-none" onclick="toggleCartDrawer(false)"></div>
        <div id="cart-drawer" class="fixed right-0 top-0 h-full w-full max-w-xs bg-white text-[#111713] shadow-2xl z-[75] transform translate-x-full transition-transform duration-200 flex flex-col border-l border-[#E8E7DF]">
            <div class="p-4 border-b border-[#E8E7DF] flex justify-between items-center bg-[#FAF9F3]">
                <div class="flex items-center gap-1.5">
                    ${cartIcon}
                    <h3 class="font-bold text-sm text-[#111713]">Your Basket</h3>
                </div>
                <button onclick="toggleCartDrawer(false)" class="text-[#8A988E] hover:text-[#111713] font-bold text-xs">Close</button>
            </div>
            <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-2.5" id="cart-drawer-items"></div>
            <div class="p-4 pb-8 sm:pb-4 border-t border-[#E8E7DF] bg-[#FAF9F3] sticky bottom-0">
                <div class="flex justify-between font-bold text-sm mb-3">
                    <span>Total:</span>
                    <span id="cart-drawer-total" class="text-[#004D2B]">₹0</span>
                </div>
                <a href="checkout.html" class="block w-full bg-[#004D2B] hover:bg-[#003B21] text-white text-center py-3 rounded-xl font-bold text-xs transition active:scale-98 shadow-sm">
                    Proceed to Checkout
                </a>
            </div>
        </div>
    `;

    const footerHTML = `
        <footer class="bg-[#FAF9F3] border-t border-[#E8E7DF] py-8 mt-16 text-xs text-[#526056]" id="main-app-footer">
            <div class="max-w-6xl mx-auto px-4 text-center space-y-3">
                <span class="font-extrabold text-base text-[#111713]">Campus<span class="text-[#004D2B]">Store</span></span>
                <p class="text-xs text-[#526056]">Food from the canteen. Essentials to your room.</p>
                <div class="flex justify-center gap-6 font-semibold text-[#111713]">
                    <a href="/student/index.html" class="hover:text-[#004D2B]">Campus Flash</a>
                    <a href="/canteen/index.html" class="hover:text-[#004D2B]">Campus Canteen</a>
                    <a href="/student/dashboard.html" class="hover:text-[#004D2B]">Student Account</a>
                </div>
                <p class="text-[11px] text-[#8A988E]">&copy; ${new Date().getFullYear()} CampusStore Platform</p>
            </div>
        </footer>

        <!-- Mobile Navigation -->
        <nav class="fixed bottom-0 left-0 right-0 z-40 bg-[#FAF9F3] border-t border-[#E8E7DF] sm:hidden flex justify-around py-2.5 px-2 text-xs text-[#526056]">
            <a href="/student/index.html" class="flex flex-col items-center font-bold hover:text-[#004D2B]">Home</a>
            <a href="search.html" class="flex flex-col items-center font-bold hover:text-[#004D2B]">Explore</a>
            <a href="dashboard.html?tab=orders" class="flex flex-col items-center font-bold hover:text-[#004D2B]">Orders</a>
            <a href="dashboard.html?tab=profile" class="flex flex-col items-center font-bold hover:text-[#004D2B]">Profile</a>
        </nav>
    `;

    const hc = document.getElementById("header-container");
    const fc = document.getElementById("footer-container");
    if (hc) hc.innerHTML = headerHTML;
    if (fc) fc.innerHTML = footerHTML;

    setupHeaderInteractions();
}

function setupHeaderInteractions() {
    const profileBtn = document.getElementById("user-profile-dropdown");
    const dropdownPanel = document.getElementById("user-dropdown-panel");
    if (profileBtn && dropdownPanel) {
        profileBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdownPanel.classList.toggle("hidden");
            document.getElementById("location-dropdown-panel")?.classList.add("hidden");
        });
    }

    const locMenuRoot = document.getElementById("location-menu-root");
    const locDropdown = document.getElementById("location-dropdown-panel");
    if (locMenuRoot && locDropdown) {
        locMenuRoot.addEventListener("click", (e) => {
            e.stopPropagation();
            locDropdown.classList.toggle("hidden");
            dropdownPanel?.classList.add("hidden");
        });
    }

    document.addEventListener("click", (e) => {
        if (profileBtn && dropdownPanel && !profileBtn.contains(e.target) && !dropdownPanel.contains(e.target)) {
            dropdownPanel.classList.add("hidden");
        }
        if (locMenuRoot && locDropdown && !locMenuRoot.contains(e.target) && !locDropdown.contains(e.target)) {
            locDropdown.classList.add("hidden");
        }
    });

    const updateAuthHeader = () => {
        const user = window.appState.user;
        const guestBtn = document.getElementById("guest-login-btn");
        const profileDropdown = document.getElementById("user-profile-dropdown");
        const userNameEl = document.getElementById("header-user-name");
        const adminLink = document.getElementById("admin-dashboard-link");

        if (user) {
            if (guestBtn) guestBtn.classList.add("hidden");
            if (profileDropdown) profileDropdown.classList.remove("hidden");
            if (userNameEl) userNameEl.innerText = user.name || "Student";
            
            if (adminLink) {
                if (user.role === "ADMIN") {
                    adminLink.classList.remove("hidden");
                } else {
                    adminLink.classList.add("hidden");
                }
            }
            const opLink = document.getElementById("operator-dashboard-link");
            if (opLink) {
                if (user.role === "CANTEEN_OP" || user.role === "ADMIN") {
                    opLink.classList.remove("hidden");
                } else {
                    opLink.classList.add("hidden");
                }
            }
            const printOpLink = document.getElementById("print-operator-dashboard-link");
            if (printOpLink) {
                if (user.role === "PRINT_OP" || user.role === "PRINT" || user.role === "ADMIN") {
                    printOpLink.classList.remove("hidden");
                } else {
                    printOpLink.classList.add("hidden");
                }
            }
        } else {
            if (guestBtn) guestBtn.classList.remove("hidden");
            if (profileDropdown) profileDropdown.classList.add("hidden");
            if (adminLink) adminLink.classList.add("hidden");
            const opLink = document.getElementById("operator-dashboard-link");
            if (opLink) opLink.classList.add("hidden");
            const printOpLink = document.getElementById("print-operator-dashboard-link");
            if (printOpLink) printOpLink.classList.add("hidden");
        }
    };

    window.addEventListener("authStateChanged", updateAuthHeader);
    updateAuthHeader();

    const searchFormHandler = (e, inputId) => {
        e.preventDefault();
        const input = document.getElementById(inputId);
        if (input && input.value.trim()) {
            window.location.href = `search.html?q=${encodeURIComponent(input.value.trim())}`;
        }
    };
    
    const dForm = document.getElementById("desktop-search-form");
    if (dForm) dForm.addEventListener("submit", (e) => searchFormHandler(e, "desktop-search-input"));

    const mForm = document.getElementById("mobile-search-form");
    if (mForm) mForm.addEventListener("submit", (e) => searchFormHandler(e, "mobile-search-input"));
}

window.toggleCartDrawer = function(open) {
    const backdrop = document.getElementById("cart-drawer-backdrop");
    const drawer = document.getElementById("cart-drawer");
    const floatingBar = document.getElementById("floating-bottom-cart-bar");

    if (open) {
        if (backdrop) {
            backdrop.classList.remove("pointer-events-none", "opacity-0");
            backdrop.classList.add("opacity-100");
        }
        if (drawer) {
            drawer.classList.remove("translate-x-full");
        }
        if (floatingBar) {
            floatingBar.classList.add("opacity-0", "pointer-events-none");
        }
    } else {
        if (backdrop) {
            backdrop.classList.add("pointer-events-none", "opacity-0");
            backdrop.classList.remove("opacity-100");
        }
        if (drawer) {
            drawer.classList.add("translate-x-full");
        }
        if (floatingBar && window.appState && window.appState.cart && window.appState.cart.length > 0) {
            floatingBar.classList.remove("opacity-0", "pointer-events-none");
        }
    }
};

window.switchStoreMode = function(storeMode) {
    window.appState.activeStore = storeMode;
    window.dispatchEvent(new CustomEvent("storeModeChanged", { detail: { mode: storeMode } }));
};

// Cart Drawer Renderer
window.addEventListener("cartUpdated", (e) => {
    const { cart, totalPrice } = e.detail;
    const itemsContainer = document.getElementById("cart-drawer-items");
    const totalEl = document.getElementById("cart-drawer-total");
    
    if (totalEl) totalEl.innerText = `₹${totalPrice}`;
    if (!itemsContainer) return;
    
    if (cart.length === 0) {
        itemsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center h-40 text-[#8A988E] text-center p-4">
                <p class="font-bold text-xs">Your basket is empty</p>
            </div>
        `;
        return;
    }
    
    itemsContainer.innerHTML = "";
    cart.forEach(item => {
        const prod = item.productId;
        if (!prod || typeof prod !== "object") return;

        const name = escapeHtml(prod.name || 'Campus Item');
        const price = Number(prod.price) || 0;
        const discount = Number(prod.discount) || 0;
        const discountedPrice = Math.max(0, Math.ceil(price - (price * discount) / 100));

        const placeholder = window.getBrandedPlaceholderSvg(prod.name);
        let rawImgUrl = (prod.image && prod.image.length > 0 && typeof prod.image[0] === 'string' && prod.image[0].trim()) 
            ? prod.image[0].trim() 
            : '';
        const mainImg = rawImgUrl ? escapeHtml(rawImgUrl) : placeholder;

        const card = document.createElement("div");
        card.className = "flex gap-2.5 p-2.5 rounded-xl border border-[#E8E7DF] items-center bg-white";
        card.innerHTML = `
            <div class="relative w-12 h-12 rounded-lg bg-[#FAF9F3] p-1 flex-shrink-0 flex items-center justify-center">
                <img src="${mainImg}" onerror="this.onerror=null; this.src='${placeholder}';" class="max-h-full max-w-full object-contain" alt="${name}">
            </div>
            <div class="flex-1 min-w-0">
                <h4 class="font-bold text-[#111713] text-xs truncate">${name}</h4>
                <div class="flex items-baseline gap-1 mt-0.5">
                    <span class="font-bold text-xs text-[#004D2B]">₹${discountedPrice}</span>
                    ${discount > 0 ? `<span class="text-[10px] text-[#8A988E] line-through">₹${price}</span>` : ""}
                </div>
            </div>
            <div class="flex items-center border border-[#E8E7DF] rounded-lg">
                <button onclick="updateCartQty('${escapeHtml(item._id)}', ${item.quantity - 1})" class="px-2 py-1 text-[#111713] text-xs hover:bg-[#FAF9F3]">
                    -
                </button>
                <span class="px-1.5 font-bold text-xs text-[#111713]">${item.quantity}</span>
                <button onclick="updateCartQty('${escapeHtml(item._id)}', ${item.quantity + 1})" class="px-2 py-1 text-[#111713] text-xs hover:bg-[#FAF9F3]">
                    +
                </button>
            </div>
            <button onclick="removeCartItem('${escapeHtml(item._id)}')" class="text-[#8A988E] hover:text-rose-600 p-1 text-xs">
                ×
            </button>
        `;
        itemsContainer.appendChild(card);
    });
});

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
    injectLayouts();
    
    const token = localStorage.getItem("campus_access_token");
    console.log("[CampusStore] Token present:", !!token, token ? `(${token.substring(0,20)}...)` : "(none)");
    
    const user = await fetchUserDetails();
    console.log("[CampusStore] User after fetchUserDetails:", user ? user.name : "null (not logged in)");
    
    await fetchCategories();
    await fetchProducts();
    await fetchCart();
});
