# Deploying Pitchly to Cloud (Render, Railway & Vercel)

Pitchly is a full-stack AI Copilot application consisting of:
- **Backend**: Django 5 + Django Channels 4 + Daphne ASGI (handles REST API and live WebSockets)
- **Frontend**: React 18 + Vite + `@dnd-kit` (interactive Kanban board & AI chat)
- **Database**: PostgreSQL (with fallback to SQLite)
- **AI Models**: Nebius Token Factory (NVIDIA / open weights models like Llama 3.1 & DeepSeek R1)

---

## Architecture on Render

```
       [ Browser / Client ]
            /         \
  (HTTP / Assets)   (WebSocket / API)
          /             \
         v               v
 [ Render Static Site ]  [ Render Web Service (Daphne ASGI) ]
  (pitchly-frontend)      (pitchly-backend: /api and /ws/)
                                 |
                                 v
                        [ Render PostgreSQL ]
                           (pitchly-db)
```

---

## Method 1: 1-Click Render Blueprint (Recommended)

Render Blueprints allow infrastructure-as-code deployment. The repository already contains [`render.yaml`](./render.yaml).

### Steps:

1. **Commit and push your changes to GitHub**:
   ```bash
   git add .
   git commit -m "Configure Render Blueprint and production settings"
   git push origin main
   ```

2. **Log into Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com/) (sign in with GitHub).

3. **Deploy via Blueprint**:
   - Click the **New +** button in the top right.
   - Select **Blueprint**.
   - Connect your GitHub repository: `HariHaran9209/Hackathon-01`.
   - Render will parse `render.yaml` and show:
     - `pitchly-db` (PostgreSQL Database - Free)
     - `pitchly-backend` (Web Service - Free)
     - `pitchly-frontend` (Static Site - Free)
   - In the environment variable prompt, enter your `NEBIUS_API_KEY` (from [Nebius Studio](https://studio.nebius.ai/)).
   - Click **Apply**.

4. **Verify Deployment**:
   - Render automatically provisions the database, runs migrations (`python manage.py migrate`), collects static files, and builds the frontend.
   - When the frontend build completes, click on your `pitchly-frontend.onrender.com` URL to open Pitchly!

---

## Method 2: Manual Setup on Render Dashboard

If you prefer configuring services step-by-step in the Render UI:

### 1. Create PostgreSQL Database
1. In Render Dashboard, click **New +** -> **PostgreSQL**.
2. Name: `pitchly-db`
3. Database: `pitchly`
4. User: `pitchly`
5. Plan: **Free**
6. Click **Create Database**.
7. Once created, copy the **Internal Database URL** (e.g., `postgres://pitchly:...@.../pitchly`).

### 2. Create Backend Web Service
1. In Render Dashboard, click **New +** -> **Web Service**.
2. Select repository: `HariHaran9209/Hackathon-01`.
3. Configure settings:
   - **Name**: `pitchly-backend`
   - **Region**: Oregon (same as your DB)
   - **Branch**: `main`
   - **Root Directory**: `pitchly/backend`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input`
   - **Start Command**: `python manage.py migrate && daphne -b 0.0.0.0 -p $PORT pitchly_backend.asgi:application`
   - **Instance Type**: `Free`
4. Add **Environment Variables**:
   | Key | Value | Notes |
   |---|---|---|
   | `DEBUG` | `False` | Production mode |
   | `SECRET_KEY` | *(generate a random string)* | Security key |
   | `ALLOWED_HOSTS` | `*` | Or `*.onrender.com` |
   | `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` | Prevents CSRF errors |
   | `DATABASE_URL` | *(paste Internal Database URL)* | From step 1 |
   | `NEBIUS_BASE_URL` | `https://api.studio.nebius.ai/v1` | API base |
   | `NEBIUS_API_KEY` | *(your Nebius API key)* | Secret key |
   | `FAST_MODEL` | `meta-llama/Meta-Llama-3.1-8B-Instruct` | Card generator |
   | `REASONING_MODEL` | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | Deep planner |
5. Click **Create Web Service**.
6. Wait for deploy to complete. Note the backend URL (e.g. `https://pitchly-backend.onrender.com`).

### 3. Create Frontend Static Site
1. In Render Dashboard, click **New +** -> **Static Site**.
2. Select repository: `HariHaran9209/Hackathon-01`.
3. Configure settings:
   - **Name**: `pitchly-frontend`
   - **Branch**: `main`
   - **Root Directory**: `pitchly/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Add **Environment Variables**:
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | `https://pitchly-backend.onrender.com` |
   | `VITE_WS_URL` | `wss://pitchly-backend.onrender.com` |
5. Add **Redirects/Rewrites**:
   - Go to **Redirects/Rewrites** tab in the static site settings.
   - Click **Add Rule**:
     - **Type**: `Rewrite`
     - **Source**: `/*`
     - **Destination**: `/index.html`
6. Click **Create Static Site**.

---

## Method 3: Alternative Platforms

### Option A: Railway (All-in-One Full Stack)
1. Go to [railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Add a **PostgreSQL** service in Railway.
4. Add your repository as a service:
   - Set **Root Directory** to `pitchly/backend`.
   - Railway will detect the [`Procfile`](./pitchly/backend/Procfile) automatically.
   - Connect the PostgreSQL database variable `DATABASE_URL`.
   - Add `NEBIUS_API_KEY`.
5. Add another service for `pitchly/frontend`:
   - Set **Root Directory** to `pitchly/frontend`.
   - Set `VITE_API_URL` to the Railway backend domain.

### Option B: Frontend on Vercel + Backend on Render
- **Frontend on Vercel**:
  1. Import `HariHaran9209/Hackathon-01` into [Vercel](https://vercel.com/).
  2. Set Framework Preset to **Vite**.
  3. Set Root Directory to `pitchly/frontend`.
  4. Add Environment Variable `VITE_API_URL=https://your-backend.onrender.com`.
  5. Deploy.
- **Backend on Render**:
  - Keep the Daphne ASGI service running on Render (as outlined in Method 2).

---

## Production & Free-Tier Tips

1. **Render Free Tier Spin-Down (Cold Starts)**:
   - Render's free tier web services spin down after 15 minutes of inactivity. When a new request arrives, it may take 30–50 seconds to wake up.
   - **Solution**: Set up a free uptime monitor (like [UptimeRobot](https://uptimerobot.com/) or [cron-job.org](https://cron-job.org/)) to ping `https://your-backend.onrender.com/health/` every 10 minutes.

2. **Render Free PostgreSQL 30-Day Limit**:
   - Render's free PostgreSQL database is automatically deleted after 30 days.
   - **Permanent Free Alternative**: Create a free PostgreSQL database on [Neon.tech](https://neon.tech/) or [Supabase](https://supabase.com/). Simply set the `DATABASE_URL` environment variable in Render to your Neon/Supabase connection string!

3. **WhiteNoise Static Serving**:
   - WhiteNoise is already configured to compress and serve Django admin and REST framework assets directly in production with zero extra configuration.

4. **Health Check Endpoint**:
   - The backend provides a `/health/` endpoint that returns `{"status": "healthy"}` for container health monitoring.
