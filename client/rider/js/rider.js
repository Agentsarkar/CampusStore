/**
 * Campus Rider Shared JavaScript Module
 * Strictly isolated inside rider/ module
 */

// Local Storage Key for Rider App State
const RIDER_STORAGE_KEY = 'campus_rider_state_v2';

// Default Initial State
const defaultState = {
  user: null,
  isOnline: false,
  disclaimerAccepted: false,
  activeOrder: null
};

// Robust State Recovery with Corrupted LocalStorage Handling
let state = (function loadState() {
  try {
    const saved = localStorage.getItem(RIDER_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && typeof parsed === 'object' && parsed.user) {
        return { ...defaultState, ...parsed };
      }
    }
  } catch (e) {
    console.warn('[Rider Module] Corrupted or invalid localStorage state detected. Resetting to clean default state:', e);
    localStorage.removeItem(RIDER_STORAGE_KEY);
  }
  return JSON.parse(JSON.stringify(defaultState));
})();

function saveState() {
  try {
    localStorage.setItem(RIDER_STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.error('[Rider Module] Error saving state to localStorage:', e);
  }
}

/**
 * Store Config Loader
 * Loads store details ONLY from rider/config/stores.json
 */
let storesCache = null;
async function getStoresConfig() {
  if (storesCache && Array.isArray(storesCache) && storesCache.length > 0) {
    return storesCache;
  }
  try {
    const res = await fetch('./config/stores.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && Array.isArray(data.stores) && data.stores.length > 0) {
      storesCache = data.stores;
      return storesCache;
    }
  } catch (err) {
    console.warn('[Rider Module] Could not load ./config/stores.json via fetch, using fallback store array:', err);
  }

  // Safe fallback matching stores.json schema
  storesCache = [
    {
      id: "canteen-central",
      name: "Central Campus Canteen",
      location: "Student Activity Center, Ground Floor, Counter 3",
      contact: "Counter Ext 401",
      instructions: "Collect order from Counter 3. Verify item count with canteen supervisor before packaging."
    },
    {
      id: "foodcourt-north",
      name: "North Campus Food Court",
      location: "Block C, Food Court Counter 2",
      contact: "Counter Ext 402",
      instructions: "Collect from Counter 2. Present Order ID on arrival."
    },
    {
      id: "campus-express",
      name: "Campus Express Store",
      location: "Hostel Complex 4, Ground Level",
      contact: "Counter Ext 403",
      instructions: "Collect package from Express pickup shelf near checkout register."
    }
  ];
  return storesCache;
}

/**
 * Real Backend API Abstraction Functions
 */
function getAuthHeaders() {
  const token = localStorage.getItem('campus_rider_access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

window.riderApiFetch = async function (endpoint, options = {}) {
    const API_URL = "";
    const url = endpoint.startsWith("http") ? endpoint : API_URL + endpoint;

    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
        ...getAuthHeaders()
    };

    const config = {
        method: options.method || "GET",
        headers,
        ...options
    };
    if (config.body && typeof config.body !== 'string') {
        config.body = JSON.stringify(config.body);
    }

    const response = await fetch(url, config);
    return response.json();
};

async function riderRegistration(registrationData) {
  // Handled directly via FormData in register.html now.
  return Promise.resolve({ success: false });
}

async function riderLogin(email, password) {
  try {
    const res = await window.riderApiFetch('/api/rider/login', {
      method: 'POST',
      body: { email, password }
    });
    if (res.success) {
      localStorage.setItem('campus_rider_access_token', res.data.accessToken);
      return { success: true, user: res.data.rider };
    }
    return { success: false, message: res.message || 'Login failed' };
  } catch (err) {
    return { success: false, message: 'Network error' };
  }
}

async function getRiderVerificationState() {
  // We can just rely on the state.user.status from login
  return Promise.resolve({
    status: state.user ? state.user.status : 'PENDING'
  });
}

async function updateRiderStatus(isOnline) {
  // We can add a PUT /api/rider/status later if needed, for now just local state
  return Promise.resolve({ success: true, is_online: isOnline });
}

async function getAvailableOrders() {
  try {
    const res = await window.riderApiFetch('/api/rider/orders/available');
    if (res.success) {
      // Map Flash orders to Rider format
      const stores = await getStoresConfig();
      return res.data.map(order => ({
        id: order.id,
        orderIdText: order.order_id,
        storeId: stores[0].id,
        reward: `₹${(order.total_amt * 0.1).toFixed(2)}`, // e.g. 10% reward
        items: order.product_details.map(item => `${item.quantity}x ${item.name}`),
        destination: order.delivery_address,
        customerNotes: 'Call upon arrival',
        customerName: (order.users && order.users.name) ? order.users.name : 'Student',
        customerPhone: (order.users && order.users.mobile) ? order.users.mobile : '+91 9876543210'
      }));
    }
    return [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

async function toggleOnlineApi(isOnline) {
  try {
    const res = await window.riderApiFetch(`/api/rider/toggle-online`, {
      method: 'PUT',
      body: { is_online: isOnline }
    });
    return { success: res.success };
  } catch (err) {
    return { success: false };
  }
}

async function penaltyOrderApi(type) {
  try {
    const res = await window.riderApiFetch(`/api/rider/orders/penalty/${type}`, {
      method: 'PUT'
    });
    return res;
  } catch (err) {
    return { success: false };
  }
}

async function handleRiderLogout() {
    try {
        if (state.isOnline) {
            await toggleOnlineApi(false);
        }
    } catch(e) {
        console.warn("Failed to toggle offline on logout", e);
    }
    localStorage.removeItem(RIDER_STORAGE_KEY);
    localStorage.removeItem('campus_rider_token');
    window.location.href = 'login.html';
}

async function acceptOrderApi(orderId) {
  try {
    const res = await window.riderApiFetch(`/api/rider/orders/${orderId}/accept`, {
      method: 'POST'
    });
    return { success: res.success };
  } catch (err) {
    return { success: false };
  }
}

async function updateOrderStatusApi(orderId, statusString, otp = null) {
  try {
    const bodyPayload = { status: statusString };
    if (otp) {
        bodyPayload.otp = otp;
    }
    const res = await window.riderApiFetch(`/api/rider/orders/${orderId}/status`, {
      method: 'PUT',
      body: bodyPayload
    });
    if (!res.success) {
        throw new Error(res.message || res.detail || "Failed to update status");
    }
    return { success: true };
  } catch (err) {
    throw err;
  }
}

/**
 * Modal Handlers with Body Scroll Lock
 */
function openGoOnlineModal() {
  const backdrop = document.getElementById('go-online-modal-backdrop');
  if (backdrop) {
    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeGoOnlineModal() {
  const backdrop = document.getElementById('go-online-modal-backdrop');
  if (backdrop) {
    backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function openIncomingOrderModal() {
  const backdrop = document.getElementById('incoming-order-modal-backdrop');
  if (backdrop) {
    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeIncomingOrderModal() {
  const backdrop = document.getElementById('incoming-order-modal-backdrop');
  if (backdrop) {
    backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }
}

/**
 * Slide-to-Action Gesture Engine (Mouse & Touch Drag with Boundary Checks)
 */
function initSlideToAction(trackId, thumbId, progressId, onComplete) {
  const track = document.getElementById(trackId);
  const thumb = document.getElementById(thumbId);
  const progress = document.getElementById(progressId);

  if (!track || !thumb) return;

  let isDragging = false;
  let startX = 0;
  let maxDrag = track.clientWidth - thumb.clientWidth - 8;

  function onStart(e) {
    if (isDragging) return;
    isDragging = true;
    thumb.classList.add('dragging');
    if (progress) progress.classList.add('dragging');

    const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : e.clientX;
    startX = clientX - thumb.offsetLeft;
    maxDrag = track.clientWidth - thumb.clientWidth - 8;

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
  }

  function onMove(e) {
    if (!isDragging) return;
    
    if (e.cancelable && e.type === 'touchmove') {
      e.preventDefault();
    }

    const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : e.clientX;
    let newLeft = clientX - startX;
    newLeft = Math.max(4, Math.min(newLeft, maxDrag));

    thumb.style.left = `${newLeft}px`;
    const percentage = ((newLeft - 4) / Math.max(1, maxDrag - 4)) * 100;
    if (progress) progress.style.width = `${percentage}%`;

    if (percentage >= 85) {
      cleanupListeners();
      isDragging = false;
      thumb.style.left = `${maxDrag}px`;
      if (progress) progress.style.width = '100%';
      
      if (typeof onComplete === 'function') {
        onComplete();
      }
    }
  }

  function onEnd() {
    if (!isDragging) return;
    isDragging = false;
    cleanupListeners();

    thumb.classList.remove('dragging');
    if (progress) progress.classList.remove('dragging');
    thumb.style.left = '4px';
    if (progress) progress.style.width = '0%';
  }

  function cleanupListeners() {
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onEnd);
    window.removeEventListener('touchmove', onMove);
    window.removeEventListener('touchend', onEnd);
  }

  // Clear existing handlers before binding
  thumb.onmousedown = null;
  thumb.ontouchstart = null;

  thumb.addEventListener('mousedown', onStart);
  thumb.addEventListener('touchstart', onStart, { passive: true });
}

/**
 * Universal State Render Handler for Dashboard Status & Badges
 */
function renderUI() {
  if (document.getElementById('profile-initial')) renderProfile();
  


  const offlineView = document.getElementById('offline-view');
  const onlineView = document.getElementById('online-view');
  const statusBadge = document.getElementById('header-status-badge');
  const offlineControl = document.getElementById('header-offline-control');

  if (state.isOnline) {
    if (offlineView) offlineView.classList.add('hidden');
    if (onlineView) onlineView.classList.remove('hidden');

    if (statusBadge) {
      statusBadge.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-[#E6F0EB] text-[#004D2B] border border-[#A3D1B9]';
      statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-[#004D2B] pulse-badge"></span> ONLINE`;
    }

    if (offlineControl) offlineControl.classList.remove('hidden');
  } else {
    if (offlineView) offlineView.classList.remove('hidden');
    if (onlineView) onlineView.classList.add('hidden');

    if (statusBadge) {
      statusBadge.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200';
      statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-gray-400"></span> OFFLINE`;
    }

    if (offlineControl) offlineControl.classList.add('hidden');
  }
}

/**
 * Global Demo Helper Functions
 */
function resetDemoState() {
  localStorage.removeItem(RIDER_STORAGE_KEY);
  state = JSON.parse(JSON.stringify(defaultState));
  saveState();
  window.location.href = 'index.html';
}

function setDemoStatusPending() {
  if (!state.user) state.user = {};
  state.user.status = 'PENDING_VERIFICATION';
  state.isOnline = false;
  saveState();
  window.location.href = 'pending.html';
}

function setDemoStatusVerified() {
  if (!state.user) state.user = {};
  state.user.status = 'VERIFIED';
  saveState();
  window.location.href = 'index.html';
}

/**
 * Universal Escape Key Listener
 */
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeGoOnlineModal();
    closeIncomingOrderModal();
  }
});


