// =========================================================
// GLOBAL TOKEN NOTIFICATION SYSTEM
// Injected into all student pages to allow background polling
// =========================================================

(function() {
    // Only run if the user is likely logged in
    if (!localStorage.getItem('campus_access_token')) return;

    // Inject styles for the slider and popup
    const style = document.createElement('style');
    style.innerHTML = `
        .slide-action-track {
            position: relative; width: 100%; height: 56px; background-color: #004D2B;
            border-radius: 9999px; overflow: hidden; user-select: none; touch-action: pan-y;
            box-shadow: 0 4px 14px rgba(0, 77, 43, 0.25);
        }
        .slide-action-progress {
            position: absolute; top: 0; left: 0; height: 100%; width: 56px;
            background-color: #003B21; border-radius: 9999px; transition: width 0.1s linear;
        }
        .slide-action-text {
            position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
            color: #D7F000; font-weight: 800; font-size: 0.875rem; z-index: 10;
            pointer-events: none; text-transform: uppercase; letter-spacing: 0.05em;
        }
        .slide-action-thumb {
            position: absolute; top: 4px; left: 4px; width: 48px; height: 48px;
            background-color: #D7F000; color: #004D2B; border-radius: 9999px;
            display: flex; align-items: center; justify-content: center; z-index: 20;
            cursor: grab; box-shadow: 0 2px 8px rgba(0,0,0,0.15); transition: transform 0.1s linear;
        }
        .slide-action-thumb:active { cursor: grabbing; }
        .pulse-badge {
            animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(215, 240, 0, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(215, 240, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(215, 240, 0, 0); }
        }
    `;
    document.head.appendChild(style);

    // Inject HTML
    const notifHTML = `
    <div id="token-notif-backdrop" class="fixed inset-0 bg-black/75 backdrop-blur-xs z-50 hidden flex items-end justify-center" style="transition: opacity 0.3s;">
        <div id="token-notif-sheet" class="bg-white w-full max-w-md rounded-t-[28px] sm:rounded-[28px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]" style="transform: translateY(100%); transition: transform 0.35s cubic-bezier(0.16,1,0.3,1); padding-bottom: max(1.25rem, env(safe-area-inset-bottom, 1.25rem));">

            <div class="pt-3 pb-1 flex justify-center">
                <div class="w-10 h-1.5 bg-[#D3D2C8] rounded-full"></div>
            </div>

            <!-- Header -->
            <div class="px-5 py-3 bg-[#004D2B] text-[#D7F000] flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-[#D7F000] pulse-badge"></span>
                    <span class="text-xs font-black uppercase tracking-wider">Token Ready!</span>
                </div>
                <button type="button" id="token-notif-dismiss-btn" class="text-xs font-bold px-2.5 py-1 rounded bg-black/20 hover:bg-black/30 text-[#D7F000]">
                    Dismiss
                </button>
            </div>

            <!-- Content -->
            <div class="p-5 space-y-4 overflow-y-auto">
                <div class="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 space-y-2">
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-[#8A988E] font-medium">Your Token Number:</span>
                        <strong id="notif-token-number" class="font-extrabold text-[#111713] text-lg">#--</strong>
                    </div>
                    <div class="border-t border-amber-200/60 pt-2 flex items-center justify-between">
                        <div class="overflow-hidden pr-2">
                            <span class="text-[10px] font-extrabold text-[#004D2B] uppercase tracking-wider block">Serving Outlet</span>
                            <h4 id="notif-outlet-name" class="text-sm font-extrabold text-[#111713] truncate">Canteen</h4>
                            <p class="text-xs text-[#526056] truncate">Now serving: <span id="notif-range-text">--</span></p>
                        </div>
                    </div>
                </div>

                <div class="space-y-2.5 text-xs">
                    <div class="p-3 rounded-xl bg-[#FAF9F3] border border-[#E8E7DF] space-y-1">
                        <span class="text-[#8A988E] font-extrabold uppercase tracking-wider text-[10px] block">Instructions</span>
                        <p class="font-bold text-[#111713]">🏃 Head to the counter now to pick up your food!</p>
                    </div>
                </div>

                <!-- SLIDE TO ACKNOWLEDGE SLIDER -->
                <div class="pt-2">
                    <div class="slide-action-track" id="slide-track">
                        <div class="slide-action-progress" id="slide-fill"></div>
                        <span class="slide-action-text" id="slide-label">Slide to Acknowledge &rarr;</span>
                        <div class="slide-action-thumb" id="slide-thumb">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
    `;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = notifHTML;
    document.body.appendChild(wrapper.firstElementChild);

    document.getElementById('token-notif-dismiss-btn').addEventListener('click', dismissTokenNotif);

    const tokenNotifState = {
        shown: false,
        dismissedForToken: null,
        pendingToken: null,
        pollInterval: null,
    };

    function playNotificationSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const times = [0, 0.18, 0.36];
            times.forEach(t => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, ctx.currentTime + t);
                osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + t + 0.15);
                gain.gain.setValueAtTime(0.35, ctx.currentTime + t);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.15);
                osc.start(ctx.currentTime + t);
                osc.stop(ctx.currentTime + t + 0.16);
            });
        } catch(e) { /* AudioContext not supported */ }
    }

    function sendBrowserNotification(tokenNum, outletName, rangeText) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('🍽️ Your Canteen Token is Ready!', {
                body: `Token #${tokenNum} at ${outletName}. Now serving: ${rangeText}. Head to the counter!`,
                icon: '/favicon.ico',
                badge: '/favicon.ico',
                vibrate: [200, 100, 200],
                tag: 'canteen-token-' + tokenNum,
                requireInteraction: true
            });
        }
    }

    function showTokenNotifSheet(tokenNum, outletName, rangeText) {
        document.getElementById('notif-token-number').textContent = '#' + tokenNum;
        document.getElementById('notif-outlet-name').textContent = outletName;
        document.getElementById('notif-range-text').textContent = rangeText;
        
        const backdrop = document.getElementById('token-notif-backdrop');
        const sheet = document.getElementById('token-notif-sheet');
        backdrop.classList.remove('hidden');
        // Animate in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                sheet.style.transform = 'translateY(0)';
            });
        });
        tokenNotifState.shown = true;
        
        // Reset slider thumb to 0
        const thumb = document.getElementById('slide-thumb');
        const fill = document.getElementById('slide-fill');
        const label = document.getElementById('slide-label');
        thumb.style.transition = 'none';
        thumb.style.transform = 'translateX(0)';
        fill.style.width = '56px';
        label.textContent = 'Slide to Acknowledge \u2192';

        playNotificationSound();
        sendBrowserNotification(tokenNum, outletName, rangeText);
    }

    function dismissTokenNotif() {
        const sheet = document.getElementById('token-notif-sheet');
        sheet.style.transform = 'translateY(100%)';
        setTimeout(() => {
            document.getElementById('token-notif-backdrop').classList.add('hidden');
        }, 400);
        tokenNotifState.shown = false;
        if (tokenNotifState.pendingToken) {
            const p = tokenNotifState.pendingToken;
            const dismissKey = `${p.token_number}_${p.outlet_id}_${p.rangeStart}_${p.rev}`;
            localStorage.setItem('campus_notif_dismissed', dismissKey);
        }
    }

    function initSlideToAcknowledge() {
        const thumb = document.getElementById('slide-thumb');
        const track = document.getElementById('slide-track');
        const fill  = document.getElementById('slide-fill');
        const label = document.getElementById('slide-label');
        let isDragging = false, startX = 0, currentX = 0;

        function onStart(e) {
            isDragging = true;
            startX = (e.touches ? e.touches[0].clientX : e.clientX);
            thumb.style.transition = 'none';
        }
        function onMove(e) {
            if (!isDragging) return;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const maxX = track.offsetWidth - thumb.offsetWidth - 8;
            currentX = Math.max(0, Math.min(maxX, clientX - startX));
            thumb.style.transform = `translateX(${currentX}px)`;
            const pct = (currentX / maxX) * 100;
            fill.style.width = (56 + currentX) + 'px';
            
            if (pct > 60) label.textContent = 'Almost there...';
            else label.textContent = 'Slide to Acknowledge \u2192';
            if (pct >= 95) {
                isDragging = false;
                label.textContent = '✓ Acknowledged!';
                setTimeout(() => dismissTokenNotif(), 600);
            }
        }
        function onEnd() { 
            if (isDragging) {
                isDragging = false;
                thumb.style.transition = 'transform 0.3s ease';
                thumb.style.transform = 'translateX(0)';
                fill.style.width = '56px';
                label.textContent = 'Slide to Acknowledge \u2192';
            }
        }

        // Just add listeners once
        thumb.addEventListener('mousedown', onStart);
        thumb.addEventListener('touchstart', onStart, { passive: true });
        window.addEventListener('mousemove', onMove);
        window.addEventListener('touchmove', onMove, { passive: true });
        window.addEventListener('mouseup', onEnd);
        window.addEventListener('touchend', onEnd);
    }
    
    // Initialize slider once
    initSlideToAcknowledge();

    async function pollTokenNotifications() {
        if ('Notification' in window && Notification.permission === 'default') {
            await Notification.requestPermission();
        }

        tokenNotifState.pollInterval = setInterval(async () => {
            try {
                if (!window.apiFetch) return; // Wait until API is loaded
                const res = await window.apiFetch('/api/canteen/my-tokens');
                if (!res || !res.success || !res.data || res.data.length === 0) return;

                const activeTokens = res.data.filter(t => t.status === 'ACTIVE');
                if (activeTokens.length === 0) return;

                for (const token of activeTokens) {
                    const outletId = token.outlet_category_id;
                    const tokenNum = token.token_number;
                    const outletName = token.outlet ? token.outlet.name : 'Canteen';

                    let statusData;
                    try {
                        const r = await fetch(`/api/canteen/notify-status/${outletId}`);
                        const j = await r.json();
                        if (!j.success) continue;
                        statusData = j.data;
                    } catch { continue; }

                    const { range_start, range_end, notify_rev } = statusData;
                    if (range_start <= 0 || range_end <= 0 || !notify_rev || notify_rev === 0) continue;

                    const rangeText = `Tokens ${range_start}\u2013${range_end}`;
                    const dismissKey = `${tokenNum}_${outletId}_${range_start}_${notify_rev || 0}`;
                    const storedDismissKey = localStorage.getItem('campus_notif_dismissed');

                    if (tokenNum >= range_start && tokenNum <= range_end) {
                        if (storedDismissKey !== dismissKey && !tokenNotifState.shown) {
                            tokenNotifState.pendingToken = { token_number: tokenNum, outlet_id: outletId, rangeStart: range_start, rev: notify_rev || 0 };
                            showTokenNotifSheet(tokenNum, outletName, rangeText);
                            break;
                        }
                    }
                }
            } catch(e) {
                console.warn('Token notification poll error:', e);
            }
        }, 5000);
    }

    // Start polling if we are logged in
    window.addEventListener('load', () => {
        pollTokenNotifications();
    });
})();
