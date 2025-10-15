#!/bin/bash
# Bash installation snippet for AI Shell

echo "# Add this to your ~/.bashrc file:"
echo ""
cat << 'EOF'
# AI Shell integration for bash
_ai_widget() {
  local goal cmd
  read -rp "AI goal: " goal || return
  cmd="$(ai suggest "$goal" 2>/dev/null)" || return
  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}
bind -x '"\C-g":"_ai_widget"'   # Ctrl-G
EOF

echo ""
echo "After adding this to ~/.bashrc, restart your shell or run:"
echo "  source ~/.bashrc"
echo ""
echo "Then press Ctrl-G to use AI Shell!"
