# AI Shell 🤖

**AI-assisted Terminal Command Palette for macOS**

Transform your terminal experience with AI-powered command suggestions. Press **Ctrl-G**, describe what you want to do in natural language, and get safe, contextual shell commands instantly.

## ✨ Features

- **🔥 Hotkey Integration**: Press `Ctrl-G` in any terminal to open the AI command palette
- **🧠 Smart Context**: Understands your current directory, git status, and available files
- **🛡️ Safety First**: Built-in safety checks prevent dangerous commands
- **⚡ Fast & Lightweight**: <150ms response time, minimal dependencies
- **🔌 Multiple AI Providers**: Works with OpenAI GPT models or local Ollama
- **📝 Audit Logging**: Tracks all suggestions and executions for transparency
- **🐚 Shell Agnostic**: Works with zsh (default macOS) and bash

## 🚀 60-Second Setup

```bash
# 1. Clone and install
git clone <repo-url> ai-shell
cd ai-shell
python -m venv .venv && source .venv/bin/activate
make quickstart

# 2. Configure AI provider
# Edit .env file with your OpenAI API key or Ollama settings

# 3. Add shell integration (choose one)
make shell-zsh    # for zsh users (macOS default)
make shell-bash   # for bash users

# 4. Restart your shell and press Ctrl-G!
```

## 📋 Prerequisites

- **Python 3.10+**
- **macOS Terminal** (or compatible terminal emulator)
- **AI Provider**: OpenAI API key OR local Ollama installation

## 🔧 Installation

### Quick Install

```bash
make quickstart
```

### Manual Install

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .

# Set up environment
cp env.example .env
# Edit .env with your configuration
```

## ⚙️ Configuration

Edit `.env` file:

```env
# Choose provider: openai | ollama
AI_PROVIDER=openai

# OpenAI (recommended for best results)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# OR Ollama (for local/private usage)
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b

# Server settings (usually no need to change)
AI_HOST=127.0.0.1
AI_PORT=8765
LOG_PATH=~/.ai-shell/audit.jsonl
```

### OpenAI Setup
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set `AI_PROVIDER=openai` and `OPENAI_API_KEY=sk-...` in `.env`

### Ollama Setup (Local AI)
1. Install [Ollama](https://ollama.ai/)
2. Run: `ollama pull llama3.1:8b`
3. Start: `ollama serve`
4. Set `AI_PROVIDER=ollama` in `.env`

## 🐚 Shell Integration

### For zsh (macOS default):

```bash
make shell-zsh
```

Add the output to your `~/.zshrc`:

```zsh
# AI Shell integration for zsh
_ai_widget() {
  emulate -L zsh
  local goal cmd
  vared -p 'AI goal: ' -c goal || return
  cmd="$(ai suggest "$goal" 2>/dev/null)" || return
  if [[ -n "$cmd" ]]; then
    BUFFER="$cmd"
    CURSOR=${#BUFFER}
    zle redisplay
  fi
}
zle -N ai-widget _ai_widget
bindkey '^G' ai-widget   # Ctrl-G
```

### For bash:

```bash
make shell-bash
```

Add the output to your `~/.bashrc`:

```bash
# AI Shell integration for bash
_ai_widget() {
  local goal cmd
  read -rp "AI goal: " goal || return
  cmd="$(ai suggest "$goal" 2>/dev/null)" || return
  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}
bind -x '"\C-g":"_ai_widget"'   # Ctrl-G
```

After adding, restart your shell: `source ~/.zshrc` or `source ~/.bashrc`

## 🎯 Usage

### Interactive Mode (Recommended)

1. **Press `Ctrl-G`** in your terminal
2. **Type your goal** in natural language:
   - "find large log files"
   - "show git commits from last week"
   - "compress all images in this folder"
3. **Review the suggested command**
4. **Press Enter** to execute or **edit** before running

### CLI Mode

```bash
# Get command suggestion
ai suggest "find files larger than 100MB"

# Get suggestion with confirmation prompt
ai run "delete all .tmp files"

# Explain a command
ai explain "rsync -av --delete src/ dest/"
ai explain --last  # explain last suggested command

# Check status
ai status
```

## 🛡️ Safety Features

AI Shell includes multiple safety layers:

- **Risk Scoring**: Commands rated 0.0 (safe) to 1.0 (dangerous)
- **Confirmation Prompts**: High-risk commands require explicit approval
- **Dry-Run Suggestions**: Automatically adds `--dry-run` flags when available
- **Dangerous Pattern Detection**: Blocks commands like `rm -rf /`
- **Audit Logging**: All interactions logged to `~/.ai-shell/audit.jsonl`

### Safety Examples

```bash
# ✅ Safe - executes immediately
"list files" → ls -la

# ⚠️ Moderate risk - adds dry-run flag
"sync folders" → rsync --dry-run -av src/ dest/

# 🚨 High risk - requires confirmation
"delete old logs" → rm -rf /var/log/*.old
```

## 📊 Examples

| Goal | Generated Command |
|------|-------------------|
| "find large files" | `find . -type f -size +100M -ls` |
| "show git log" | `git log --oneline -10` |
| "compress images" | `find . -name "*.jpg" -exec jpegoptim {} \;` |
| "free up space" | `du -sh * \| sort -hr \| head -10` |
| "check disk usage" | `df -h` |
| "find python files" | `find . -name "*.py" -type f` |

## 🔧 Development

```bash
# Install with dev dependencies
make install-dev

# Run tests
make test

# Start development server
make dev

# Code formatting
make format

# Linting
make lint
```

## 📁 Project Structure

```
ai-shell/
├── src/ai_shell/
│   ├── config.py          # Configuration management
│   ├── server.py          # FastAPI daemon
│   ├── cli.py             # CLI interface
│   ├── safety.py          # Safety checks
│   ├── context.py         # Context collection
│   ├── audit.py           # Audit logging
│   └── provider/          # AI providers
│       ├── base.py        # Provider interface
│       ├── openai_provider.py
│       └── ollama_provider.py
├── tests/                 # Unit tests
├── scripts/               # Shell integration scripts
└── Makefile              # Development commands
```

## 🔍 Troubleshooting

### Daemon won't start
```bash
# Check if port is in use
lsof -i :8765

# Start daemon manually
ai daemon

# Check logs
tail -f ~/.ai-shell/audit.jsonl
```

### OpenAI API errors
```bash
# Verify API key
ai status

# Test connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### Ollama connection issues
```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# Start Ollama
ollama serve

# Pull model if needed
ollama pull llama3.1:8b
```

### Shell integration not working
```bash
# Verify function is loaded
type _ai_widget

# Check key binding
bind -p | grep "\\C-g"  # bash
bindkey | grep "\\^G"   # zsh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Typer](https://typer.tiangolo.com/)
- Inspired by GitHub Copilot CLI and other AI-assisted tools
- Safety patterns adapted from shell security best practices

---

**Press `Ctrl-G` and let AI Shell transform your terminal experience!** 🚀 
