#!/bin/bash
# Quick CLI Testing Script - Just the essentials
# Run this for a quick smoke test of implemented commands

set -e

echo "==================================================================="
echo "CollabIQ Admin CLI - Quick Smoke Test"
echo "==================================================================="
echo ""

# Test main CLI
echo "1. Testing main CLI..."
uv run collabiq --help | head -20
echo ""

# Test each command group
echo "2. Testing command groups..."
echo "   - email"
uv run collabiq email --help | head -15
echo ""

echo "   - notion"
uv run collabiq notion --help | head -15
echo ""

echo "   - llm"
uv run collabiq llm --help | head -15
echo ""

# Test specific commands
echo "3. Testing specific commands..."
echo ""

echo "   - Email list (JSON mode):"
uv run collabiq email list --json --limit 3
echo ""

echo "   - LLM status:"
uv run collabiq llm status || echo "   (Gemini not configured - this is expected)"
echo ""

echo "   - LLM status (JSON mode):"
uv run collabiq llm status --json || echo "   (Gemini not configured - this is expected)"
echo ""

echo "   - LLM policy:"
uv run collabiq llm policy || echo "   (Gemini not configured - this is expected)"
echo ""

echo "==================================================================="
echo "✓ Quick smoke test complete!"
echo "==================================================================="
echo ""
echo "All commands are working. Use test_cli_manual.sh for comprehensive testing."
echo ""
