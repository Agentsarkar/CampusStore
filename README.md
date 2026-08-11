<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/FastAPI-Dark.svg" height="60" alt="FastAPI" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/HTML.svg" height="60" alt="HTML5" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/JavaScript.svg" height="60" alt="JavaScript" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Supabase-Dark.svg" height="60" alt="Supabase" />
</div>

<h1 align="center">Campus Ecosystem Platform</h1>

<p align="center">
  <strong>A unified hyper-local delivery, printing, and e-commerce network built for university campuses.</strong>
</p>

---

## 🚀 Overview

The **Campus Ecosystem Platform** is a monolithic architecture designed to solve real-world logistical friction within university campuses. It replaces fragmented WhatsApp groups, physical queues, and cash transactions with a seamless digital experience. 

It powers three distinct interconnected verticals:
1. **Campus Flash**: Hyper-local food delivery matching students with on-campus student riders.
2. **Campus Print Express**: Remote document printing and direct-to-dorm delivery.
3. **Canteen Fast-Track**: Digital tokens and queue management for physical cafeteria outlets.

## ✨ Key Features

- **⚡ Live Order Tracking**: Real-time status updates bridging the student, the outlet, and the rider.
- **🔐 Secure Delivery Handoffs**: OTP PIN verification required for riders to complete deliveries.
- **🖨️ Remote Printing**: Students upload PDFs, select color/BW, and print operators receive jobs in a unified queue. 
- **🛵 Peer-to-Peer Rider Network**: Students can toggle "Online" to become riders, accept flash orders, manage checklists, and earn money. 
- **💸 Razorpay Integration**: Secure digital payments processing.
- **🎨 Custom UI/UX**: Built with bespoke Vanilla CSS featuring glassmorphism, dynamic micro-animations, and a responsive bottom-sheet modal architecture.

## 🛠️ Technology Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Zero-build architecture for maximum speed)
- **Backend**: Python 3, FastAPI
- **Database**: PostgreSQL hosted on [Supabase](https://supabase.com)
- **Storage**: Supabase Buckets (for PDF print jobs and product images)
- **Payments**: Razorpay Gateway
- **Deployment**: Configured out-of-the-box for [Vercel](https://vercel.com) Serverless

## 📁 Repository Structure

```text
📦 campus-ecosystem
 ┣ 📂 client               # Vanilla JS/HTML Frontend Application
 ┃ ┣ 📂 css                # Custom Design System
 ┃ ┣ 📂 js                 # Application Logic & API calls
 ┃ ┣ 📂 rider              # Isolated Rider Dashboard & Workflow
 ┃ ┣ 📂 student            # Student Facing Dashboards (Print, Flash)
 ┃ ┗ 📜 index.html         # Main Landing Page
 ┣ 📂 server               # FastAPI Python Backend
 ┃ ┣ 📂 routers            # Domain-driven route controllers (Cart, Print, Rider, Order)
 ┃ ┣ 📂 utils              # Auth logic, OTP generation, token verification
 ┃ ┗ 📜 main.py            # ASGI Application Entrypoint
 ┣ 📜 supabase_schema.sql  # Database Schema & Policies
 ┣ 📜 vercel.json          # Serverless deployment configuration
 ┗ 📜 README.md
```

## 💻 Local Development Setup

### 1. Database Setup (Supabase)
1. Create a new project on [Supabase](https://supabase.com).
2. Navigate to the SQL Editor and run the contents of `supabase_schema.sql` to initialize all tables, triggers, and storage buckets.
3. Obtain your `Project URL` and `API Key`.

### 2. Backend Setup
```bash
# Navigate to backend
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file in the server directory
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_api_key
JWT_SECRET=your_super_secret_jwt_key
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

### 3. Running Locally
```bash
# Start the FastAPI server (it automatically serves the static client folder)
uvicorn main:app --reload
```
Navigate to `http://localhost:8000` in your browser.

## 🚀 Vercel Deployment

This repository is pre-configured for automated Vercel deployment. 

1. Push this repository to GitHub.
2. Log into Vercel and **Import Project**.
3. Under **Environment Variables**, add the keys defined in the local setup (`SUPABASE_URL`, etc.).
4. Click **Deploy**.

Vercel will automatically route `/api/*` to the Serverless FastAPI backend and serve the `client/` folder natively on the Edge network!

---
*Built with ❤️ for Campus Hackathons.*
