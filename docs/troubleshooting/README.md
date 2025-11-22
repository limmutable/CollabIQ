# Troubleshooting Guide

This guide provides solutions for common issues encountered when running CollabIQ.

## Common Issues

### 1. Gmail API Errors

**Symptoms:**
- `RefreshError: ('invalid_grant', 'Token has been expired or revoked.')`
- `HttpError 403... 'Quota exceeded'`

**Solutions:**
- **Token Expired**: The refresh token has expired or been revoked.
  1. Delete `token.json`.
  2. Run `uv run collabiq email verify` to re-authenticate via browser.
  3. Ensure you select all requested scopes.
- **Quota Exceeded**: The application has hit the Gmail API rate limit.
  - Wait for quota reset (usually daily).
  - Reduce `email fetch --limit`.

### 2. Notion API Errors

**Symptoms:**
- `APIResponseError: Could not find database with ID...`
- `APIResponseError: restricted_resource`

**Solutions:**
- **Invalid Database ID**: Verify `NOTION_COLLABORATIONS_DB_ID` in `.env`.
- **Missing Integration Access**: The integration has not been invited to the database page.
  1. Open the database in Notion.
  2. Click `...` > `Connections`.
  3. Add your integration ("CollabIQ Integration").

### 3. LLM Extraction Issues

**Symptoms:**
- "JSON decode error" in logs.
- Empty fields in Notion entries.

**Solutions:**
- **Model Overload**: Gemini may return 503 or refuse generation. The system auto-retries.
- **Strict Formatting**: If LLM returns invalid JSON, check `data/dlq/` for the failed payload.
- **Check Logs**: Run with `--debug` to see the raw LLM response.

### 4. Daemon Mode Issues

**Symptoms:**
- Daemon stops unexpectedly.
- State file corruption.

**Solutions:**
- **Check Logs**: `logs/collabiq.log` or stdout.
- **Reset State**: Delete `data/daemon/state.json` to restart from clean state.
- **Permissions**: Ensure the user running the daemon has write access to `data/`.

## Diagnostic Tools

The CLI provides built-in diagnostic commands:

- `collabiq test validate`: Quick health check of all connections.
- `collabiq llm status --detailed`: Detailed LLM provider metrics.
- `collabiq errors list`: View recent errors in the Dead Letter Queue.

## Support

If issues persist, check the [GitHub Issues](https://github.com/limmutable/CollabIQ/issues) page or contact the maintainers.
