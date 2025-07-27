# Blue Configuration System

## Overview
The Blue configuration system uses **clean separation** with three focused TOML files:

1. **Core Settings**: `blue/config/default.toml` - Agent configs, limits, scoring
2. **System Prompts**: `blue/config/prompts.toml` - All LLM prompts (separate for easy editing)
3. **User Overrides**: `config/config.toml` - Your customizations only

## Configuration Hierarchy

```
1. Load blue/config/default.toml (core settings)
2. Load blue/config/prompts.toml (system prompts)
3. Merge config/config.toml (user overrides)
4. Ready to use!
```

## Key Features

### ✅ **Eliminated Redundancy**
- **Removed** hardcoded Python defaults (`_get_default_config()`)
- **Single source** for defaults: `blue/config/default.toml`
- **No more** scattered configuration values

### ✅ **Agent-Specific LLM Configuration**
Each agent can use different LLM providers/models for cost optimization:

```toml
[agents.navigator]
provider = "anthropic"
model = "claude-3-5-sonnet-20241022"  # Premium model for insights
max_tokens = 500

[agents.intervention]  
provider = "anthropic"
model = "claude-3-5-haiku-20241022"   # Faster model for decisions
max_tokens = 100
```

### ✅ **Clear Configuration Locations**
- `blue/config/default.toml` - **Core settings** (don't edit)
- `blue/config/prompts.toml` - **System prompts** (don't edit) 
- `config/config.toml` - **Your customizations** (edit freely)

### ✅ **Enhanced System Prompts**
System prompts are now in their own file with detailed, actionable guidance:
- **NavigatorAgent proactive**: Comprehensive guidelines for security analysis, architecture review, code quality assessment
- **NavigatorAgent interactive**: Expert coding assistant with context awareness  
- **InterventionAgent decision**: Smart timing decisions to avoid interruptions
- Explicitly forbids generic, token-wasting comments
- Focuses on providing specific, valuable insights that save developer time

## Usage Examples

### Most Users: Just Add API Keys
The `config/config.toml` should typically contain **only your API key**:
```toml
[llm_providers.anthropic]
api_key = "your-key-here"
```

### Advanced: Custom Agent Models
Only add sections you want to customize:
```toml
[llm_providers.anthropic]
api_key = "your-key-here"

# Use OpenAI for NavigatorAgent (cost optimization)
[agents.navigator]
provider = "openai"
model = "gpt-4o"

# Use cheaper model for quick decisions  
[agents.intervention]
provider = "openai"
model = "gpt-4o-mini"
```

### Pure Defaults
Simply delete `config/config.toml` entirely - everything will use defaults with environment variables for API keys.

## Migration Notes

- **Old hardcoded defaults**: Removed ❌
- **Multiple config files**: Eliminated ❌  
- **Single default source**: `blue/config/default.toml` ✅
- **Clean merging**: User config merges over defaults ✅

The system now has **zero redundancy** and a clear, predictable configuration hierarchy!