# Local LLM Setup Guide

Detailed instructions for setting up Ollama or LM Studio for unlimited local inference.

## Why Local LLM?

- **Unlimited Usage**: No API quotas or rate limits
- **Privacy**: Your code never leaves your machine
- **Speed**: Low latency for iterative tasks
- **Cost**: Free after initial GPU investment

## Option 1: Ollama (Recommended)

### Installation

**Windows:**
1. Download from <https://ollama.ai/download>
2. Run installer
3. Ollama starts automatically

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

### Pull Models

Choose based on your GPU VRAM:

```bash
# 4-6 GB VRAM
ollama pull llama3.2:3b

# 8 GB VRAM
ollama pull qwen2.5:14b-instruct-q4_K_M

# 12 GB VRAM (Desktop 4070 Ti)
ollama pull qwen2.5:32b-instruct-q4_K_M  # Best quality with offloading
ollama pull qwen2.5:14b-instruct-q4_K_M  # Faster, fully in VRAM

# 16-24 GB VRAM
ollama pull qwen2.5:32b-instruct-q4_K_M
```

### Verify Installation

```bash
# List installed models
ollama list

# Check running models
ollama ps

# Test API
curl http://localhost:11434/api/tags
```

### GPU Offloading

Ollama automatically uses your GPU. For large models on smaller VRAM:

```bash
# Set GPU layers (adjust based on VRAM)
# Model will use GPU + CPU RAM
OLLAMA_NUM_GPU_LAYERS=32 ollama run qwen2.5:32b-instruct-q4_K_M
```

## Option 2: LM Studio

### Installation

1. Download from <https://lmstudio.ai>
2. Install and launch
3. Go to "Discover" tab
4. Search and download a model:
   - **qwen2.5** (recommended)
   - **llama3.2**
   - **mistral**

### Start Server

1. Click "Local Server" tab
2. Select your downloaded model
3. Click "Start Server"
4. Default port: 1234

### Configuration

**In LM Studio Settings:**
- Enable GPU acceleration
- Set context length (2048-8192)
- Adjust temperature (0.7 default)

## Model Recommendations

### GPU Requirements Table

| GPU VRAM | Recommended Model               | Use Case                 |
| -------- | ------------------------------- | ------------------------ |
| 4-6 GB   | llama3.2:3b, qwen2.5:7b-q4      | Basic coding tasks       |
| 8 GB     | qwen2.5:14b-q4                  | Most development tasks   |
| 12 GB    | qwen2.5:32b-q4                  | Complex reasoning        |
| 16-24 GB | qwen2.5:32b-q4, llama3.1:70b-q4 | Production-grade quality |

### Your Hardware

- **Desktop: NVIDIA 4070 Ti (12GB)**
  - Best: `qwen2.5:32b-q4` with GPU offloading
  - Fastest: `qwen2.5:14b-q4` fully in VRAM

- **Laptop: NVIDIA 4070 (8GB)**
  - Best: `qwen2.5:14b-q4`
  - Fallback: `llama3.2:3b` for speed

## Integration with Job Lead Finder

### Update .env

**For Ollama (default port 11434):**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

**For LM Studio (default port 1234):**
```bash
OLLAMA_BASE_URL=http://localhost:1234
```

### Test Connection

```bash
# From project directory
python tools/llm_api.py --prompt "What is the capital of France?" --provider local
```

Expected output:
```
The capital of France is Paris.
```

## Performance Tuning

### Ollama Configuration

Create `~/.ollama/config.json`:

```json
{
  "num_gpu": 1,
  "num_thread": 8,
  "num_ctx": 4096
}
```

### LM Studio Settings

- **Context Length**: 4096 (balance speed/quality)
- **Temperature**: 0.7 (0.0 = deterministic, 1.0 = creative)
- **GPU Layers**: Max (use all available VRAM)

## Troubleshooting

### Ollama Issues

**"Connection refused":**
```bash
# Start Ollama service
# Windows: Restart Ollama app
# Linux: ollama serve
# Mac: brew services restart ollama
```

**"Model not found":**
```bash
# List available models
ollama list

# Pull the model
ollama pull qwen2.5:14b-instruct-q4_K_M
```

**GPU not detected:**
```bash
# Check NVIDIA drivers
nvidia-smi

# Update drivers if needed
# Windows: GeForce Experience
# Linux: nvidia-driver-xxx package
```

### LM Studio Issues

**Server won't start:**
- Check if port 1234 is available
- Try different port in settings
- Restart LM Studio

**Poor performance:**
- Enable GPU acceleration in settings
- Reduce context length
- Use smaller model

**Out of memory:**
- Reduce max context length
- Use quantized model (q4 instead of fp16)
- Close other GPU applications

## Model Management

### Ollama

```bash
# List all models
ollama list

# Remove unused model
ollama rm llama3.2:3b

# Update model
ollama pull qwen2.5:14b-instruct-q4_K_M
```

### LM Studio

- Models stored in: `~/.cache/lm-studio/models/`
- Delete unused models to save disk space
- Download new models from "Discover" tab

## Best Practices

1. **Start small**: Test with 3b or 7b model first
2. **Monitor VRAM**: Use `nvidia-smi` or Task Manager
3. **Batch processing**: Use local LLM for repetitive tasks
4. **Save prompts**: Reuse effective prompts in scripts
5. **Compare outputs**: Test same prompt with different models

## Integration with Parallel Work Strategy

Use local LLM for:
- ✅ Code analysis (unlimited)
- ✅ Pattern detection
- ✅ Refactoring suggestions
- ✅ Test generation
- ✅ Documentation formatting

Reserve Copilot/Gemini for:
- Complex implementation
- Code review
- Architecture decisions

## Next Steps

1. Install Ollama or LM Studio
2. Pull recommended model for your GPU
3. Test with `tools/llm_api.py`
4. Configure in `.env`
5. Start using in parallel work (see `PARALLEL_WORK_STRATEGY.md`)

## References

- Ollama: <https://ollama.ai/library>
- LM Studio: <https://lmstudio.ai>
- Model Hub: <https://huggingface.co/models>
