---
trigger: always_on
description: Automatically ensures NotebookLM and Google Workspace MCP environments and tools are installed, configured, and self-healed.
---

# Automatic MCP Environment Management & Self-Healing Rule

## 1. Scope & Objective
Whenever working in this workspace or interacting with NotebookLM and Google Workspace tools across accounts:
- Account 1: `parkjinsoo8485@gmail.com` (`notebooklm-1`, profile: `account1`)
- Account 2: `jinsoo85@genedu.kr` (`notebooklm-2`, profile: `account2`)
- Account 3: `lea8485@genedu.kr` (`notebooklm-3`, profile: `account3`)

## 2. Environment Verification & Self-Healing Protocol
Whenever a user request requires NotebookLM or Google Workspace tools:
1. **Python Dependencies Check**:
   - Check if `notebooklm-py` and `playwright` are installed.
   - If missing, autonomously execute:
     ```powershell
     python -m pip install "notebooklm-py[mcp]" playwright
     python -m playwright install chromium
     ```
2. **Profile Check**:
   - Ensure `account1`, `account2`, `account3` profiles exist in `~/.notebooklm/profiles/`.
   - If missing, autonomously run `python -m notebooklm profile create <profile_name>`.
3. **Global MCP Config Check**:
   - Ensure `~/.gemini/config/mcp_config.json` contains `notebooklm-1`, `notebooklm-2`, `notebooklm-3`.
4. **Authentication Check**:
   - If a requested profile is not authenticated, proactively run `python -m notebooklm -p <profile> login` for the user to complete browser authentication.
