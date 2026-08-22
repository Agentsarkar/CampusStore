<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/FastAPI-Dark.svg" height="60" alt="FastAPI" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/HTML.svg" height="60" alt="HTML5" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/JavaScript.svg" height="60" alt="JavaScript" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Supabase-Dark.svg" height="60" alt="Supabase" />
</div>

<h1 align="center">Campus Ecosystem Platform & AI Consumer Shield</h1>

<p align="center">
  <strong>A unified hyper-local delivery, printing, and e-commerce network with integrated algorithmic consumer defense built for university campuses.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Architecture-FastAPI%20%7C%20Supabase-green.svg" alt="Stack">
  <img src="https://img.shields.io/badge/Award-2nd%20Place%20Winner-gold.svg" alt="Hackathon Award">
</p>

---

## 🏆 Hackathon Recognition & Validation

- **2nd Place Winner** at the Inter-College Hackathon Finals (August 2026).
- **Enterprise System Validation**: Evaluated and commended by engineers as an *"IIT-grade production architecture"* for its real-time API integrations, resilient background task handling, and forensic dynamic pricing detection engine.

---

## 👨‍💻 System Architecture & Lead Authorship

* **Core Maintainer & Lead Systems Architect**: **Anurag Sarkar** ([@your-github-username](https://github.com/your-github-username))
  * Solely engineered the monolithic FastAPI backend, database schema, JWT auth lifecycle, and external API pipelines.
  * Designed the proprietary **Dynamic Pricing Manipulation Index (DPMI)** and **Cohort-Based Scarcity Auditor**.
* **Frontend Designer**: Keshav Rajesh Maheshwari *(Client UI layout support)*

---

## 🚀 Overview

The **Campus Ecosystem Platform** resolves operational and financial friction within university campuses. It replaces fragmented WhatsApp groups, physical queues, cash transactions, and predatory third-party aggregator pricing with a unified digital ecosystem.

It powers four distinct interconnected verticals:
1. **Campus Flash**: Hyper-local food delivery matching students with on-campus student riders.
2. **Campus Print Express**: Remote document printing with direct-to-dorm delivery.
3. **Canteen Fast-Track**: Digital queue management and real-time token synchronization.
4. **Campus Concierge & AI Trust Shield**: An active consumer protection engine auditing third-party ticketing/travel vendors against cookie tracking, artificial scarcity, and predatory dynamic pricing.

---

## ✨ Key Features

### 📦 Campus Logistics & Commerce
- **⚡ Live Order Tracking**: Real-time status updates bridging student, merchant, and rider.
- **🔐 Secure Delivery Handoffs**: Cryptographic OTP PIN verification required for delivery completion.
- **🖨️ Remote Print Queue**: Student PDF ingestion with automated page metrics and operator queues.
- **🛵 Peer-to-Peer Rider Network**: Dynamic student rider toggle with real-time checklist state machines.
- **💸 Integrated Checkout**: Razorpay API handling seamless payment flows.

### 🛡️ Algorithmic Consumer Defense (AI Trust Shield)
- **Mathematical Surge Anomaly Detection (DPMI)**: Computes a standardized Z-Score deviation against historical price arrays, penalizing high-frequency view counts and false countdown timers:
  $$\text{DPMI} = \text{Sigmoid}\left( w_1 \cdot Z_{\text{score}} + w_2 \cdot \log(1 + V_{\text{views}}) + w_3 \cdot S_{\text{FOMO}} \right)$$
- **Cohort-Based Scarcity Auditing**: Verifies "Only 1 Seat Left" claims against a rolling 3-month snapshot baseline to distinguish genuine capacity crunches from artificial dark patterns.
- **Clean-Room Proxy Buying**: Client-side counter-purchasing tool that strips tracking cookies and queries fresh API sessions directly.

---

## 🛠️ Technology Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Zero-build client architecture)
- **Backend**: Python 3.11, FastAPI, Uvicorn ASGI
- **Database & Auth**: PostgreSQL hosted on [Supabase](https://supabase.com), Row Level Security (RLS), JWT
- **Storage**: Supabase Storage Buckets (Encrypted PDF handling)
- **Intelligence & Telemetry**: SearchApi (Google Flights Engine), OpenRouter LLM API
- **Payments**: Razorpay Gateway API
- **Deployment**: Configured for serverless hosting on [Vercel](https://vercel.com)

---

## 📁 Repository Structure

```text
📦 campus-ecosystem
 ┣ 📂 client                 # Client Application
 ┃ ┣ 📂 css                  # Custom Design System
 ┃ ┣ 📂 js                   # Application Logic & API calls
 ┃ ┣ 📂 rider                # Isolated Rider Dashboard & Workflow
 ┃ ┣ 📂 student              # Student Facing Dashboards (Print, Flash, Concierge)
 ┃ ┗ 📜 index.html           # Main Landing Page
 ┣ 📂 server                 # FastAPI Python Backend
 ┃ ┣ 📂 routers              # Domain-driven controllers (Cart, Print, Rider, Order, Audit)
 ┃ ┣ 📂 utils                # Auth logic, OTP generation, DPMI math engine
 ┃ ┗ 📜 main.py              # ASGI Application Entrypoint
 ┣ 📜 supabase_schema.sql    # Database Schema, Policies & Cohort Snapshots
 ┣ 📜 vercel.json            # Serverless deployment configuration
 ┣ 📜 LICENSE                # MIT License
 ┗ 📜 README.md
