# Anthropic Claude Integration for Blue CLI

## Overview

Blue CLI now supports both OpenAI's GPT-4 and Anthropic's Claude 3.5 Sonnet as AI providers for the Navigator Agent. You can seamlessly switch between providers during runtime without losing your session state.

## Features Added

### 🔧 Dual AI Provider Support
- **OpenAI GPT-4**: Original provider for strategic thinking and goal decomposition
- **Anthropic Claude 3.5 Sonnet**: New provider with advanced reasoning capabilities
- **Runtime switching**: Change providers on-the-fly with the `/ai-provider` command
- **Unified API**: Same functionality regardless of which provider you choose

### 🚀 New Commands
- `/ai-provider <provider>` - Switch between 'openai' and 'anthropic'
- `/config` - Show detailed configuration status including active AI provider

## Setup

### 1. Install Anthropic Dependency
```bash
pip install anthropic>=0.7.0
```

### 2. Set Up API Keys

You can use either provider (or both):

**For OpenAI:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**For Anthropic:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Configure Default Provider (Optional)

In your `~/.config/blue-cli/config.toml`:
```toml
[preferences]
ai_provider = "anthropic"  # or "openai"
```

## Usage

### Switching Providers During Runtime

```bash
# Check current provider
> /ai-provider

# Switch to Anthropic Claude
> /ai-provider anthropic
✓ Switched to Anthropic AI provider
✓ Navigator agent reinitialized with new provider

# Switch to OpenAI GPT-4
> /ai-provider openai
✓ Switched to OpenAI AI provider
✓ Navigator agent reinitialized with new provider
```

### Configuration Status

```bash
> /config
=== Blue CLI Configuration Status ===

API Keys:
  Openai (Inactive): ✓ Configured
  Anthropic (Active AI Provider): ✓ Configured
  Jira: ✗ Not set
  Github: ✓ Configured
  Google: ✗ Not set
```

## Provider Comparison

| Feature | OpenAI GPT-4 | Anthropic Claude 3.5 Sonnet |
|---------|--------------|------------------------------|
| Strategic Analysis | ✅ Excellent | ✅ Excellent |
| Code Understanding | ✅ Very Good | ✅ Excellent |
| Architectural Insights | ✅ Strong | ✅ Very Strong |
| Context Window | 8K tokens | 200K tokens |
| Rate Limits | Standard | Generous |
| Cost | $$ | $ |

## Technical Implementation

### Unified API Layer
The Navigator Agent now includes a `_make_ai_request()` method that abstracts away provider differences:

```python
async def _make_ai_request(self, messages, temperature=0.7, max_tokens=300):
    """Make a request to the configured AI provider."""
    if self.ai_provider == 'anthropic':
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.content[0].text
    else:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
```

### Configuration Management
- Provider preference stored in config TOML
- API key validation for active provider
- Automatic fallback to available provider if preferred isn't configured

## Migration Guide

### From OpenAI-only to Dual Provider

1. **Update dependencies:**
   ```bash
   pip install anthropic>=0.7.0
   ```

2. **Add Anthropic API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   ```

3. **Optional: Set as default provider:**
   ```toml
   [preferences]
   ai_provider = "anthropic"
   ```

4. **Switch during runtime:**
   ```bash
   > /ai-provider anthropic
   ```

### Existing Sessions
- All existing workspace graphs, goals, and history are preserved when switching providers
- Decision algorithm parameters remain unchanged
- No interruption to file watching or external integrations

## Benefits

### For Users
- **Choice**: Pick the AI provider that works best for your use case
- **Flexibility**: Switch providers based on task requirements
- **Cost optimization**: Use more cost-effective providers when appropriate
- **Reliability**: Fallback options if one provider has issues

### For Developers
- **Extensible**: Easy to add new AI providers in the future
- **Maintainable**: Single codebase supports multiple providers
- **Testable**: Each provider can be tested independently

## Troubleshooting

### Common Issues

**1. API Key Not Found**
```bash
> /ai-provider anthropic
❌ Anthropic API key not configured
```
**Solution:** Set the `ANTHROPIC_API_KEY` environment variable

**2. Invalid Provider**
```bash
> /ai-provider claude
❌ Invalid provider. Use 'openai' or 'anthropic'
```
**Solution:** Use exact provider names: 'openai' or 'anthropic'

**3. Provider Switch Failed**
- Check API key is valid and has sufficient credits
- Verify network connectivity
- Check `/config` for configuration status

## Future Enhancements

- **Auto-selection**: Automatically choose provider based on task type
- **Load balancing**: Distribute requests across multiple providers
- **Provider-specific tuning**: Different parameters for different providers
- **Cost tracking**: Monitor usage and costs across providers

---

The dual provider support makes Blue CLI more flexible and accessible, allowing you to leverage the strengths of both OpenAI and Anthropic's AI models for your strategic pair programming needs.