# Cloud Hosting Options - Research TODO

**Goal:** Find the best platform to host job-lead-finder online for users who don't want to run Docker locally.

## Evaluation Criteria

### Must-Have
- Free tier or generous trial
- Docker/container support
- Auto-deploy from GitHub
- HTTPS included
- Reasonable cold start times (<5s)

### Nice-to-Have
- Automatic scaling
- Built-in monitoring
- Database hosting
- CDN integration
- Multiple regions

---

## Platform Comparison Matrix

| Platform                      | Free Tier               | Cold Start          | GitHub Integration        | Notes                       |
| ----------------------------- | ----------------------- | ------------------- | ------------------------- | --------------------------- |
| **Fly.io**                    | ✅ 3 VMs, 256MB RAM each | ~1-2s               | ✅ flyctl + GitHub Actions | Edge deployment, global     |
| **Railway.app**               | ✅ $5/month credit       | ~2-3s               | ✅ Native integration      | Simple, dev-friendly        |
| **Render**                    | ✅ 750 hours/month       | ~30-60s (free tier) | ✅ Auto-deploy on push     | Spins down after 15min idle |
| **Cloud Run (GCP)**           | ✅ 2M requests/month     | ~1-3s               | ✅ Via Cloud Build         | Serverless, pay-per-use     |
| **AWS Fargate**               | ❌ Pay-per-use only      | ~3-5s               | ✅ Via ECS + CodePipeline  | AWS ecosystem integration   |
| **Azure Container Instances** | ❌ Pay-per-second        | ~5-10s              | ✅ Via Container Registry  | Pay-per-second billing      |
| **Heroku**                    | ⚠️ Free tier removed     | N/A                 | ✅ Git push to deploy      | Now paid only               |

---

## Detailed Evaluation

### 🥇 Top Pick: Fly.io
**Pros:**
- True edge deployment (runs close to users globally)
- Generous free tier (3 shared-cpu VMs)
- Fast cold starts
- Great for async/background workers
- Multi-region deployment simple

**Cons:**
- Smaller community than AWS/GCP
- Less documentation for complex scenarios

**Cost Estimate:**
- Free: Up to ~1000 requests/day
- $5-10/month: Small production workload
- $50-100/month: 10K active users

**One-Click Deploy:**
```bash
# Create fly.toml, then:
fly deploy
```

---

### 🥈 Runner-Up: Railway.app
**Pros:**
- Extremely simple deployment
- Built-in database hosting
- Nice web UI
- Good for monorepos

**Cons:**
- Less control over infrastructure
- Free tier limited to $5 credit/month

**Cost Estimate:**
- Free: $5 credit (~ few hundred requests)
- $5-20/month: Small production
- $50-150/month: 10K users

**One-Click Deploy:**
- Connect GitHub repo in Railway UI
- Auto-detects Dockerfile

---

### 🥉 Third Place: Google Cloud Run
**Pros:**
- Massive free tier (2M requests/month)
- True serverless (zero cost when idle)
- Tight integration with GCP services
- Auto-scaling built-in

**Cons:**
- More complex setup than Fly/Railway
- Requires GCP account
- Cold starts can be slower on free tier

**Cost Estimate:**
- Free: Up to 2M requests/month (!)
- $10-30/month: Production with reserved instances
- $100-200/month: 10K active users

**Setup:**
```bash
gcloud run deploy job-lead-finder \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Kubernetes Journey - Considerations

### Local Development
**Recommended:** k3s or minikube
- k3s: Lightweight, production-like
- minikube: Feature-rich, easy debugging

### Cloud Kubernetes Options
| Provider          | Service         | Free Tier                     | Notes               |
| ----------------- | --------------- | ----------------------------- | ------------------- |
| **Google**        | GKE Autopilot   | ❌ $70/month minimum           | Most managed        |
| **AWS**           | EKS             | ❌ $75/month for control plane | Industry standard   |
| **Azure**         | AKS             | ✅ Free control plane          | Pay for nodes only  |
| **Civo**          | Civo Kubernetes | ✅ $5 credit                   | Lightweight K8s     |
| **Digital Ocean** | DOKS            | ❌ $12/month minimum           | Simple, predictable |

**Reality Check:** For job-lead-finder scale, Kubernetes is overkill initially. Start with:
1. **Now:** Docker on Fly.io/Railway
2. **Growth phase:** Cloud Run serverless
3. **Scale:** Consider K8s when >10K concurrent users

---

## Recommendation Path

### Phase 1: Immediate (This Week)
**Deploy to:** Fly.io + Railway.app
- Create both configs
- Add "Deploy to Fly.io" and "Deploy to Railway" buttons to README
- Document setup for each

### Phase 2: Scale Testing (Month 2)
**Add:** Google Cloud Run
- Test auto-scaling behavior
- Compare costs under load
- Keep as backup option

### Phase 3: Enterprise-Ready (Month 3+)
**Explore:** Kubernetes on Civo or AKS
- Learn K8s fundamentals
- Setup staging environment
- Document migration path

---

## Action Items for Tomorrow

### High Priority
- [ ] Create Fly.io configuration (`fly.toml`)
- [ ] Create Railway.app configuration (`railway.json`)
- [ ] Test deploy to both platforms
- [ ] Add deploy buttons to README
- [ ] Write deployment guides

### Medium Priority
- [ ] Setup Cloud Run configuration
- [ ] Create cost calculator spreadsheet
- [ ] Document environment variable setup for each platform

### Low Priority (Research)
- [ ] Investigate Kubernetes learning path
- [ ] Test k3s locally with Docker Desktop
- [ ] Create basic K8s manifests for future reference

---

## Decision Matrix

**Choose Fly.io if:**
- Need global edge deployment
- Want fast cold starts
- Prefer infrastructure-as-code

**Choose Railway.app if:**
- Want simplest possible deployment
- Need integrated database
- Prefer GUI over CLI

**Choose Cloud Run if:**
- Expect highly variable traffic
- Want truly serverless (pay only when used)
- Already using GCP ecosystem

**Recommendation:** Support all three, document Fly.io as primary.

---

## Success Criteria

By end of implementation:
- [ ] ≤10 minutes from git clone to deployed URL
- [ ] Auto-deploy on main branch push
- [ ] HTTPS enabled automatically
- [ ] Environment variables easily configurable
- [ ] Cost <$10/month for demo workload
- [ ] One-click rollback capability

---

## Future: Self-Hosting Options

For advanced users who want full control:

**Documentation to Create:**
- [ ] Docker Compose for VPS deployment
- [ ] Systemd service setup guide
- [ ] Nginx reverse proxy configuration
- [ ] Automated backups setup
- [ ] Monitoring stack (Prometheus + Grafana)

**Platforms to Document:**
- Hetzner Cloud (~$5/month for small VPS)
- Digital Ocean Droplets
- AWS EC2 (with spot instances)
- Home server setup (Raspberry Pi / NUC)
