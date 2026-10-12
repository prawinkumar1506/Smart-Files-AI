# LLM Providers Guide

SmartFile AI now supports multiple LLM providers, giving you flexibility to choose the best AI service for your needs!

## Supported Providers

### 1. **Google Gemini** (Cloud)
- **Display Name**: Google Gemini (Cloud)
- **API Key Required**: Yes
- **Get API Key**: https://ai.google.dev/
- **Default Model**: gemini-2.5-flash
- **Available Models**: gemini-2.5-flash, gemini-pro
- **Best For**: Fast, high-quality responses with generous free tier

### 2. **OpenRouter** (Cloud - Multi-Model)
- **Display Name**: OpenRouter (Multi-Model)
- **API Key Required**: Yes
- **Get API Key**: https://openrouter.ai/
- **Default Model**: meta-llama/llama-3-70b-instruct
- **Available Models**: Multiple (Claude, GPT-4, Llama, and more)
- **Best For**: Access to multiple models through a single API

### 3. **Groq** (Cloud - Fast Inference)
- **Display Name**: Groq (Fast Inference)
- **API Key Required**: Yes
- **Get API Key**: https://console.groq.com/
- **Default Model**: mixtral-8x7b-32768
- **Available Models**: mixtral-8x7b-32768, llama2-70b-4096
- **Best For**: Ultra-fast inference speeds

### 4. **OpenAI** (Cloud)
- **Display Name**: OpenAI (GPT Models)
- **API Key Required**: Yes
- **Get API Key**: https://platform.openai.com/
- **Default Model**: gpt-3.5-turbo
- **Available Models**: gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Best For**: Industry-standard GPT models

### 5. **Anthropic Claude** (Cloud)
- **Display Name**: Anthropic Claude (Advanced AI)
- **API Key Required**: Yes
- **Get API Key**: https://console.anthropic.com/
- **Default Model**: claude-3-sonnet-20240229
- **Available Models**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Best For**: High-quality reasoning and longer context

### 6. **Ollama** (Local)
- **Display Name**: Ollama (Local LLM)
- **API Key Required**: No
- **Installation**: https://ollama.ai/
- **Default Model**: tinyllama:latest
- **Available Models**: llama2, mistral, neural-chat, and more
- **Best For**: Complete privacy, no internet required

## How to Configure

### Via Settings UI

1. Open **Settings** from the sidebar
2. Navigate to **LLM Configuration** section
3. Select your desired provider from the dropdown
4. Enter your API key (if required)
5. Choose a model (optional)
6. Click **Save Settings**

### Via Environment Variables

You can also configure providers using environment variables in your `.env` file:

```bash
# Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=mixtral-8x7b-32768

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
```

### Via Configuration File

API keys are stored in `~/.smartfile_ai_config.json`:

```json
{
  "llm_provider": "gemini",
  "gemini_api_key": "your_api_key_here",
  "gemini_model": "gemini-2.5-flash",
  "openrouter_api_key": "your_openrouter_key",
  "groq_api_key": "your_groq_key",
  "openai_api_key": "your_openai_key",
  "anthropic_api_key": "your_anthropic_key"
}
```

## System Requirements Check

The Settings page now includes a **System Status** section that checks:

- ✅ **Python Version**: Verifies Python 3.8+
- ✅ **RAM**: Checks available memory (recommends 8+ GB)
- ✅ **Disk Space**: Ensures sufficient storage (requires 2+ GB)
- ✅ **SQLite**: Verifies database availability
- ✅ **NumPy**: Checks embedding dependencies
- ✅ **Internet Connectivity**: Tests connection for cloud providers
- ✅ **Ollama Status**: Detects if local Ollama is running

## Choosing the Right Provider

### For Privacy-Conscious Users
→ **Ollama** - Runs completely offline on your machine

### For Best Free Tier
→ **Gemini** or **Groq** - Generous free quotas

### For Production Use
→ **OpenAI** or **Anthropic Claude** - Industry-standard reliability

### For Model Variety
→ **OpenRouter** - Access to multiple models through one API

### For Speed
→ **Groq** - Ultra-fast inference

## API Costs Comparison

| Provider | Free Tier | Pay-as-you-go |
|----------|-----------|---------------|
| Gemini | 60 requests/minute | $0.50/$1.50 per 1M tokens |
| OpenRouter | Varies by model | Starts at $0.10 per 1M tokens |
| Groq | Limited free tier | Competitive pricing |
| OpenAI | $5 credit | $0.50-$30 per 1M tokens |
| Claude | Limited credit | $3-$15 per 1M tokens |
| Ollama | Unlimited (local) | Free (uses your hardware) |

## Troubleshooting

### "API key not configured" error
- Ensure you've entered the API key in Settings
- Check that the key is valid
- Verify internet connectivity for cloud providers

### Ollama not detected
- Install Ollama from https://ollama.ai/
- Run `ollama serve` to start the service
- Verify it's running at http://localhost:11434

### System requirements not met
- Check the System Status section in Settings
- Install missing dependencies: `pip install -r requirements.txt`
- Ensure you have sufficient RAM and disk space

## Migration from Previous Versions

If you were using the old Gemini-only configuration:

1. Your existing Gemini API key will be automatically migrated
2. You can now add API keys for other providers
3. Switch providers anytime from the Settings page
4. Your chat history and indexed files remain unchanged

## Advanced Configuration

### Custom Models

You can specify custom models by setting environment variables:

```bash
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
GROQ_MODEL=llama2-70b-4096
```

### Multiple Configurations

You can save configurations for all providers and switch between them easily. The application remembers your last selection.

### Programmatic Configuration

For advanced users, you can configure providers programmatically via the API:

```bash
# Save configuration
curl -X POST http://localhost:8000/api/settings/api-key \
  -H "Content-Type: application/json" \
  -d '{"provider": "gemini", "api_key": "your_key", "model": "gemini-2.5-flash"}'

# Get providers list
curl http://localhost:8000/api/settings/providers

# Check system requirements
curl http://localhost:8000/api/settings/system-requirements
```

## Support

For issues or questions about LLM providers:
- Check the System Status section in Settings
- Review provider-specific documentation
- Ensure your API keys have sufficient quota
- Test with a different provider to isolate issues

---

**Note**: Keep your API keys secure and never commit them to version control!
