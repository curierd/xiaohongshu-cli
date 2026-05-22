# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**xiaohongshu-cli** (or "xhs") is a full-featured Command Line Interface for the Xiaohongshu (小红书) Chinese social platform. It provides access to search, reading, social interactions, content creation, and notifications via a reverse-engineered API.

## Key Architecture

- **CLI Entry Point**: `xhs_cli/cli.py` - Click command registration and group setup
- **Core Client**: `xhs_cli/client.py` - HTTP client with rate limiting, retries, and anti-detection
- **Command Modules**: `xhs_cli/commands/` - Separate modules for auth, reading, interactions, social, creator, notifications
- **Signing**: `xhs_cli/signing.py` (main API) and `xhs_cli/creator_signing.py` (creator API) handle request signatures
- **Formatting**: `xhs_cli/formatter*.py` - Rich terminal output and JSON/YAML structured output
- **Authentication**: `xhs_cli/cookies.py` and `xhs_cli/qr_login.py` - Cookie management and QR login

## Development Commands

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Unit tests only (no network)
uv run pytest tests/ -v --ignore=tests/test_integration.py -m "not smoke"

# Lint
uv run ruff check .
```

## Important Patterns

- **Command Registration**: New commands are added in `xhs_cli/cli.py` by importing and registering the Click group
- **Anti-Detection**: The client uses Gaussian jitter, random long pauses, consistent browser fingerprinting, and adaptive rate limiting
- **Short-Index Navigation**: After listing commands, notes can be referenced by index via `~/.xiaohongshu-cli/index_cache.json`
- **Structured Output**: All commands support `--json` and `--yaml` flags with a standard envelope schema

## Configuration & Storage

Directory: `~/.xiaohongshu-cli/`
- `cookies.json` - Saved cookies (0o600 permissions)
- `token_cache.json` - Cached xsec tokens (LRU, max 500 entries, TTL 1 day)
- `index_cache.json` - Note index for short-index navigation
