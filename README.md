# Blue CLI - Ambient Pair Programming Assistant

Blue CLI is a Jarvis-like command-line application that acts as an ambient pair programming assistant. It monitors your codebase in real-time and provides proactive, conversational feedback about your code changes.

## Features

- **Real-time File Monitoring**: Watches your codebase for changes using efficient event-driven monitoring
- **Intelligent Change Detection**: Recognizes meaningful code changes like new functions, significant line additions, etc.
- **Conversational Interface**: Natural, bidirectional communication that feels like pair programming
- **Color-Coded Output**: Easy-to-read terminal output with timestamps and color coding
- **Multi-Agent Architecture**: Observer Agent for monitoring, Navigator Agent for reasoning

## Installation

1. **Clone or download** the Blue CLI files to your local machine.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**:
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_actual_api_key_here
     ```

## Usage

Run Blue CLI by pointing it to a directory you want to monitor:

```bash
python blue.py --dir /path/to/your/codebase
```

### Example Usage

```bash
# Monitor a Python project
python blue.py --dir ~/my-python-project

# Monitor a JavaScript project  
python blue.py --dir ~/my-react-app

# Monitor the current directory
python blue.py --dir .
```

## How It Works

### 1. File Monitoring
Blue CLI automatically monitors these file types:
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`)
- Go (`.go`)
- Rust (`.rs`)
- And more...

### 2. Change Detection
The system detects and displays:
- File modifications, creations, and deletions
- Line count changes
- New function additions
- Meaningful code patterns

### 3. AI Feedback
When significant changes are detected, the AI assistant provides:
- Architecture suggestions
- Code quality observations
- Security considerations
- Performance tips
- General programming advice

### 4. Interactive Mode
While monitoring, you can:
- Type questions or comments at the `>` prompt
- Get conversational responses from the AI
- Discuss your code changes in real-time
- Type `quit` or `exit` to stop monitoring

## Sample Output

```
[14:30:15] Blue CLI initialized for directory: /Users/dev/my-project
[14:30:15] Observer Agent initialized
[14:30:15] Navigator Agent initialized
[14:30:15] Starting file monitoring...
[14:30:15] File monitoring started for: /Users/dev/my-project

[14:32:41] ~ File auth.py modified: +12 lines, new functions: validate_user
[14:32:45] 🤖 Hey, nice addition of that validate_user function! You might want to consider adding some input validation and error handling for edge cases.

> I was thinking about that too. What specific validations would you suggest?

[14:33:02] 🤖 For user validation, I'd suggest checking for empty inputs, validating email formats if applicable, and implementing rate limiting to prevent brute force attempts. Also consider logging failed attempts for security monitoring.

[14:35:12] + File user_model.py created: +45 lines, new functions: User, save, load
[14:35:15] 🤖 I see you're building out the User model - that's a solid separation of concerns! The save/load methods look like they'll work well with your validation layer.

> quit
[14:36:05] Blue CLI stopped.
```

## File Structure

```
Blue_2/
├── blue.py              # Main CLI entry point
├── blue_cli.py          # Core system coordinator
├── observer_agent.py    # File monitoring and change detection
├── navigator_agent.py   # AI reasoning and conversation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required for AI features)

### Supported File Types
The system monitors common programming file extensions. You can modify the `supported_extensions` set in `observer_agent.py` to add or remove file types.

### Change Detection Thresholds
- Buffer size: 10 recent changes (configurable in `observer_agent.py`)
- Processing trigger: 5 accumulated changes or function detection
- Response length: Up to 200 tokens for concise feedback

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY not found"**
   - Make sure you've created a `.env` file with your API key
   - Verify the API key is valid

2. **No file changes detected**
   - Check that you're editing files with supported extensions
   - Verify the directory path is correct
   - Hidden files and common build directories are ignored

3. **Permission errors**
   - Ensure you have read access to the directory you're monitoring
   - Some system directories may require special permissions

### Performance Tips

- For large codebases, consider monitoring specific subdirectories
- The system automatically ignores build directories (`node_modules`, `__pycache__`, etc.)
- File content is cached efficiently to detect meaningful changes

## Extending Blue CLI

### Adding New File Types
Edit the `supported_extensions` set in `observer_agent.py`:
```python
self.supported_extensions.add('.your_extension')
```

### Customizing AI Behavior
Modify the system prompts in `navigator_agent.py` to change how the AI responds to different situations.

### Adding New Agents
The architecture supports additional agents - simply create new agent classes and integrate them into the `blue_cli.py` coordinator.

## Requirements

- Python 3.7+
- Anthropic API key
- Internet connection for AI features
- Read access to the directories you want to monitor

## License

This project is for educational and development purposes. Please respect API usage guidelines and rate limits.
