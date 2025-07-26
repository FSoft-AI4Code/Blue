# Anthropic API Format Fix

## ❌ The Problem

Anthropic's Messages API has a different format than OpenAI's Chat API:

```python
# ❌ WRONG (OpenAI format)
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"}
]

# This fails with Anthropic:
# Error: Unexpected role "system". The Messages API accepts 
# a top-level `system` parameter, not "system" as an input message role.
```

## ✅ The Solution

Anthropic requires system messages as a separate parameter:

```python
# ✅ CORRECT (Anthropic format)
system = "You are a helpful assistant"
messages = [
    {"role": "user", "content": "Hello"}
]

response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=system,  # ← System message as separate parameter
    messages=messages,
    max_tokens=300
)
```

## 🔧 Fixed Implementation

The `_make_ai_request` method now handles both formats:

```python
async def _make_ai_request(self, messages, temperature=0.7, max_tokens=300):
    if self.ai_provider == 'anthropic':
        # Extract system message for Anthropic
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg)
        
        # Build request with system as separate parameter
        request_params = {
            'model': self.model_config["model"],
            'messages': user_messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        if system_message:
            request_params['system'] = system_message
        
        response = await self.client.messages.create(**request_params)
        return response.content[0].text
    
    else:  # OpenAI format
        response = await self.client.chat.completions.create(
            model=self.model_config["model"],
            messages=messages,  # System message stays in messages
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
```

## 🎯 API Format Comparison

| Provider | System Message | User Messages | Response |
|----------|----------------|---------------|----------|
| **OpenAI** | In `messages` array with `role: "system"` | In `messages` array | `response.choices[0].message.content` |
| **Anthropic** | Separate `system` parameter | In `messages` array (no system role) | `response.content[0].text` |

## ✅ Now Working!

Try setting a goal again:

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run Blue CLI
uv run python main.py --dir /Users/quocnghi/codes/marvis-ai/Blue

# Set a goal (should work now!)
> /set-goal "implement user authentication system"
```

The error should be resolved and Blue CLI will now properly communicate with Anthropic's Claude API! 🎉