# Blue - Ambient Intelligence for Developers

> *"The best pair programmer is one who's always there, never intrusive, and speaks up exactly when you need them to."*

## Rethinking Developer-AI Interaction

Traditional AI coding assistants operate on a **request-response paradigm** - you ask, they answer. Blue represents a fundamental shift toward **ambient intelligence** - an AI system that understands your development context continuously and provides insights proactively, like an experienced colleague working alongside you.

### The Ambient Coding Paradigm

**Traditional Approach:**
- Interrupt your flow to ask questions
- Context switching between coding and prompting
- Static, one-off interactions
- You drive all conversations

**Ambient Approach:**
- AI observes your work patterns naturally
- Insights emerge from your actual coding behavior  
- Continuous contextual awareness
- AI initiates conversations when valuable
- Maintains development flow state

### Core Principles

1. **Non-Intrusive Observation**: Blue watches your codebase changes without interrupting your creative process
2. **Contextual Intelligence**: Understanding emerges from accumulated observations, not isolated questions
3. **Proactive Guidance**: The system speaks up when it recognizes patterns worth discussing
4. **Conversational Continuity**: Maintains ongoing dialogue that builds on previous interactions
5. **Flow Preservation**: Designed to enhance, not break, your development rhythm

## Why Ambient Intelligence Matters

Modern software development involves complex mental models, architectural decisions, and pattern recognition that unfold over hours or days, not single interactions. Blue captures this temporal dimension by:

- **Learning your coding patterns** as they evolve across sessions
- **Recognizing architectural decisions** in the context of your broader codebase
- **Identifying emerging problems** before they become technical debt
- **Suggesting optimizations** based on observed usage patterns
- **Facilitating knowledge transfer** through contextual explanations

## Architecture: Multi-Agent Ambient System

Blue implements a **multi-agent architecture** designed for continuous operation:

### Observer Agent
- **Event-driven file monitoring** using filesystem watchers
- **Semantic change detection** (not just file diffs)
- **Pattern recognition** for architectural changes
- **Context accumulation** across development sessions

### Navigator Agent  
- **Large Language Model integration** (Anthropic Claude, OpenAI GPT)
- **Conversational state management** 
- **Proactive insight generation**
- **Interactive dialogue handling**

### Coordinator System
- **Agent orchestration** and communication
- **Real-time stream processing**
- **Session state persistence**
- **Graceful error handling**

## Quick Start

### Prerequisites
- Python 3.7+
- API key from either Anthropic or OpenAI
- Read access to your development directories

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Blue

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Blue supports both **Anthropic Claude** and **OpenAI GPT** models through TOML configuration files:

#### Option 1: Environment Variables (Quick Setup)
```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="your_anthropic_key_here"

# For OpenAI GPT  
export OPENAI_API_KEY="your_openai_key_here"
```

#### Option 2: TOML Configuration (Recommended)
Edit the configuration files to customize behavior:

**anthropic_config.toml:**
```toml
[anthropic]
api_key = "your_anthropic_key_here"
model = "claude-3-5-sonnet-20241022"
max_tokens = 200
temperature = 0.7
```

**openai_config.toml:**
```toml
[openai]  
api_key = "your_openai_key_here"
model = "gpt-4o"
max_tokens = 200
temperature = 0.7
base_url = "https://api.openai.com/v1"  # Optional: for custom endpoints
```

### Usage

**Basic Usage:**
```bash
# Default: Anthropic Claude
python blue.py --dir /path/to/your/codebase

# Specify OpenAI GPT
python blue.py --dir /path/to/your/codebase --provider openai
```

**Real-world Examples:**
```bash
# Monitor a React/TypeScript project
python blue.py --dir ~/projects/my-react-app --provider anthropic

# Monitor a Python microservice
python blue.py --dir ~/backend/user-service --provider openai

# Monitor current directory with Claude
python blue.py --dir . 
```

## The Ambient Experience in Action

### Continuous Code Intelligence

Blue operates through **three complementary modes** that work simultaneously:

#### 1. **Passive Observation**
- **Semantic file monitoring** across 15+ programming languages
- **Change pattern recognition** (architectural shifts, refactoring, new features)
- **Context accumulation** building understanding over time
- **Non-intrusive background processing**

**Supported Languages:**
```
Python • JavaScript/TypeScript • Java • C/C++ • Go • Rust 
C# • PHP • Ruby • Swift • Kotlin • Scala • HTML/CSS • SQL
```

#### 2. **Proactive Insights**
When Blue detects significant patterns, it proactively shares observations:

- **Architectural implications** of your changes
- **Potential security or performance concerns**
- **Code quality suggestions** based on emerging patterns
- **Refactoring opportunities** as complexity grows
- **Best practice reminders** contextual to your current work

#### 3. **Interactive Dialogue**
Natural conversation during development:

```bash
> I'm trying to decide between using a factory pattern or dependency injection here

🤖 Given the auth refactoring I've been observing, dependency injection would give you 
better testability. I noticed you're already injecting the database layer in user_service.py - 
keeping that pattern consistent would make the codebase more maintainable.

> Good point. What about performance implications?

🤖 For your current scale, the overhead is negligible. The bigger win is the decoupling 
you'll get, especially since I see you're planning to extract that payment logic into 
a separate service based on your recent file structure changes.
```

## Sample Session: Building a Authentication System

```bash
$ python blue.py --dir ~/my-microservice --provider anthropic

[09:15:22] Blue - Ambient Intelligence for Developers
[09:15:22] 🔍 Observer Agent initialized
[09:15:22] 🧠 Navigator Agent initialized with ANTHROPIC  
[09:15:22] 📁 Monitoring: ~/my-microservice
[09:15:22] ✨ Blue CLI is now active. Type your thoughts or questions:

# You start working on authentication...

[09:18:45] 📝 auth/models.py created: +67 lines, new functions: User, hash_password, verify_password
[09:18:48] 🤖 Nice start on the User model! I see you're using proper password hashing - that's 
critical for security. Consider adding password complexity validation and rate limiting for login attempts.

[09:22:15] 📝 auth/jwt_utils.py created: +34 lines, new functions: generate_token, verify_token  
[09:22:18] 🤖 JWT implementation looks solid. I notice you're using HS256 - for production, 
consider RS256 for better key rotation. Also, you might want configurable token expiration.

> I'm debating between Redis and database sessions for token storage. What do you think?

[09:23:01] 🤖 Based on your current architecture, I'd lean toward Redis. You're building 
what looks like a stateless microservice, and Redis gives you built-in expiration and 
better performance for session lookups. Plus it scales horizontally more easily.

[09:28:33] 📝 auth/middleware.py modified: +23 lines, new functions: authenticate_request
[09:28:36] 🤖 Smart middleware pattern! This'll work well with your Flask setup. One thing - 
consider extracting the token parsing logic into a separate utility so you can reuse it 
in other services if you're going microservices.

> Actually, I'm planning to extract this whole auth module into a shared library

[09:29:12] 🤖 Perfect timing! That'll make your auth consistent across services. When you 
extract it, consider making the JWT configuration injectable so different services can 
have different token lifetimes if needed.

[09:35:47] 📝 tests/test_auth.py created: +89 lines, new functions: test_password_hashing, test_jwt_flow
[09:35:50] 🤖 Excellent - testing first! I see you're covering the happy path and edge cases. 
You might also want to test token expiration and invalid signature scenarios.

> quit
[09:40:15] 🔴 Blue CLI stopped. Happy coding!
```

## Project Architecture

```
Blue/
├── 🚀 Core System
│   ├── blue.py                 # CLI entry point & argument parsing
│   ├── blue_cli.py             # Multi-agent coordinator & session management  
│   ├── observer_agent.py       # Filesystem monitoring & change detection
│   └── navigator_agent.py      # LLM integration & conversation management
│
├── ⚙️  Configuration  
│   ├── anthropic_config.toml   # Claude model settings & prompts
│   ├── openai_config.toml      # GPT model settings & prompts
│   └── requirements.txt        # Python dependencies
│
├── 📁 Generated (Runtime)
│   ├── .blue_session/          # Session state & conversation history
│   └── .blue_cache/            # File change cache & patterns
│
└── 📖 Documentation
    └── README.md               # This file
```

## Advanced Configuration

### Custom System Prompts

Modify the TOML configuration files to customize Blue's personality and expertise:

```toml
[anthropic.system_prompts]
proactive = """You are an expert software architect observing code changes...
Focus on: security, performance, maintainability, and emerging patterns."""

interactive = """You are a senior developer mentor having a real-time conversation...
Be encouraging, specific, and help with architectural decisions."""
```

### Performance Tuning

```toml
[anthropic.limits]
max_conversation_history = 10      # Conversation context window
max_recent_changes = 8             # File changes to analyze
```

### Provider-Specific Settings

**Anthropic Claude:**
```toml
[anthropic]
model = "claude-3-5-sonnet-20241022"    # Latest Claude model
max_tokens = 300                        # Longer responses
temperature = 0.6                       # More focused outputs
```

**OpenAI GPT:**
```toml
[openai]
model = "gpt-4o"                        # GPT-4 Optimized
base_url = "https://api.openai.com/v1"  # Custom endpoint support
```

## Troubleshooting & Optimization

### Common Issues

#### **API Configuration**
```bash
# Issue: "API key not found"
# Solution: Check both config file and environment variables

# Verify configuration
cat anthropic_config.toml  # Check if api_key is set
echo $ANTHROPIC_API_KEY    # Check environment variable

# Test API connectivity
python -c "import anthropic; print(anthropic.Anthropic(api_key='your_key').models.list())"
```

#### **File Monitoring**
```bash
# Issue: Changes not detected
# Solution: Verify file types and permissions

# Check supported extensions (in observer_agent.py)
grep -n "supported_extensions" observer_agent.py

# Verify directory permissions  
ls -la /path/to/your/codebase
```

#### **Performance Issues**
```bash  
# Issue: High CPU usage on large repositories
# Solution: Optimize monitoring scope

# Monitor specific subdirectories
python blue.py --dir ./src --provider anthropic

<<<<<<< HEAD
# Exclude large directories by modifying observer_agent.py ignore patterns
```

### Production Deployment

For teams wanting to deploy Blue as a shared development tool:

#### **Docker Container**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "blue.py"]
```

#### **Team Configuration**
```toml
# shared_config.toml
[anthropic]
model = "claude-3-5-sonnet-20241022"
max_tokens = 150                    # Shorter for team usage
temperature = 0.5                   # More consistent responses

[anthropic.system_prompts]
proactive = """You are a team code reviewer focused on:
- Security vulnerabilities
- Performance bottlenecks  
- Code style consistency
- Architecture decisions that affect team velocity"""
```

## Extending Blue

### Custom Agents

The multi-agent architecture supports domain-specific agents:

```python
class SecurityAgent:
    def analyze_change(self, file_content, change_type):
        # Custom security analysis logic
        if self.detect_sql_injection_risk(file_content):
            return "⚠️  Potential SQL injection risk detected"
        return None

# Register in blue_cli.py
self.security_agent = SecurityAgent()
```

### Integration Hooks

Blue can integrate with existing development workflows:

```python
# Git hooks integration
def on_commit_hook(commit_info):
    blue_session = BlueCLI(".", provider="anthropic")
    analysis = blue_session.analyze_commit(commit_info)
    return analysis

# CI/CD pipeline integration  
def ci_code_review(changed_files):
    return BlueCLI.batch_analyze(changed_files, provider="openai")
```

### Plugin Architecture

```python
# Custom plugin example: performance_monitor.py
class PerformanceMonitorPlugin:
    def on_file_change(self, file_path, change_details):
        if self.is_performance_critical(file_path):
            return self.analyze_performance_impact(change_details)
```

## The Future of Ambient Development

Blue represents the first step toward **truly ambient development environments** where:

- **AI understands your codebase** as deeply as you do
- **Insights emerge naturally** from your development patterns  
- **Knowledge compounds** across sessions and team members
- **Development flow** remains uninterrupted by AI assistance

As models improve and context windows expand, ambient agents will become indispensable partners in software creation, helping developers navigate complexity while maintaining creative control.

---

## Technical Specifications

**Supported Models:**
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- OpenAI: GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo

**System Requirements:**
- Python 3.7+ (3.9+ recommended)
- 50MB disk space
- Network access for LLM APIs
- Read permissions on target directories

**Performance:**
- ~1-5ms file change detection latency
- ~200-500ms LLM response time (model dependent)
- <10MB memory footprint for typical sessions

**Security:**
- API keys encrypted in transit (HTTPS)
- No code content stored remotely
- Local session data only

---

*Built with ❤️ for developers who believe AI should enhance, not interrupt, the creative process of coding.*
=======
This project is for educational and development purposes. Please respect API usage guidelines and rate limits.
>>>>>>> 5e40b60d0fba67e73a2fa5d53258620aee5e0e28
