// =======================================================
// Campus Canteen — Student Ordering Flow
// client/canteen/js/canteen-order.js
// =======================================================

const canteenOrder = {
    outlets: [],
    selectedOutlet: null,
    menu: [],
    cart: [],              // Local cart state
    cartOutletId: null     // Which outlet the cart belongs to
};

document.addEventListener("DOMContentLoaded", async () => {
    await loadOutlets();
    await syncCartFromServer();
});

// -------------------------------------------------------
// Load Outlets
// -------------------------------------------------------
async function loadOutlets() {
    const res = await window.apiFetch("/api/canteen/outlets");
    if (!res.success || !res.data.length) {
        document.getElementById("outlets-row").innerHTML = `<p class="text-xs text-rose-600 py-2">No canteen outlets available right now.</p>`;
        return;
    }

    canteenOrder.outlets = res.data;
    const row = document.getElementById("outlets-row");
    row.innerHTML = res.data.map(outlet => `
        <button onclick="selectOutlet('${outlet.id}')" id="outlet-btn-${outlet.id}"
            class="flex-shrink-0 flex flex-col items-center gap-2 p-3 rounded-2xl border-2 border-[#E8E7DF] hover:border-[#004D2B] transition bg-white min-w-[80px] cursor-pointer">
            <div class="w-12 h-12 rounded-xl overflow-hidden border border-[#E8E7DF] bg-[#F4F3EB]">
                <img src="${outlet.image || ''}" class="w-full h-full object-cover" onerror="this.style.display='none'">
            </div>
            <span class="text-[11px] font-bold text-center text-[#111713] leading-tight">${outlet.name}</span>
        </button>`).join("");
}

async function selectOutlet(outletId) {
    // If cart has items from a DIFFERENT outlet, warn
    if (canteenOrder.cartOutletId && canteenOrder.cartOutletId !== outletId && canteenOrder.cart.length > 0) {
        const outlet = canteenOrder.outlets.find(o => o.id === canteenOrder.cartOutletId);
        const outletName = outlet ? outlet.name : "another outlet";
        if (!confirm(`Your cart has items from ${outletName}. Switching will clear your cart. Continue?`)) return;
        await clearCanteenCart();
    }

    canteenOrder.selectedOutlet = canteenOrder.outlets.find(o => o.id === outletId);

    // Highlight selected outlet button
    canteenOrder.outlets.forEach(o => {
        const btn = document.getElementById(`outlet-btn-${o.id}`);
        if (!btn) return;
        if (o.id === outletId) {
            btn.className = "flex-shrink-0 flex flex-col items-center gap-2 p-3 rounded-2xl border-2 border-[#004D2B] bg-[#E6F0EB] transition min-w-[80px] cursor-pointer";
        } else {
            btn.className = "flex-shrink-0 flex flex-col items-center gap-2 p-3 rounded-2xl border-2 border-[#E8E7DF] hover:border-[#004D2B] transition bg-white min-w-[80px] cursor-pointer";
        }
    });

    // Load menu for this outlet
    await loadMenu(outletId);
}

// -------------------------------------------------------
// Load Menu
// -------------------------------------------------------
async function loadMenu(outletId) {
    const section = document.getElementById("menu-section");
    section.innerHTML = `<p class="text-sm text-[#526056] text-center py-8">Loading menu...</p>`;

    const res = await window.apiFetch(`/api/canteen/menu/${outletId}`);
    if (!res.success || !res.data.length) {
        section.innerHTML = `<p class="text-sm text-[#526056] text-center py-8">No items available at this outlet.</p>`;
        return;
    }

    canteenOrder.menu = res.data;
    section.innerHTML = `
        <h2 class="text-sm font-extrabold text-[#111713] mb-4">${canteenOrder.selectedOutlet.name} Menu</h2>
        <div class="space-y-3">
            ${res.data.map(p => {
                const foodDot = p.food_type === "veg"
                    ? `<span class="w-2.5 h-2.5 rounded-sm border-2 border-[#16a34a] inline-block flex-shrink-0 mr-1"><span class="block w-1.5 h-1.5 rounded-full bg-[#16a34a] m-px"></span></span>`
                    : p.food_type === "non-veg"
                    ? `<span class="w-2.5 h-2.5 rounded-sm border-2 border-[#dc2626] inline-block flex-shrink-0 mr-1"><span class="block w-1.5 h-1.5 rounded-full bg-[#dc2626] m-px"></span></span>`
                    : "";
                const outOfStock = p.stock <= 0;
                return `
                    <div class="flex items-center gap-3 p-3 rounded-2xl border border-[#E8E7DF] bg-white hover:border-[#004D2B] transition ${outOfStock ? 'opacity-50' : ''}">
                        <div class="w-14 h-14 rounded-xl overflow-hidden border border-[#E8E7DF] flex-shrink-0 bg-[#F4F3EB]">
                            <img src="${p.image && p.image[0] ? p.image[0] : ''}" class="w-full h-full object-cover" onerror="this.style.display='none'">
                        </div>
                        <div class="flex-grow min-w-0">
                            <div class="font-extrabold text-sm text-[#111713] flex items-center">${foodDot}${p.name}</div>
                            <div class="text-xs text-[#526056]">${p.prep_time || '8 mins'} · ${p.unit || ''}</div>
                            <div class="text-sm font-extrabold text-[#004D2B] mt-0.5">₹${p.price}</div>
                        </div>
                        ${outOfStock
                            ? `<span class="text-[11px] font-bold text-rose-500 flex-shrink-0">Sold Out</span>`
                            : `<button onclick="addToCart('${p._id}')" class="px-3 py-1.5 rounded-xl bg-[#004D2B] text-white text-xs font-bold hover:bg-[#003B21] transition flex-shrink-0">+ Add</button>`}
                    </div>`;
            }).join("")}
        </div>`;
}

// -------------------------------------------------------
// Cart Management
// -------------------------------------------------------
async function syncCartFromServer() {
    const res = await window.apiFetch("/api/canteen/cart");
    if (res.success && Array.isArray(res.data)) {
        canteenOrder.cart = res.data;
        canteenOrder.cartOutletId = res.outlet_category_id || null;
        renderCart();
    }
}

async function addToCart(productId) {
    if (!canteenOrder.selectedOutlet) {
        window.toast && window.toast.error("Please select an outlet first.");
        return;
    }

    const token = localStorage.getItem("campus_access_token");
    if (!token) {
        window.toast && window.toast.info("Please log in to place an order.");
        window.location.href = "/student/login.html";
        return;
    }

    const res = await window.apiFetch("/api/canteen/cart/add", {
        method: "POST",
        body: {
            product_id: productId,
            outlet_category_id: canteenOrder.selectedOutlet.id,
            quantity: 1
        }
    });

    if (res.conflict) {
        if (confirm(res.message + "\n\nClear cart and switch outlet?")) {
            await clearCanteenCart();
            await addToCart(productId);
        }
        return;
    }

    if (res.success) {
        await syncCartFromServer();
        window.toast && window.toast.success("Added to order!");
    } else {
        window.toast && window.toast.error(res.message || "Failed to add");
    }
}

async function updateCartQty(itemId, qty) {
    const res = await window.apiFetch("/api/canteen/cart/update", {
        method: "PUT",
        body: { id: itemId, qty }
    });
    if (res.success) await syncCartFromServer();
}

async function removeCartItem(itemId) {
    const res = await window.apiFetch("/api/canteen/cart/item", {
        method: "DELETE",
        body: { id: itemId }
    });
    if (res.success) await syncCartFromServer();
}

async function clearCanteenCart() {
    const res = await window.apiFetch("/api/canteen/cart/clear", { method: "DELETE" });
    if (res.success) {
        canteenOrder.cart = [];
        canteenOrder.cartOutletId = null;
        renderCart();
    }
}

function renderCart() {
    const listEl = document.getElementById("cart-items-list");
    const totalEl = document.getElementById("cart-total");
    const checkoutBtn = document.getElementById("checkout-btn");
    const cart = canteenOrder.cart;

    if (!cart.length) {
        listEl.innerHTML = `<p class="text-xs text-[#8A988E] py-4 text-center">Your order is empty</p>`;
        if (totalEl) totalEl.innerText = "₹0";
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }

    let total = 0;
    listEl.innerHTML = cart.map(item => {
        const prod = item.productId;
        const price = prod ? prod.price || 0 : 0;
        const name = prod ? prod.name : "Item";
        const subtotal = price * item.quantity;
        total += subtotal;
        return `
            <div class="flex items-center gap-2 text-xs py-1.5 border-b border-[#F4F3EB] last:border-0">
                <span class="flex-grow font-semibold text-[#111713] truncate">${name}</span>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                    <button onclick="updateCartQty('${item._id}', ${item.quantity - 1})" class="w-5 h-5 rounded-full border border-[#D3D2C8] font-bold text-[#526056] hover:bg-[#FAF9F3] flex items-center justify-center">−</button>
                    <span class="font-bold w-4 text-center">${item.quantity}</span>
                    <button onclick="updateCartQty('${item._id}', ${item.quantity + 1})" class="w-5 h-5 rounded-full border border-[#D3D2C8] font-bold text-[#526056] hover:bg-[#FAF9F3] flex items-center justify-center">+</button>
                </div>
                <span class="font-bold text-[#004D2B] flex-shrink-0">₹${subtotal.toFixed(0)}</span>
                <button onclick="removeCartItem('${item._id}')" class="text-rose-400 hover:text-rose-600 flex-shrink-0">✕</button>
            </div>`;
    }).join("");

    if (totalEl) totalEl.innerText = `₹${total.toFixed(0)}`;
    if (checkoutBtn) checkoutBtn.disabled = false;
}

// -------------------------------------------------------
// Checkout → Token
// -------------------------------------------------------
async function proceedToCheckout() {
    const btn = document.getElementById("checkout-btn");
    btn.disabled = true;
    btn.innerText = "Placing order...";

    const outletId = canteenOrder.cartOutletId || canteenOrder.selectedOutlet?.id;
    if (!outletId) {
        window.toast && window.toast.error("No outlet selected.");
        btn.disabled = false;
        btn.innerText = "Place Order & Get Token";
        return;
    }

    if (!canteenOrder.cart || canteenOrder.cart.length === 0) {
        window.toast && window.toast.error("Cart is empty.");
        btn.disabled = false;
        btn.innerText = "Place Order & Get Token";
        return;
    }

    let finalTotal = 0;
    canteenOrder.cart.forEach(item => {
        const prod = item.productId;
        if (prod) {
            finalTotal += (prod.price || 0) * item.quantity;
        }
    });

    try {
        // 1. Fetch Config
        const configRes = await window.apiFetch("/api/payment/config");
        if (!configRes.success) throw new Error("Payment gateway unavailable");
        const keyId = configRes.data.key_id;

        // 2. Create Razorpay Order
        const rzpOrderRes = await window.apiFetch("/api/payment/create-order", {
            method: "POST",
            body: { amount: finalTotal, is_delivery: false }
        });
        if (!rzpOrderRes.success) throw new Error(rzpOrderRes.message || rzpOrderRes.detail || "Failed to create payment order");
        const rzpOrder = rzpOrderRes.data;

        // 3. Open Razorpay Modal
        const options = {
            key: keyId,
            amount: rzpOrder.amount,
            currency: rzpOrder.currency,
            name: "Campus Canteen",
            description: "Canteen Order Payment",
            order_id: rzpOrder.razorpay_order_id,
            handler: async function (response) {
                // 4. Verify & Complete Order
                btn.innerText = "Verifying...";
                const res = await window.apiFetch("/api/canteen/checkout", {
                    method: "POST",
                    body: {
                        outlet_category_id: outletId,
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_signature: response.razorpay_signature
                    }
                });

                btn.innerText = "Place Order & Get Token";
                btn.disabled = false;

                if (res.success && res.data) {
                    const tokenData = res.data;
                    const outlet = canteenOrder.outlets.find(o => o.id === outletId);

                    // Show token modal
                    document.getElementById("token-number-display").innerText = `#${tokenData.token_number}`;
                    document.getElementById("token-outlet-name").innerText = `at ${outlet ? outlet.name : 'Outlet'}`;
                    document.getElementById("token-modal").classList.remove("hidden");

                    // Clear cart UI
                    canteenOrder.cart = [];
                    canteenOrder.cartOutletId = null;
                    renderCart();
                } else {
                    if (res.message && res.message.includes("Not enough stock")) {
                        const oosDisplay = document.getElementById("oos-message-display");
                        if (oosDisplay) oosDisplay.innerText = res.message;
                        const oosModal = document.getElementById("out-of-stock-modal");
                        if (oosModal) oosModal.classList.remove("hidden");
                    } else {
                        window.toast && window.toast.error(res.message || "Failed to place order.");
                    }
                }
            },
            modal: {
                ondismiss: function() {
                    btn.disabled = false;
                    btn.innerText = "Place Order & Get Token";
                    window.toast && window.toast.info("Payment cancelled.");
                }
            }
        };

        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (response){
            btn.disabled = false;
            btn.innerText = "Place Order & Get Token";
            window.toast && window.toast.error("Payment failed. Please try again.");
        });
        rzp.open();
    } catch (err) {
        btn.disabled = false;
        btn.innerText = "Place Order & Get Token";
        window.toast && window.toast.error(err.message || "Payment initiation failed");
    }
}

function closeOosModal() {
    const oosModal = document.getElementById("out-of-stock-modal");
    if (oosModal) oosModal.classList.add("hidden");
}

function closeTokenModal() {
    document.getElementById("token-modal").classList.add("hidden");
}

// Globals
window.selectOutlet = selectOutlet;
window.addToCart = addToCart;
window.updateCartQty = updateCartQty;
window.removeCartItem = removeCartItem;
window.clearCanteenCart = clearCanteenCart;
window.proceedToCheckout = proceedToCheckout;
window.closeTokenModal = closeTokenModal;
