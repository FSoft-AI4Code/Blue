# Blue CLI 🔵

A command-line-only Jarvis-like workspace-wise pair programming assistant, implemented using AutoGen for multi-agent orchestration with transparent decision-making processes to ensure reliable and traceable operations.

Blue CLI runs as a terminal-based tool that observes your developer workspace ecosystem, including local codebase changes and remote contexts like Google Docs/Drive, Jira tickets, GitHub Issues/PRs, and more. It provides strategic, big-picture guidance through a lightweight, in-memory workspace context graph that connects all your development contexts.

## Features

### 🧠 Strategic Navigation
- **Big-picture scope management** as a navigator, not a micromanager
- **Architecture alignment** and scalability implications
- **Maintainability insights** across your workspace graph
- **Goal coherence** tracking and blind spot identification
- **Empathetic, collaborative suggestions** that foster thoughtful development

### 🔄 Event-Driven Intelligence
- **Real-time file monitoring** using watchdog for .py/.js/etc. files
- **Dynamic decision algorithm** with human-like intervention timing
- **Context-aware scoring** based on change patterns and goal relevance
- **Adaptive thresholds** that learn from your feedback
- **Batch processing** to avoid notification fatigue

### 🌐 Workspace Integration
- **Multi-source context graph** connecting code, tickets, docs, and goals
- **Auto-parsing references** like "#JIRA-123" from code comments
- **Manual linking** of external resources
- **Intelligent traversals** for insights and blind spot detection
- **Persistent state** with JSON-based session management

### 🤖 Multi-Agent Architecture
- **Navigator Agent**: Strategic guidance and goal management (GPT-4 or Claude 3.5 Sonnet powered)
- **Observer Agent**: Event monitoring and remote context fetching
- **Tool Agents**: API calls, code analysis, and Git operations
- **Transparent dialogues** in verbose mode for debugging

### 🔧 AI Provider Support
- **OpenAI Integration**: GPT-4 for strategic thinking and goal decomposition
- **Anthropic Integration**: Claude 3.5 Sonnet for strategic analysis and insights
- **Runtime switching**: Change AI providers on-the-fly with `/ai-provider` command
- **Unified interface**: Same functionality regardless of provider choice

## Installation

### Prerequisites
- Python 3.10 or higher
- Git repository (for optimal functionality)
- OpenAI API key OR Anthropic API key for Navigator agent

### Setup

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd Blue
pip install -r requirements.txt
```

2. **Set up your AI API key (choose one):**

For OpenAI (GPT-4):
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

For Anthropic (Claude):
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

3. **Run Blue CLI:**
```bash
python main.py --dir /path/to/your/codebase
```

## Quick Start

### Basic Usage
```bash
# Start Blue CLI in your project directory
python main.py --dir /path/to/your/project

# Set a goal to begin
> /set-goal "implement user authentication system"

# Link external resources
> /link jira https://yourcompany.atlassian.net/browse/AUTH-123

# Ask for strategic guidance
> /ask "what are potential architectural concerns?"

# Switch AI provider (if you have both API keys)
> /ai-provider anthropic

# Check status and configuration
> /status
> /config
```

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/set-goal "goal"` | Set your current programming goal | `/set-goal "implement login function"` |
| `/link <type> <url>` | Link external resource | `/link jira https://company.atlassian.net/issue/KEY-123` |
| `/ask "question"` | Ask Navigator a question | `/ask "explain blind spot"` |
| `/status` | Show current status and progress | `/status` |
| `/quiet` | Toggle quiet mode (fewer interventions) | `/quiet` |
| `/verbose on/off` | Toggle verbose mode (show agent dialogues) | `/verbose on` |
| `/rate +/-` | Rate last suggestion for learning | `/rate +` |
| `/ai-provider <provider>` | Switch AI provider | `/ai-provider anthropic` |
| `/config` | Show configuration status | `/config` |
| `/help` | Show help message | `/help` |
| `/exit` | Exit Blue CLI | `/exit` |

## Configuration

Blue CLI uses a TOML configuration file located at `~/.config/blue-cli/config.toml` (or `~/blue-cli/config.toml` on Windows).

### Example Configuration
```toml
[api_keys]
openai = "your-openai-key"
anthropic = "your-anthropic-key"
jira = "your-jira-token"
github = "your-github-token"

[preferences]
verbose_mode = false
quiet_mode = false
intervention_threshold = 8
confidence_threshold = 70.0
buffer_size = 10
ai_provider = "anthropic"  # or "openai" (default: anthropic)

[integrations.jira]
enabled = true
base_url = "https://company.atlassian.net"
username = "your-email@company.com"

[integrations.github]
enabled = true
username = "your-github-username"
repositories = ["owner/repo1", "owner/repo2"]

[integrations.google_drive]
enabled = false
folder_ids = []

[security]
encrypt_sensitive_data = true
require_confirmation_for_api_calls = true
```

### Setting up Integrations

#### Jira Integration
```bash
# The CLI will prompt you for configuration
> /setup jira
```

#### GitHub Integration
```bash
# Generate a personal access token at github.com/settings/tokens
> /setup github
```

#### Google Drive Integration
```bash
# Follow Google Drive API setup instructions
> /setup gdrive
```

## How It Works

### Decision Algorithm
Blue CLI uses a sophisticated decision algorithm that mimics human navigation behavior:

1. **Event Accumulation**: Changes are buffered in a rolling window
2. **Pattern Scoring**: Events are scored based on structural changes, complexity, and goal relevance
3. **Threshold Evaluation**: Cumulative scores are compared against adaptive thresholds
4. **Contextual Analysis**: Graph state and external factors boost confidence
5. **Strategic Intervention**: Only intervenes when confidence exceeds threshold

### Workspace Graph
The in-memory graph connects:
- **Files** and their dependencies
- **Goals** and subtasks
- **External resources** (Jira, GitHub, Drive)
- **References** auto-parsed from code
- **Patterns** and architectural concerns

### Example Intervention
```
[15:32] Navigator: On your login goal: Observing emerging structure—graph flags 
tight coupling risking scalability per Confluence guidelines. Big pic: Decouple 
with interfaces? Preview idea: Abstract auth service. Your thoughts? [Y/N/Explain]
```

## Advanced Usage

### Verbose Mode
See internal agent dialogues and decision traces:
```bash
> /verbose on
```

### Quiet Mode
Reduce intervention frequency for focused work:
```bash
> /quiet
```

### Health Check
Monitor system health and diagnostics:
```bash
> /health
```

### Feedback Learning
Rate suggestions to improve the algorithm:
```bash
> /rate +    # Positive feedback
> /rate -    # Negative feedback
```

## Architecture

```
Blue CLI
├── main.py                 # Entry point and CLI orchestration
├── agents/
│   ├── navigator.py        # Strategic guidance (GPT-4)
│   ├── observer.py         # Event monitoring
│   └── tool_agents.py      # API calls, code analysis
├── core/
│   ├── workspace_graph.py  # Context graph management
│   └── decision_algorithm.py # Intervention logic
└── utils/
    ├── config_manager.py   # Configuration handling
    └── error_handler.py    # Error handling & fallbacks
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## Privacy & Security

- **Local-first**: Graph data stored locally in JSON format
- **Encrypted secrets**: API keys encrypted in configuration
- **Consent-based**: Prompts for permissions on first use
- **No telemetry**: No data sent to external services except configured integrations

## Troubleshooting

### Common Issues

**High memory usage:**
- Reduce `buffer_size` in configuration
- Use `/quiet` mode during intensive work

**Network connectivity issues:**
- Blue CLI automatically enters fallback mode
- Works offline with local graph data
- Check `/status` for connectivity status

**Too many/few interventions:**
- Adjust `intervention_threshold` in config
- Use `/rate +/-` to provide feedback
- Toggle `/quiet` mode as needed

### Debug Mode
```bash
python main.py --dir /path/to/project --verbose
```

### Health Check
```bash
> /health
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [AutoGen](https://github.com/microsoft/autogen) for multi-agent orchestration
- Uses [Watchdog](https://github.com/gorakhargosh/watchdog) for file monitoring
- Strategic guidance powered by OpenAI GPT-4

---

**Blue CLI** - Your strategic pair programming navigator 🔵