# Ollama Setup Guide

JobFlow now supports **Ollama** for local AI-powered job matching, eliminating API quota limits!

## Why Ollama?

- **No API quotas** - Run unlimited job evaluations locally
- **Privacy** - Your resume never leaves your machine
- **Fast inference** - 2-5 seconds per job with your RTX 4070 Ti (12GB VRAM)
- **Free** - No API costs

## Quick Start

### 1. Install Ollama

Download and install from: https://ollama.ai

**Windows**: Download the installer and run it. Ollama will start automatically.

### 2. Pull a Model

Choose based on your VRAM preference:

```powershell
# Fast & lightweight (2GB VRAM) - Recommended to start
ollama pull llama3.2:3b

# Better quality (4GB VRAM)
ollama pull qwen2.5:7b

# Best balance (5GB VRAM)
ollama pull llama3.1:8b
```

**Your RTX 4070 Ti (12GB VRAM) can run all of these comfortably!**

### 3. Verify Installation

```powershell
ollama list  # Should show your pulled model
```

### 4. Start Using JobFlow

JobFlow will **automatically** use Ollama if available:

```powershell
docker compose up
```

Open http://localhost:8080 and start searching. Your jobs will be evaluated using the local Ollama model!

## Provider Priority

JobFlow automatically selects the best available provider:

1. **Ollama** (local, unlimited) - Used if model is pulled
2. **Gemini** (API, quota limited) - Fallback if Ollama unavailable
3. **None** (no scoring) - Graceful degradation if both unavailable

## Configuration

### Change Ollama Model

Set environment variable in `.env`:

```env
OLLAMA_MODEL=qwen2.5:7b  # Default: llama3.2:3b
```

### Change Ollama URL

If running Ollama on a different machine:

```env
OLLAMA_BASE_URL=http://192.168.1.100:11434  # Default: http://localhost:11434
```

## Model Recommendations

| Model       | VRAM | Speed    | Quality | Use Case                         |
| ----------- | ---- | -------- | ------- | -------------------------------- |
| llama3.2:3b | 2GB  | ⚡ Fast   | ⭐⭐⭐     | Quick searches, testing          |
| qwen2.5:7b  | 4GB  | 🚀 Medium | ⭐⭐⭐⭐    | Best quality/speed balance       |
| llama3.1:8b | 5GB  | 🐢 Slower | ⭐⭐⭐⭐⭐   | Best quality, detailed reasoning |

## Troubleshooting

### "Ollama not available" in logs

**Check if Ollama is running:**

```powershell
ollama list
```

**Pull a model if none installed:**

```powershell
ollama pull llama3.2:3b
```

### Slow inference

- Try a smaller model (`llama3.2:3b`)
- Check GPU utilization: Task Manager → Performance → GPU
- Ensure no other apps using GPU heavily

### "Connection refused" error

**Check Ollama service:**

```powershell
# Windows - check if Ollama service is running
Get-Service ollama
```

**Restart Ollama:**

Close Ollama from system tray and restart it.

## Performance Tips

1. **Use batch evaluation** - JobFlow automatically batches jobs for faster processing
2. **Smaller models** - `llama3.2:3b` is 3-5x faster than `llama3.1:8b`
3. **Keep Ollama running** - First request after start takes longer (model loading)

## Switching Back to Gemini

To temporarily use Gemini instead of Ollama:

1. Stop Ollama service
2. Ensure `GEMINI_API_KEY` is set in `.env`
3. Restart JobFlow

JobFlow will auto-fallback to Gemini.

## FAQ

**Q: Can I use both Ollama and Gemini?**
A: Yes! JobFlow tries Ollama first, falls back to Gemini if unavailable.

**Q: Which model should I use?**
A: Start with `llama3.2:3b`. If you want better quality and don't mind slower speed, try `qwen2.5:7b`.

**Q: Does this work with LM Studio?**
A: Not yet, but you can add an `LMStudioProvider` following the same pattern as `OllamaProvider`.

**Q: How much slower is local inference?**
A: Ollama (local): ~2-5s/job. Gemini (API): ~1-2s/job. Worth it for unlimited usage!

## Next Steps

- **Test the integration**: Run a search and check logs for "Using Ollama provider"
- **Try different models**: Compare quality of `llama3.2:3b` vs `qwen2.5:7b`
- **Optimize prompts**: Edit `ollama_provider.py` to tune evaluation prompt
- **Add UI controls**: Display active provider in settings modal

Enjoy unlimited, private job matching! 🚀
