# Campus Rider Console — Frontend Module

This directory contains the standalone, isolated **Campus Rider Console** application for delivery partners.

---

## 📁 Architecture & File Structure

All rider files and resources are strictly contained within `rider/`:

```
rider/
├── index.html            # Main Rider Dashboard (Offline, Online Radar, Go Online Modal, Incoming Request Modal)
├── login.html            # Rider Sign In Screen with validation
├── register.html         # Rider Application Form with ID document upload & cancellation
├── pending.html          # Verification Gate Screen (Locked until admin approval)
├── order.html            # Active Delivery Workflow (Pickup Collection, Transit, Delivery & Completed states)
├── css/
│   └── rider.css         # Isolated Design Tokens, Bottom-Sheets, Radar & Slider animations
├── js/
│   └── rider.js          # Isolated State Engine, LocalStorage Recovery, Stores Config Loader & API Abstractions
├── config/
│   └── stores.json       # Store Details (Name, Location, Contact, Pickup Instructions)
└── README.md             # Architectural & Module Documentation
```

---

## 🔄 Delivery Partner Workflow Flow

1. **Rider Registration & ID Verification** (`register.html` → `pending.html`)
   - Applicant submits details and uploads Campus ID / Driver's License document.
   - Profile status is set to `PENDING_VERIFICATION`.
   - Access to online status is locked until verified (Demo evaluator override available on `pending.html`).

2. **Offline Dashboard & Safety Guidelines** (`index.html`)
   - Rider reviews safety & duty guidelines card.
   - Clicking **"I Understand"** opens the Go Online bottom-sheet modal.

3. **Go Online Bottom Sheet** (`index.html` Modal)
   - Displays session availability, location check, and bag check.
   - Action **"Go Online"** updates rider status to `ONLINE` with pulsing green badge.

4. **Online Radar & Listening State** (`index.html`)
   - Animated radar search listens for incoming delivery requests.
   - **Simulate Incoming Order** trigger opens the request notification modal.

5. **Incoming Order Request & Slide-to-Accept** (`index.html` Modal)
   - Store details loaded dynamically from `rider/config/stores.json`.
   - Operational values use neutral placeholders (`₹-- (Demo)`).
   - Rider slides the **Slide to Accept Order →** slider to confirm assignment.

6. **Order Collection / Pickup Screen** (`order.html` — Step 1)
   - Displays pickup store details strictly from `stores.json`.
   - Collection instructions & verification checklist.
   - Rider slides **Slide to Pick Order →** when meals are collected.

7. **Delivery State / En Route** (`order.html` — Step 2)
   - Updates status to `ORDER PICKED / IN TRANSIT`.
   - Displays customer destination (`Hostel Block B`), delivery notes & instructions.
   - Rider slides **Slide to Complete Delivery →** upon reaching destination.

8. **Completed State** (`order.html` — Completion Card)
   - Celebratory success summary card.
   - Button returns rider cleanly to the Online Dashboard.

---

## ⚙️ Store Configuration

Store data is loaded dynamically from `rider/config/stores.json`:

```json
{
  "stores": [
    {
      "id": "canteen-central",
      "name": "Central Campus Canteen",
      "location": "Student Activity Center, Ground Floor, Counter 3",
      "contact": "Counter Ext 401",
      "instructions": "Collect order from Counter 3. Verify item count with canteen supervisor before packaging."
    }
  ]
}
```

---

## 🔌 API Abstraction Hooks (`rider/js/rider.js`)

The frontend contains clean API contract abstractions ready for future backend integration:

- `riderRegistration(data)`
- `riderLogin(email, password)`
- `getRiderVerificationState()`
- `updateRiderStatus(isOnline)`
- `getAvailableOrders()`
- `acceptOrderApi(orderId)`
- `updateOrderStatusApi(orderId, newStatus)`
- `getStoresConfig()`

---

## 🧪 Demo Mode & Evaluator Controls

- **Demo State Persistence**: App state persists cleanly in `localStorage` under `campus_rider_app_state`.
- **Demo State Reset**: Click **Reset State 🔄** in the Demo Flow Controller at any time to clear local state.
