# 100% Free Deployment Guide (No Credit Card Required)

This guide shows you how to deploy **Pitchly** completely **free** without paid plans, without Render Blueprints, and without needing to install or manage complicated databases.

---

## 💡 Why Not Blueprints or Local PostgreSQL?

1. **Render Blueprints**: Render requires a paid plan or credit card verification when launching databases or multiple services via Blueprints (`render.yaml`).
2. **Individual Services are 100% FREE**: Creating an individual **Web Service** or **Static Site** on Render is **completely free** with **no credit card needed**.
3. **The Database Dilemma**:
   - Installing and configuring PostgreSQL locally is complicated (ports, users, pgAdmin, services).
   - In contrast, people love **MongoDB Atlas** because you just copy a cloud URL.
   - **However, Django is a relational SQL framework**. Swapping Django's ORM to MongoDB breaks built-in Django features (ForeignKeys, migrations, admin, and ID auto-increments).
   - **The Solution**: Use **Neon.tech** (Serverless PostgreSQL) or **Supabase**!
     - It gives you the **exact same copy-paste cloud URL experience as MongoDB Atlas**.
     - 100% **free forever**, **no credit card**, no local installation.
     - Or even simpler: **Pitchly works out of the box with built-in SQLite** (zero setup needed!).

---

## 🚀 Recommended 100% Free Architecture

| Component | Platform | Cost | Credit Card? |
|---|---|---|---|
| **Frontend** | **Vercel** or **Render Static Site** | Free | ❌ None |
| **Backend** | **Render Web Service** (Manual) | Free | ❌ None |
| **Database** | **Neon.tech** (Serverless DB) or **Built-in SQLite** | Free | ❌ None |

---

## Step 1: Get a Free Cloud Database (1 Minute — 0 Setup)

> *Skip this step if you want to test with built-in SQLite first!*

1. Go to **[neon.tech](https://neon.tech/)** and click **Sign Up** (use your GitHub or Google account).
2. Click **Create Project**, name it `pitchly`, and click **Create**.
3. On the project dashboard, you will see a connection string:
   ```text
   postgresql://alex:AbC123dEf@ep-cool-fog-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Copy this string. That's it! You have a fully managed, permanent cloud database with zero configuration.

---

## Step 2: Deploy Backend to Render (100% Free)

1. Go to **[dashboard.render.com](https://dashboard.render.com/)** and log in with GitHub.
2. Click **New +** in the top-right corner and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and select your repository: **`HariHaran9209/Hackathon-01`**.
4. Fill in the service settings:
   - **Name**: `pitchly-backend`
   - **Region**: Oregon (or nearest to you)
   - **Branch**: `main`
   - **Root Directory**: `pitchly/backend`
   - **Runtime**: `Python`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --no-input
     ```
   - **Start Command**:
     ```bash
     python manage.py migrate && daphne -b 0.0.0.0 -p $PORT pitchly_backend.asgi:application
     ```
   - **Instance Type**: Select **Free** ($0/month).
5. Scroll down to **Environment Variables** and add:
   | Key | Value | Notes |
   |---|---|---|
   | `DEBUG` | `False` | Production mode |
   | `SECRET_KEY` | *(type any random 30-character text)* | e.g. `pitchly-secret-prod-key-xyz-123` |
   | `ALLOWED_HOSTS` | `*` | Allows Render domain |
   | `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` | Prevents CSRF issues |
   | `CORS_ALLOW_ALL_ORIGINS` | `True` | Allows frontend access |
   | `DATABASE_URL` | *(paste the Neon connection string from Step 1)* | Leave empty to use SQLite |
   | `NEBIUS_BASE_URL` | `https://api.studio.nebius.ai/v1` | AI endpoint |
   | `NEBIUS_API_KEY` | *(your Nebius API key or leave empty for offline demo)* | Optional |
6. Click **Create Web Service**.
7. Render will build and deploy the backend. Once deployed, copy your backend URL (e.g. `https://pitchly-backend.onrender.com`).
8. You can verify it's working by opening `https://pitchly-backend.onrender.com/health/` in your browser. It will return:
   ```json
   {"status": "healthy", "service": "pitchly-backend"}
   ```

---

## Step 3: Deploy Frontend (Choose Vercel or Render)

### Option A: Deploy on Vercel (Fastest & 100% Free)

1. Go to **[vercel.com](https://vercel.com/)** and log in with GitHub.
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository: **`HariHaran9209/Hackathon-01`**.
4. In the configuration screen:
   - **Framework Preset**: Vite
   - **Root Directory**: Click *Edit* and select **`pitchly/frontend`**.
5. Expand **Environment Variables** and add:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://pitchly-backend.onrender.com` *(your backend URL from Step 2)*
6. Click **Deploy**.
7. In ~30 seconds, your site is live!

---

### Option B: Deploy on Render Static Site (100% Free)

1. On the **Render Dashboard**, click **New +** -> **Static Site**.
2. Select your repository: **`HariHaran9209/Hackathon-01`**.
3. Configure settings:
   - **Name**: `pitchly-frontend`
   - **Branch**: `main`
   - **Root Directory**: `pitchly/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL`: `https://pitchly-backend.onrender.com`
5. Click **Advanced** -> scroll to **Redirects/Rewrites** and add:
   - **Type**: `Rewrite`
   - **Source**: `/*`
   - **Destination**: `/index.html`
6. Click **Create Static Site**.

---

## ⚡ Important Free-Tier Tips

1. **Free Backend Spin-Down (Cold Starts)**:
   - Render's free tier spins down the backend after 15 minutes of inactivity. When someone visits, it can take ~40 seconds to wake up.
   - **Free Fix**: Use a free monitoring service like [cron-job.org](https://cron-job.org/) or [UptimeRobot](https://uptimerobot.com/) to send an HTTP GET request to `https://pitchly-backend.onrender.com/health/` every 10 minutes.
2. **WebSocket Auto-Detection**:
   - The frontend automatically detects the protocol. When `VITE_API_URL` is set to `https://pitchly-backend.onrender.com`, it automatically connects WebSockets to `wss://pitchly-backend.onrender.com/ws/projects/...`.
