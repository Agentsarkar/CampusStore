// =======================================================
// CampusStore — Canteen Operator Panel (Production)
// Wired to /api/canteen/* endpoints
// =======================================================

const panelState = {
    activeTab: "tokens",
    tokenFilter: "ALL",
    notifyOffset: 0,   // 0 = serving 1-10, 10 = serving 11-20, etc.
    outlet: null,
    tokens: [],
    products: []
};

// -------------------------------------------------------
// Init
// -------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
    // Auth guard: must be ADMIN or CANTEEN_OP
    if (!window.campusAuth) {
        window.location.href = "/student/login.html";
        return;
    }
    const token = window.campusAuth.getToken ? window.campusAuth.getToken() : localStorage.getItem("campus_access_token");
    if (!token) {
        window.location.href = "/student/login.html";
        return;
    }

    // Load operator outlet info
    const outletRes = await window.apiFetch("/api/canteen/my-outlet");
    if (!outletRes.success) {
        window.toast && window.toast.error("Access denied. You are not a canteen operator.");
        setTimeout(() => window.location.href = "/student/index.html", 2000);
        return;
    }

    const { name, email, role, outlet } = outletRes.data;
    panelState.outlet = outlet;

    // Set header info
    const opName = document.getElementById("operator-name");
    const opRole = document.getElementById("operator-role");
    const outletName = document.getElementById("header-outlet-name");

    if (opName) opName.innerText = name || email || "Operator";
    if (opRole) opRole.innerText = role === "ADMIN" ? "Super Admin" : "Canteen Operator";

    if (!outlet && role !== "ADMIN") {
        if (outletName) outletName.innerText = "No Outlet Assigned";
        window.toast && window.toast.warning("No outlet assigned to your account. Contact admin.");
        return;
    }

    if (role === "ADMIN") {
        const outRes = await window.apiFetch("/api/canteen/outlets");
        if (outRes.success && outRes.data.length > 0) {
            if (outletName) {
                outletName.innerHTML = `
                    <select id="admin-outlet-select" class="bg-transparent font-bold text-[#004D2B] focus:outline-none cursor-pointer">
                        <option value="">Select Outlet...</option>
                        ${outRes.data.map(o => {
                            const isSelected = outlet && o._id === outlet._id ? "selected" : "";
                            return `<option value="${o._id}" ${isSelected}>${o.name}</option>`;
                        }).join("")}
                    </select>
                `;
                document.getElementById("admin-outlet-select").addEventListener("change", (e) => {
                    const selectedId = e.target.value;
                    if (!selectedId) {
                        panelState.outlet = null;
                        document.getElementById("tokens-tbody").innerHTML = `<tr><td colspan="5" class="text-center py-10 text-xs text-[#526056]">Please select an outlet from the top bar.</td></tr>`;
                        return;
                    }
                    panelState.outlet = outRes.data.find(o => o._id === selectedId);
                    refreshAllData();
                });
            }
            
            // If they didn't have a default outlet, stop and wait for them to select one
            if (!outlet) {
                document.getElementById("tokens-tbody").innerHTML = `<tr><td colspan="5" class="text-center py-10 text-xs text-[#526056]">Please select an outlet from the top bar.</td></tr>`;
                return;
            }
        } else {
            if (outletName) outletName.innerText = "No Canteen Outlets";
            window.toast && window.toast.warning("No canteen outlets found in the system.");
            return;
        }
    } else {
        if (outletName) outletName.innerText = outlet.name;
    }

    // Load initial data for assigned operator
    switchTab("tokens");
    await refreshAllData();

    // Load persisted notify offset from server so page refresh doesn't reset it
    if (panelState.outlet) {
        try {
            const statusRes = await window.apiFetch(`/api/canteen/notify-status/${panelState.outlet.id}`);
            if (statusRes.success && statusRes.data) {
                panelState.notifyOffset = statusRes.data.notify_offset || 0;
                panelState.notifyRev = statusRes.data.notify_rev || 0;
                renderTokens();
            }
        } catch (e) { /* ignore */ }
    }
});

// -------------------------------------------------------
// Tab Navigation
// -------------------------------------------------------
function switchTab(tab) {
    panelState.activeTab = tab;
    const tabs = ["tokens", "menu", "analytics"];
    tabs.forEach(t => {
        const el = document.getElementById(`tab-${t}`);
        const btn = document.getElementById(`nav-btn-${t}`);
        if (el) el.classList.add("hidden");
        if (btn) {
            btn.classList.remove("bg-[#004D2B]", "text-white");
            btn.classList.add("text-[#526056]", "hover:bg-[#FAF9F3]");
        }
    });
    const activeEl = document.getElementById(`tab-${tab}`);
    const activeBtn = document.getElementById(`nav-btn-${tab}`);
    if (activeEl) activeEl.classList.remove("hidden");
    if (activeBtn) {
        activeBtn.classList.add("bg-[#004D2B]", "text-white");
        activeBtn.classList.remove("text-[#526056]", "hover:bg-[#FAF9F3]");
    }
}

async function refreshAllData() {
    if (!panelState.outlet) return;
    await Promise.all([loadTokens(), loadMenu(), loadAnalytics()]);
}

// -------------------------------------------------------
// Tokens
// -------------------------------------------------------
async function loadTokens() {
    if (!panelState.outlet) return;
    const res = await window.apiFetch(`/api/canteen/tokens/${panelState.outlet.id}`);
    if (res.success) {
        panelState.tokens = res.data;
        const activeCount = panelState.tokens.filter(t => t.status === "ACTIVE").length;
        const badge = document.getElementById("sidebar-active-count");
        if (badge) badge.innerText = `${activeCount} Active`;
        renderTokens();
    }
}

function setFilter(filter) {
    panelState.tokenFilter = filter;
    ["ALL", "ACTIVE", "DONE", "CANCELLED"].forEach(f => {
        const btn = document.getElementById(`filter-${f}`);
        if (!btn) return;
        if (f === filter) {
            btn.className = "px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#004D2B] text-white transition";
        } else {
            btn.className = "px-3.5 py-1.5 rounded-xl text-xs font-bold text-[#526056] hover:bg-[#FAF9F3] transition";
        }
    });
    renderTokens();
}

function renderTokens() {
    const filter = panelState.tokenFilter;
    let tokens = panelState.tokens;
    if (filter === "ACTIVE") tokens = tokens.filter(t => t.status === "ACTIVE");
    else if (filter === "DONE") tokens = tokens.filter(t => t.status === "DONE");
    else if (filter === "CANCELLED") tokens = tokens.filter(t => t.status === "CANCELLED");

    // Update the notify range label
    const start = panelState.notifyOffset + 1;
    const end = panelState.notifyOffset + 10;
    const rangeLabel = document.getElementById("notify-range-label");
    if (rangeLabel) rangeLabel.innerText = `Tokens ${start}\u2013${end}`;

    const btnAgain = document.getElementById("btn-text-again");
    if (btnAgain) btnAgain.innerText = `Notify (${start}-${end})`;

    const btnNext = document.getElementById("btn-text-next");
    if (btnNext) btnNext.innerText = `Next (${start+10}-${end+10}) \u2192`;

    const btnPrev = document.getElementById("btn-notify-prev");
    const btnTextPrev = document.getElementById("btn-text-prev");
    if (btnPrev && btnTextPrev) {
        if (panelState.notifyOffset >= 10) {
            btnPrev.classList.remove("hidden");
            btnTextPrev.innerText = `\u2190 Prev (${start-10}-${end-10})`;
        } else {
            btnPrev.classList.add("hidden");
        }
    }

    const grid = document.getElementById("tokens-grid");
    if (!grid) return;

    if (tokens.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full campus-card p-10 text-center text-[#526056] space-y-2">
                <div class="w-12 h-12 rounded-full bg-[#F4F3EB] flex items-center justify-center mx-auto text-lg font-bold">#</div>
                <p class="font-extrabold text-sm text-[#111713]">No ${filter === "ALL" ? "" : filter.toLowerCase() + " "}tokens</p>
                <p class="text-xs text-[#8A988E]">Tokens appear here when students place canteen orders.</p>
            </div>`;
        return;
    }

    grid.innerHTML = tokens.map(t => renderTokenCard(t)).join("");
}

function renderTokenCard(t) {
    const isDone = t.status === "DONE";
    const isCancelled = t.status === "CANCELLED";
    
    const cardBorder = isDone ? "border-l-emerald-500" : isCancelled ? "border-l-rose-400 opacity-75" : "border-l-amber-400";
    const statusBadge = isDone
        ? `<span class="text-[9px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-[#E6F0EB] text-[#004D2B] border border-[#A3D1B9]">DONE ✓</span>`
        : isCancelled
        ? `<span class="text-[9px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 border border-rose-200">CANCELLED</span>`
        : `<span class="text-[9px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">ACTIVE</span>`;

    const items = (t.product_details || []).map(p =>
        `<div class="flex justify-between text-[11px]">
            <span class="font-medium text-[#526056] truncate">${p.name} × ${p.quantity}</span>
            <span class="font-bold text-[#111713] ml-2">₹${p.subtotal || (p.price * p.quantity).toFixed(0)}</span>
        </div>`
    ).join("");

    const studentName = t.student ? `<div class="text-[10px] text-[#8A988E] mt-1">Student: ${t.student.name || t.student.email}</div>` : "";

    const markDoneBtn = !isDone && !isCancelled
        ? `<button onclick="markDone('${t._id}', ${t.token_number})" class="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center justify-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                Mark Done
            </button>`
        : `<div class="flex-1 py-2 rounded-xl bg-[#F4F3EB] text-[#8A988E] text-xs font-bold flex items-center justify-center gap-1.5 cursor-not-allowed">
                ${isDone ? "✓ Served" : "Cancelled"}
            </div>`;

    return `
        <div class="campus-card p-4 flex flex-col gap-3 border-l-4 ${cardBorder} ${isDone ? 'opacity-80' : ''}">
            <div class="flex justify-between items-start">
                <div>
                    <span class="text-[10px] font-extrabold text-[#526056] uppercase tracking-wider block">Token</span>
                    <h3 class="text-2xl font-extrabold text-[#111713] tracking-tight">#${t.token_number}</h3>
                    ${studentName}
                </div>
                ${statusBadge}
            </div>
            <div class="space-y-1 border-t border-b border-[#E8E7DF] py-2.5">${items}</div>
            <div class="flex justify-between items-center text-xs">
                <span class="text-[#526056]">Total</span>
                <span class="font-extrabold text-[#111713]">₹${t.total_amt}</span>
            </div>
            <div class="flex gap-2">${markDoneBtn}</div>
        </div>`;
}

async function markDone(tokenId, tokenNumber) {
    const res = await window.apiFetch("/api/canteen/token/mark-done", {
        method: "PUT",
        body: { token_id: tokenId }
    });
    if (res.success) {
        window.toast && window.toast.success(`Token #${tokenNumber} marked as done!`);
        await loadTokens();
        renderTokens();
    } else {
        window.toast && window.toast.error(res.message || "Failed to mark done");
    }
}

async function triggerNotifyNext() {
    if (!panelState.outlet) return;
    const res = await window.apiFetch("/api/canteen/notify-next", {
        method: "POST",
        body: {
            outlet_category_id: panelState.outlet.id,
            current_offset: panelState.notifyOffset
        }
    });
    if (res.success) {
        panelState.notifyOffset = res.new_offset;
        panelState.notifyRev = res.notify_rev || (panelState.notifyRev || 0) + 1;
        window.toast && window.toast.success(res.message);
        renderTokens();
    } else {
        window.toast && window.toast.error(res.message || "Failed");
    }
}

async function triggerNotifyAgain() {
    if (!panelState.outlet) return;
    // Call /notify-again with the CURRENT offset (already applied, same batch re-notified)
    const res = await window.apiFetch("/api/canteen/notify-again", {
        method: "POST",
        body: {
            outlet_category_id: panelState.outlet.id,
            current_offset: panelState.notifyOffset  // e.g. 10 means we ARE on batch 11-20
        }
    });
    if (res.success) {
        panelState.notifyRev = res.notify_rev || (panelState.notifyRev || 0) + 1;
        window.toast && window.toast.success("Re-notified: " + res.message);
    } else {
        window.toast && window.toast.error(res.message || "Failed to re-notify");
    }
}

async function triggerNotifyPrev() {
    if (!panelState.outlet) return;
    const res = await window.apiFetch("/api/canteen/notify-prev", {
        method: "POST",
        body: {
            outlet_category_id: panelState.outlet.id,
            current_offset: panelState.notifyOffset
        }
    });
    if (res.success) {
        panelState.notifyOffset = res.new_offset;
        panelState.notifyRev = res.notify_rev || (panelState.notifyRev || 0) + 1;
        window.toast && window.toast.success(res.message);
        renderTokens();
    } else {
        window.toast && window.toast.error(res.message || "Failed");
    }
}

// -------------------------------------------------------
// Menu & Stock
// -------------------------------------------------------
async function loadMenu() {
    if (!panelState.outlet) return;
    const res = await window.apiFetch(`/api/canteen/menu/${panelState.outlet.id}`);
    if (res.success) {
        panelState.products = res.data;
        renderMenu();
    }
}

function renderMenu() {
    const tbody = document.getElementById("menu-tbody");
    if (!tbody) return;
    const products = panelState.products;

    if (products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-[#526056]">No menu items. Add your first item!</td></tr>`;
        return;
    }

    tbody.innerHTML = products.map(p => {
        const foodBadge = p.food_type === "veg"
            ? `<span class="inline-flex items-center gap-1 text-[10px] font-extrabold text-[#16a34a] bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded"><span class="w-2 h-2 rounded-full bg-[#16a34a]"></span>Veg</span>`
            : p.food_type === "non-veg"
            ? `<span class="inline-flex items-center gap-1 text-[10px] font-extrabold text-[#dc2626] bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded"><span class="w-2 h-2 rounded-full bg-[#dc2626]"></span>Non-Veg</span>`
            : "";
        const isLow = p.stock <= 5;
        return `
            <tr class="hover:bg-[#FAF9F3] transition">
                <td class="py-3 px-4">
                    <div class="flex items-center gap-2.5">
                        <div class="w-10 h-10 rounded-xl overflow-hidden border border-[#E8E7DF] flex-shrink-0 bg-[#F4F3EB]">
                            <img src="${p.image && p.image[0] ? p.image[0] : ''}" class="w-full h-full object-cover" onerror="this.style.display='none'">
                        </div>
                        <div>
                            <div class="font-extrabold text-xs text-[#111713]">${p.name}</div>
                            <span class="text-[10px] text-[#526056]">${p.unit || ''} · ${p.prep_time || '8 mins'}</span>
                        </div>
                    </div>
                </td>
                <td class="py-3 px-4 font-extrabold text-xs">₹${p.price}</td>
                <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                        <input type="number" min="0" value="${p.stock}" onchange="quickStock('${p._id}', this.value)" class="w-16 px-2 py-1 border border-[#D3D2C8] rounded-xl text-xs font-bold text-center focus:outline-none focus:border-[#004D2B]">
                        ${isLow ? `<span class="text-[9px] font-extrabold text-rose-600 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded">Low</span>` : ""}
                    </div>
                </td>
                <td class="py-3 px-4">${foodBadge}</td>
                <td class="py-3 px-4 text-right space-x-2">
                    <button onclick="openEditModal('${p._id}')" class="px-2.5 py-1 rounded-xl text-xs font-bold border border-[#D3D2C8] text-[#111713] hover:bg-[#FAF9F3] transition">Edit</button>
                    <button onclick="deleteItem('${p._id}')" class="px-2.5 py-1 rounded-xl text-xs font-bold border border-rose-200 text-rose-600 hover:bg-rose-50 transition">Delete</button>
                </td>
            </tr>`;
    }).join("");
}

async function quickStock(productId, newVal) {
    const val = parseInt(newVal);
    if (isNaN(val)) return;
    const res = await window.apiFetch("/api/product/update-product-details", {
        method: "PUT",
        body: { id: productId, stock: val }
    });
    if (res.success) {
        window.toast && window.toast.success(`Stock updated to ${val}`);
        await loadMenu();
    }
}

async function deleteItem(productId) {
    if (!confirm("Delete this menu item?")) return;
    const res = await window.apiFetch("/api/product/delete-product", {
        method: "DELETE",
        body: { id: productId }
    });
    if (res.success) {
        window.toast && window.toast.success("Item deleted");
        await loadMenu();
    }
}

// -------------------------------------------------------
// Analytics & Withdrawals
// -------------------------------------------------------
async function loadAnalytics() {
    if (!panelState.outlet) return;
    const res = await window.apiFetch(`/api/canteen/analytics/${panelState.outlet.id}`);
    if (res.success && res.data) {
        const d = res.data;
        panelState.currentRevenue = d.total_revenue || 0; // Store for withdrawals
        
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
        set("a-revenue", `₹${d.total_revenue}`);
        set("a-total", d.total_tokens);
        set("a-active", d.active_tokens);
        set("a-avg", `₹${d.avg_order_value}`);
        
        // Init withdrawal UI
        toggleWithdrawFields();
    }
}

async function executeTokenReset() {
    if (!panelState.outlet) return;
    const btn = document.getElementById("reset-confirm-btn");
    btn.disabled = true;
    btn.innerText = "Resetting...";
    
    const res = await window.apiFetch("/api/canteen/reset-tokens", {
        method: "POST",
        body: { outlet_category_id: panelState.outlet.id }
    });
    
    if (res.success) {
        window.toast && window.toast.success("Tokens and revenue reset for today!");
        document.getElementById("reset-modal").classList.add("hidden");
        await fetchTokens();
        await loadAnalytics();
    } else {
        window.toast && window.toast.error(res.message || "Failed to reset");
    }
    
    btn.disabled = false;
    btn.innerText = "Yes, Reset Data";
}

function toggleWithdrawFields() {
    const type = document.getElementById("withdraw-type").value;
    const container = document.getElementById("withdraw-dynamic-fields");
    
    if (type === "UPI") {
        container.innerHTML = `
            <div class="space-y-1">
                <label class="font-bold text-[#111713] block">UPI ID <span class="text-rose-600">*</span></label>
                <input type="text" id="w-upi-id" required placeholder="e.g. john@okhdfcbank" class="w-full px-3 py-2 border border-[#D3D2C8] rounded-xl font-semibold focus:outline-none focus:border-[#004D2B] bg-[#FAF9F3]">
            </div>
        `;
    } else if (type === "NEFT") {
        container.innerHTML = `
            <div class="space-y-1">
                <label class="font-bold text-[#111713] block">Account Number <span class="text-rose-600">*</span></label>
                <input type="text" id="w-acc-no" required placeholder="Account Number" class="w-full px-3 py-2 border border-[#D3D2C8] rounded-xl font-semibold focus:outline-none focus:border-[#004D2B] bg-[#FAF9F3]">
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                    <label class="font-bold text-[#111713] block">IFSC Code <span class="text-rose-600">*</span></label>
                    <input type="text" id="w-ifsc" required placeholder="e.g. SBIN0001234" class="w-full px-3 py-2 border border-[#D3D2C8] rounded-xl font-semibold focus:outline-none focus:border-[#004D2B] bg-[#FAF9F3]">
                </div>
                <div class="space-y-1">
                    <label class="font-bold text-[#111713] block">Account Holder <span class="text-rose-600">*</span></label>
                    <input type="text" id="w-acc-name" required placeholder="Full Name" class="w-full px-3 py-2 border border-[#D3D2C8] rounded-xl font-semibold focus:outline-none focus:border-[#004D2B] bg-[#FAF9F3]">
                </div>
            </div>
        `;
    } else if (type === "WALLET") {
        container.innerHTML = `
            <div class="space-y-1">
                <label class="font-bold text-[#111713] block">Wallet Mobile Number <span class="text-rose-600">*</span></label>
                <input type="tel" id="w-wallet-no" required pattern="[0-9]{10}" placeholder="10-digit mobile number" class="w-full px-3 py-2 border border-[#D3D2C8] rounded-xl font-semibold focus:outline-none focus:border-[#004D2B] bg-[#FAF9F3]">
            </div>
        `;
    }
}

function handleWithdrawSubmit(e) {
    e.preventDefault();
    const amountInput = document.getElementById("withdraw-amount");
    const amount = parseFloat(amountInput.value);
    
    if (!amount || amount <= 0) {
        window.toast && window.toast.error("Please enter a valid amount");
        return;
    }
    
    if (amount > (panelState.currentRevenue || 0)) {
        window.toast && window.toast.error(`Amount exceeds available revenue (₹${panelState.currentRevenue || 0})`);
        return;
    }
    
    // Dummy success behavior
    const btn = e.target.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.innerText = "Processing...";
    
    setTimeout(() => {
        window.toast && window.toast.success(`Withdrawal request for ₹${amount} has been initiated successfully!`);
        e.target.reset();
        toggleWithdrawFields();
        btn.disabled = false;
        btn.innerText = "Request Withdrawal";
    }, 800);
}

// -------------------------------------------------------
// Product Modal (Add/Edit)
// -------------------------------------------------------
function openAddModal() {
    document.getElementById("modal-title").innerText = "Add Menu Item";
    document.getElementById("item-form").reset();
    document.getElementById("edit-product-id").value = "";
    document.getElementById("item-modal").classList.remove("hidden");
}

function openEditModal(productId) {
    const prod = panelState.products.find(p => p._id === productId);
    if (!prod) return;
    document.getElementById("modal-title").innerText = "Edit Menu Item";
    document.getElementById("edit-product-id").value = productId;
    document.getElementById("item-name").value = prod.name || "";
    document.getElementById("item-price").value = prod.price || 0;
    document.getElementById("item-stock").value = prod.stock || 0;
    document.getElementById("item-food-type").value = prod.food_type || "veg";
    document.getElementById("item-prep-time").value = prod.prep_time || "8 mins";
    document.getElementById("item-image").value = (prod.image && prod.image[0]) ? prod.image[0] : "";
    document.getElementById("item-desc").value = prod.description || "";
    document.getElementById("item-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("item-modal").classList.add("hidden");
}

async function handleItemSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById("edit-product-id").value;
    const payload = {
        name: document.getElementById("item-name").value.trim(),
        price: parseFloat(document.getElementById("item-price").value),
        stock: parseInt(document.getElementById("item-stock").value),
        food_type: document.getElementById("item-food-type").value,
        prep_time: document.getElementById("item-prep-time").value.trim(),
        image: [document.getElementById("item-image").value.trim()].filter(Boolean),
        description: document.getElementById("item-desc").value.trim(),
        section: "canteen",
        category: panelState.outlet ? [panelState.outlet.id] : [],
        unit: "1 plate"
    };

    let res;
    if (editId) {
        payload.id = editId;
        res = await window.apiFetch("/api/product/update-product-details", { method: "PUT", body: payload });
    } else {
        res = await window.apiFetch("/api/product/create", { method: "POST", body: payload });
    }

    if (res.success) {
        window.toast && window.toast.success(editId ? "Item updated!" : "Item added!");
        closeModal();
        await loadMenu();
        renderMenu();
    } else {
        window.toast && window.toast.error(res.message || "Failed to save item");
    }
}

// -------------------------------------------------------
// Global Exports
// -------------------------------------------------------
window.switchTab = switchTab;
window.setFilter = setFilter;
window.markDone = markDone;
window.triggerNotifyNext = triggerNotifyNext;
window.triggerNotifyAgain = triggerNotifyAgain;
window.openAddModal = openAddModal;
window.openEditModal = openEditModal;
window.closeModal = closeModal;
window.handleItemSubmit = handleItemSubmit;
window.quickStock = quickStock;
window.deleteItem = deleteItem;
window.refreshAllData = refreshAllData;
