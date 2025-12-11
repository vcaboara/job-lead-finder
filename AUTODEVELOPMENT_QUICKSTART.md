# Autodevelopment Quick Reference

## 🚀 Execute AI Task (5-Minute Guide)

### 1. Read Task
```powershell
Get-Content .ai-tasks/track-8-gemini-logo-ui.md
```

### 2. Screenshot BEFORE
```powershell
docker compose up -d
Start-Process "http://localhost:8000"
# Screenshot: Save as "before.png"
```

### 3. Get Code from Gemini
- Copy task file content
- Paste into Gemini (web/API)
- Gemini provides HTML/CSS code

### 4. Apply Code
- Edit `src/app/templates/index.html`
- Paste Gemini's code

### 5. Screenshot AFTER
```powershell
docker compose up --build -d
Start-Process "http://localhost:8000"
# Screenshot: Save as "after.png"
```

### 6. Create PR
```bash
git checkout -b auto/ui-company-logo-placeholders
git add src/app/templates/index.html CHANGELOG.md
git commit -m "feat: Add company logo placeholders"
git push -u origin auto/ui-company-logo-placeholders
gh pr create --title "feat: Company logo placeholders"
# Upload before.png and after.png in PR description
```

### 7. Run Review Chain
```bash
python scripts/ai_review_chain.py <PR_NUMBER>
```

Done! ✅

---

## 📋 Review Workflow

```
Gemini → Ollama → Copilot → Human
  ↓        ↓         ↓         ↓
 Code   Quality   Guidelines Approve
```

**Run review:**
```bash
python scripts/ai_review_chain.py 85
```

---

## 🎯 Available Tasks

List all tasks:
```powershell
Get-ChildItem .ai-tasks/*.md
```

Current tasks:
- `track-1-gemini.md` - Resource monitor dashboard
- `track-2-copilot.md` - Email integration
- `track-8-gemini-logo-ui.md` - **Company logos** ⭐

Generate more:
```bash
python scripts/autonomous_task_executor.py
```

---

## 🔧 Common Commands

**Start services:**
```powershell
docker compose up -d
```

**View UI:**
```powershell
Start-Process "http://localhost:8000"
```

**Check PR status:**
```bash
gh pr checks <PR_NUMBER> --watch
```

**Review PR locally:**
```bash
gh pr checkout <PR_NUMBER>
docker compose up --build -d
```

---

## 📌 Remember

**Try lovable.dev for company logos!** 🎨

---

## 🆘 Troubleshooting

**Ollama not responding:**
```bash
docker compose ps ollama
docker compose logs ollama
```

**Missing dependencies:**
```bash
pip install httpx
```

**Reset environment:**
```bash
docker compose down
docker compose up --build -d
```
