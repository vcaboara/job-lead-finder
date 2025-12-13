# Free Hosting Options for JobForge Dashboard

## Recommended: Railway.app (Best for Python/Docker)

### Pros
- ✅ Free tier: $5/month credit (enough for small apps)
- ✅ Native Docker support (uses our existing Dockerfile)
- ✅ Postgres, Redis included
- ✅ Automatic HTTPS
- ✅ GitHub integration (auto-deploy on push)
- ✅ Environment variables UI
- ✅ Python/Flask friendly

### Cons
- ⚠️ Needs credit card (won't charge without approval)
- ⚠️ $5/month after free trial (very cheap)

### Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init
railway up
```

Configuration needed:
- Set PORT=8000 environment variable
- Mount volume for /app/data persistence
- Configure GEMINI_API_KEY, GOOGLE_API_KEY, etc.

---

## Alternative 1: Fly.io (Docker-focused)

### Pros
- ✅ Free tier: 3 shared VMs, 3GB storage
- ✅ Excellent Docker support
- ✅ Fast global deployment
- ✅ Automatic HTTPS
- ✅ GitHub Actions integration

### Cons
- ⚠️ Requires credit card
- ⚠️ CLI-heavy (less web UI)
- ⚠️ More complex configuration

### Setup
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch app
fly launch
fly deploy
```

---

## Alternative 2: Render.com (Easiest setup)

### Pros
- ✅ True free tier (no credit card)
- ✅ Docker support
- ✅ Auto-deploy from GitHub
- ✅ Great web UI
- ✅ Free Postgres database
- ✅ Automatic HTTPS

### Cons
- ⚠️ Free tier spins down after 15min inactivity (50s cold start)
- ⚠️ Limited to 512MB RAM on free tier
- ⚠️ May be slow for our app

---

## Alternative 3: Vercel (Frontend-focused, limited backend)

### Pros
- ✅ No credit card needed
- ✅ Excellent for static/Next.js apps
- ✅ CDN, automatic HTTPS
- ✅ GitHub integration

### Cons
- ❌ Not ideal for Python/Flask
- ❌ 10-second serverless timeout
- ❌ Limited backend functionality
- ❌ Would need major refactor

---

## Alternative 4: PythonAnywhere (Python-specific)

### Pros
- ✅ Free tier available
- ✅ Python-focused
- ✅ No credit card
- ✅ Simple setup

### Cons
- ❌ Limited to 512MB RAM
- ❌ CPU throttling on free tier
- ❌ No Docker support
- ❌ Limited customization

---

## Alternative 5: Heroku (Historical option)

### Status
- ❌ No longer offers free tier (as of Nov 2022)
- ⚠️ $5/month minimum now

---

## Recommendation

**For JobForge Dashboard: Railway.app**

Why:
1. Native Docker support (use existing Dockerfile)
2. Persistent storage for job data
3. Environment variable management
4. GitHub auto-deploy
5. Affordable ($5/month is reasonable for a live app)

**Setup Steps:**

1. Install Railway CLI
   ```powershell
   npm install -g @railway/cli
   ```

2. Create railway.toml
   ```toml
   [build]
   builder = "dockerfile"
   dockerfilePath = "Dockerfile"

   [deploy]
   startCommand = "python -m uvicorn app.ui_server:app --host 0.0.0.0 --port $PORT"
   healthcheckPath = "/"
   healthcheckTimeout = 30
   ```

3. Configure environment variables in Railway dashboard:
   - GEMINI_API_KEY
   - GOOGLE_API_KEY
   - RAPIDAPI_KEY
   - GITHUB_TOKEN
   - OLLAMA_BASE_URL (optional, for local Ollama)

4. Deploy
   ```bash
   railway login
   railway init
   railway up
   ```

5. Custom domain (optional)
   - Free .railway.app subdomain
   - Can add custom domain

**Data Persistence:**
Railway provides persistent volumes. Configure in railway.toml:
```toml
[[services]]
name = "app"

[[services.volumes]]
mountPath = "/app/data"
name = "job-data"
```

This ensures job leads persist across deployments.
