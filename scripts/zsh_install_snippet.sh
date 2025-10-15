#!/bin/bash
# ZSH installation snippet for AI Shell

echo "# Add this to your ~/.zshrc file:"
echo ""
cat << 'EOF'
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
EOF

echo ""
echo "After adding this to ~/.zshrc, restart your shell or run:"
echo "  source ~/.zshrc"
echo ""
echo "Then press Ctrl-G to use AI Shell!"
