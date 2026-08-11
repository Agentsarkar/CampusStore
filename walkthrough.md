# Walkthrough: Campus E-Commerce Rewrite

We have successfully rewritten the Blinkit-style grocery e-commerce store into a simplified, campus-focused delivery application using **Python (FastAPI)** and **Supabase (PostgreSQL)** on the backend, and **Vanilla HTML, CSS, and JavaScript** on the frontend.

---

## What Was Accomplished

### 1. Database Schema (`supabase_schema.sql`)
- Created a fresh PostgreSQL script to set up all tables inside Supabase SQL Editor.
- Modified address structure to target campus delivery details: `room_number`, `building_name`, and `branch`.
- Simplified relations by removing subcategories and linking products directly to flat categories.

### 2. Python Backend (`/server`)
- Built a **FastAPI** web server with modular routing:
  * **Auth/Users**: Supports direct email registration, login, profile updates, and email/password validations. Direct authentication bypasses complex OTP/email confirmation for quick campus onboarding.
  * **Categories**: Category CRUD and lookup.
  * **Products**: Product CRUD, catalog pagination, details, and search query filters.
  * **Cart**: Manages user cart sessions in PostgreSQL tables.
  * **Address**: Manages campus delivery locations.
  * **Orders**: Submits Cash on Delivery / Pay on Delivery checkouts and manages order logs.
  * **Uploads**: Integrated with **Supabase Storage** to save uploaded files (category and product images) directly into a public storage bucket.

### 3. Vanilla Frontend (`/client`)
- Converted React + Vite JSX elements into simple, fast-loading, pure HTML files styled with Tailwind CSS CDN and FontAwesome icon toolsets.
- Created `js/app.js` (Unified State and Layout Manager) that dynamically injects shared components (Header, Footer, Cart sliding drawer) and synchronizes user authentication and shopping cart states.
- Implemented clean, smooth custom CSS toast alerts.
- Built a tabbed `dashboard.html` for profile edits, address listings, order history, and admin actions (adding/deleting categories and products with direct file uploading previews).

---

## File Summary

- [supabase_schema.sql](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/supabase_schema.sql): PostgreSQL tables schema.
- [SETUP.md](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/SETUP.md): Run & Configuration instructions.
- [server/requirements.txt](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/server/requirements.txt): Python backend dependencies.
- [server/config.py](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/server/config.py): Configures Supabase client.
- [server/main.py](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/server/main.py): Entrypoint launching the FastAPI application.
- [client/js/app.js](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/client/js/app.js): Core state synchronizer.
- [client/index.html](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/client/index.html): Store home page.
- [client/checkout.html](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/client/checkout.html): Order checkout details.
- [client/dashboard.html](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/client/dashboard.html): Tabbed user/admin panels.

---

## How to Verify Functionality

1. Open **Supabase** and run [supabase_schema.sql](file:///c:/Users/THE%20GAMERS%20CHOICE/Documents/Hackathon/supabase_schema.sql) to build tables. Create a public bucket `grocery-images` under Storage.
2. In `/server`, create a `.env` file containing your `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and a JWT `SECRET_KEY`.
3. Launch the API server:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
4. Access the API documentation at `http://localhost:8000/docs` to inspect endpoints.
5. In `/client`, launch a quick HTTP server:
   ```bash
   python -m http.server 3000
   ```
6. Open `http://localhost:3000` in your web browser:
   - Create a user account and log in.
   - Set up your default address details (Room, Building, Branch) under Dashboard.
   - Upload new categories and products in the Admin tab.
   - Add items to your cart, proceed to checkout, select your location, and place your Pay on Delivery order!
