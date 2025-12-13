# Ollama Tunnel Setup for Free AI PR Reviews

This guide helps you set up a secure tunnel to your local Ollama instance so GitHub Actions can access it for free AI-powered code reviews.

## Why Use Local Ollama?

- **Free**: No API costs for code reviews
- **Privacy**: Your code never leaves your infrastructure
- **Fast**: Direct access to your GPU
- **Always Available**: As long as your computer is on

## Prerequisites

1. Ollama installed and running locally
2. Models downloaded (you already have `deepseek-coder:6.7b`, `codellama:7b`, etc.)
3. Cloudflared installed (for tunnel)

## Quick Setup

### 1. Install Cloudflared (if not already done)

```powershell
winget install --id Cloudflare.cloudflared
```

After installation, restart your PowerShell terminal or refresh PATH:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### 2. Start Ollama Tunnel

Open a new terminal and run:
```powershell
cloudflared tunnel --url http://localhost:11434
```

You'll see output like:
```
2025-12-09T16:30:00Z INF +--------------------------------------------------------------------------------------------+
2025-12-09T16:30:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2025-12-09T16:30:00Z INF |  https://random-words-1234.trycloudflare.com                                               |
2025-12-09T16:30:00Z INF +--------------------------------------------------------------------------------------------+
```

**Copy the `https://` URL** - this is your tunnel endpoint.

### 3. Set GitHub Secret

```powershell
gh secret set OLLAMA_BASE_URL --body "https://your-tunnel-url.trycloudflare.com"
```

### 4. Test the Tunnel

From another terminal:
```powershell
curl https://your-tunnel-url.trycloudflare.com/api/tags
```

You should see your Ollama models listed.

## How It Works

1. GitHub Actions workflow checks for `OLLAMA_BASE_URL` secret
2. If found, sends PR diff to your local Ollama via tunnel
3. Ollama generates review using `deepseek-coder:6.7b`
4. Review is posted as PR comment

## Workflow Priority

The AI PR review workflow tries providers in this order:

1. **Gemini Flash 2.0** (if `GEMINI_API_KEY` has credits)
2. **OpenAI GPT-4o** (if `OPENAI_API_KEY` has credits)
3. **Local Ollama** (if `OLLAMA_BASE_URL` is set and tunnel is running)
4. **Skip Review** (if all fail - no error spam)

## Keeping Tunnel Running

### Option 1: Manual (for testing)
Keep the `cloudflared tunnel` command running in a terminal while working.

### Option 2: Background Service (recommended)

Create a scheduled task to run cloudflared on startup:

```powershell
$action = New-ScheduledTaskAction -Execute 'cloudflared' -Argument 'tunnel --url http://localhost:11434'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U
Register-ScheduledTask -TaskName "Ollama Tunnel" -Action $action -Trigger $trigger -Principal $principal -Description "Cloudflare tunnel for Ollama AI"
```

Note: The tunnel URL changes each time cloudflared restarts, so you'll need to update the GitHub secret when restarting.

### Option 3: Named Tunnel (persistent URL)

For a permanent URL that doesn't change:

1. Login to Cloudflare:
   ```powershell
   cloudflared tunnel login
   ```

2. Create a named tunnel:
   ```powershell
   cloudflared tunnel create ollama-ai
   ```

3. Configure the tunnel (create `~/.cloudflared/config.yml`):
   ```yaml
   tunnel: <tunnel-id-from-step-2>
   credentials-file: C:\Users\<your-username>\.cloudflared\<tunnel-id>.json

   ingress:
     - hostname: ollama.yourname.workers.dev
       service: http://localhost:11434
     - service: http_status:404
   ```

4. Route DNS (follow cloudflared instructions)

5. Run tunnel:
   ```powershell
   cloudflared tunnel run ollama-ai
   ```

## Security Considerations

- The tunnel URL is public but randomly generated
- Only your GitHub Actions can use the `OLLAMA_BASE_URL` secret
- Cloudflare provides DDoS protection
- Ollama API itself has no authentication by default (fine for local use)
- Consider rate limiting if exposing publicly long-term

## Troubleshooting

### Tunnel URL not working
- Check if Ollama is running: `ollama list`
- Verify tunnel is active: look for "Your quick Tunnel has been created"
- Test locally first: `curl http://localhost:11434/api/tags`

### GitHub Actions can't reach tunnel
- Verify `OLLAMA_BASE_URL` secret is set: `gh secret list`
- Check tunnel URL is HTTPS (not HTTP)
- Ensure cloudflared process is still running

### Review using wrong model
- Check `.github/workflows/ai-pr-review.yml` for model name
- Verify model exists: `ollama list`
- Default is `deepseek-coder:6.7b` - change if needed

## Cost Comparison

| Provider | Cost per 1M tokens | PR Review Cost | Notes |
|----------|-------------------|----------------|-------|
| Gemini Flash 2.0 | $0.075 | ~$0.004 | Fast, cheap |
| OpenAI GPT-4o | $2.50 | ~$0.13 | Expensive |
| Anthropic Claude | $3.00 | ~$0.15 | Most expensive |
| **Local Ollama** | **$0.00** | **$0.00** | Free! |

Your GPU is already paid for - use it!

## Alternative: GitHub Copilot

If you prefer not to run a tunnel, you can use GitHub Copilot API (you mentioned having credits):
- Set as primary in workflow priority
- Be mindful of quota (you're at 25% for December)
- Configure workflow to skip on draft PRs and test commits

## Next Steps

1. Start tunnel: `cloudflared tunnel --url http://localhost:11434`
2. Copy URL and set secret: `gh secret set OLLAMA_BASE_URL --body "URL"`
3. Create a test PR to verify it works
4. Set up named tunnel for permanent solution (optional)
