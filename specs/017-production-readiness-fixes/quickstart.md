# Quickstart: Production Readiness Fixes (Phase 017)

**Branch**: 017-production-readiness-fixes
**Prerequisites**: Phases 001-016 completed, Python 3.12+, UV package manager

## Overview

Phase 017 enables fully autonomous CollabIQ operation by implementing six critical production fixes:

1. **Person Matching**: Automatically populate 담당자 field using Korean name fuzzy matching
2. **Summary Quality**: Multi-LLM orchestration for better "협업내용" summaries
3. **Token Management**: Automatic Gmail OAuth2 token refresh (30+ days)
4. **UUID Validation**: Improved LLM prompts (<5% error rate)
5. **Daemon Mode**: Autonomous background operation with graceful shutdown
6. **Testing**: Comprehensive E2E tests with Markdown reports

---

## Quick Start (5 minutes)

### Step 1: Install New Dependencies

```bash
# Add cryptography for token encryption
uv add cryptography

# Sync all dependencies
uv sync
```

### Step 2: Configure Token Encryption

```bash
# Generate encryption key for Gmail tokens
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env file
echo "GMAIL_TOKEN_ENCRYPTION_KEY=<generated-key>" >> .env
```

### Step 3: Test Person Matching

```bash
# Process a test email with person field
uv run collabiq process --max-emails 1 --verbose

# Check logs for person matching
# Expected: "Person matched: '김철수' -> <notion-user-uuid> (confidence: 92%)"
```

### Step 4: Test Daemon Mode

```bash
# Start daemon with 15-minute intervals
uv run collabiq run --daemon --interval 15m

# Check daemon status (in another terminal)
uv run collabiq daemon status

# Stop daemon gracefully
uv run collabiq daemon stop
```

### Step 5: Run Phase 017 Tests

```bash
# Run new tests
uv run pytest tests/unit/test_person_matcher.py tests/unit/test_token_manager.py -v

# Generate test report
uv run collabiq test run --report markdown --output phase_017_report.md
```

---

## Detailed Setup

### 1. Person Matching Setup

**Goal**: Automatically populate 담당자 field with matched Notion users.

#### 1.1 Verify Notion Integration Permissions

```bash
# Check integration has user:read permission
uv run collabiq config validate

# Expected output should include:
# ✓ Notion integration: Valid
# ✓ Permissions: user:read
```

If missing permissions:
1. Go to Notion Settings & Members → Integrations
2. Find your CollabIQ integration
3. Ensure "Read user information" is enabled

#### 1.2 Test User Cache

```python
# Test user list fetching and caching
from collabiq.notion_integrator.person_matcher import NotionUserService

service = NotionUserService(token=os.getenv("NOTION_TOKEN"))
users = service.get_all_users()
print(f"Found {len(users)} workspace users")

# Cache file should be created
assert Path("data/notion_cache/workspace_users.json").exists()
```

#### 1.3 Configure Fuzzy Matching Threshold

```bash
# Default threshold is 85% (recommended for Korean names)
# To adjust, set environment variable
echo "PERSON_MATCH_THRESHOLD=90" >> .env
```

---

### 2. Multi-LLM Summary Quality

**Goal**: Improve "협업내용" summary quality using consensus strategy.

#### 2.1 Verify LLM Providers

```bash
# Check all three LLM providers are configured
uv run collabiq config show

# Expected:
# ✓ GEMINI_API_KEY: Set
# ✓ ANTHROPIC_API_KEY: Set
# ✓ OPENAI_API_KEY: Set
```

#### 2.2 Test Summary Generation

```python
# Test multi-LLM consensus for summaries
from collabiq.adapters.llm_orchestrator import SummaryEnhancer

enhancer = SummaryEnhancer()
summary = enhancer.generate_summary(email_content="...")

print(f"Summary: {summary.summary_text}")
print(f"Strategy: {summary.strategy}")  # "consensus" or "best_match"
print(f"Quality: {summary.quality_score}")  # 0.0-1.0
print(f"LLMs: {summary.llm_models}")  # ["gemini-1.5-pro", "claude-3-sonnet", "gpt-4"]
```

#### 2.3 Adjust Orchestration Strategy (Optional)

```bash
# Default is consensus (2-3 LLMs agree)
# To use best-match (fastest single LLM):
echo "LLM_ORCHESTRATION_STRATEGY=best_match" >> .env
```

---

### 3. Gmail Token Management

**Goal**: Automatic token refresh for 30+ days unattended operation.

#### 3.1 Initial OAuth2 Setup (If Not Done)

```bash
# Run Gmail OAuth2 flow to get refresh_token
uv run python -m collabiq.email_receiver.oauth_setup

# Follow prompts:
# 1. Browser opens for Google sign-in
# 2. Grant Gmail read permission
# 3. Tokens saved to data/tokens/gmail_tokens.enc (encrypted)
```

#### 3.2 Verify Token Encryption

```bash
# Check token status
uv run collabiq config token-status

# Expected:
# Gmail Token Status
# ------------------
# Access token: Valid
# Expires in: 45 minutes
# Refresh token: Available
# Encrypted: Yes
# Encryption algorithm: Fernet-AES128
```

#### 3.3 Test Token Refresh

```python
# Simulate token expiration and refresh
from collabiq.email_receiver.token_manager import TokenManager

manager = TokenManager(encryption_key=os.getenv("GMAIL_TOKEN_ENCRYPTION_KEY"))
token_pair = manager.load_tokens()

# Force refresh (even if not expired)
refreshed = manager.refresh_if_needed(token_pair, force=True)

print(f"New expiry: {refreshed.expires_at}")
print(f"Last refreshed: {refreshed.last_refreshed_at}")
```

---

### 4. UUID Validation Improvement

**Goal**: Reduce UUID validation errors from ~10% to <5%.

#### 4.1 Test Improved Prompts

```python
# Test UUID extraction with improved prompts
from collabiq.adapters.gemini_adapter import GeminiAdapter

adapter = GeminiAdapter()
extraction = adapter.extract_collaboration(email_content="...")

# Check UUID validation
uuid_result = extraction.company_uuid
print(f"UUID: {uuid_result.extracted_value}")
print(f"Valid: {uuid_result.validation_status}")  # "valid"
print(f"Retries: {uuid_result.retry_count}")  # 0 if first attempt succeeded
```

#### 4.2 Monitor Error Rate

```bash
# Process 20 test emails and measure UUID error rate
uv run python -m collabiq.testing.uuid_validation_test --emails 20

# Expected output:
# Total emails: 20
# Valid UUIDs: 19 (95%)
# Invalid UUIDs: 1 (5%)
# Error rate: 5.0% ✓ (target: <5%)
```

---

### 5. Daemon Mode

**Goal**: Continuous autonomous operation with graceful shutdown.

#### 5.1 Start Daemon

```bash
# Start daemon with default 15-minute intervals
uv run collabiq run --daemon

# Or customize interval
uv run collabiq run --daemon --interval 5m

# Daemon runs in foreground, logs to stdout
# Press Ctrl+C to stop gracefully
```

#### 5.2 Background Daemon (Production)

```bash
# Run daemon in background with nohup
nohup uv run collabiq run --daemon --interval 15m > daemon.log 2>&1 &

# Save PID for later
echo $! > daemon.pid
```

#### 5.3 Monitor Daemon

```bash
# Check daemon status
uv run collabiq daemon status

# View logs
tail -f daemon.log

# Stop daemon
kill -TERM $(cat daemon.pid)  # Graceful shutdown
# Or
uv run collabiq daemon stop
```

#### 5.4 Daemon State Persistence

```bash
# Daemon state saved to data/daemon/state.json
cat data/daemon/state.json

# Example:
# {
#   "daemon_start_time": "2025-11-19T08:00:00Z",
#   "last_check_time": "2025-11-19T10:15:00Z",
#   "check_interval_seconds": 900,
#   "total_cycles": 9,
#   "emails_processed": 47,
#   "error_count": 1,
#   "current_status": "running",
#   "last_processed_email_id": "18c3a2b1d4e5f6g7",
#   "pid": 12345
# }
```

---

### 6. Comprehensive Testing

**Goal**: Validate all Phase 017 fixes with E2E tests and reports.

#### 6.1 Run Phase 017 Test Suite

```bash
# Run all new tests
uv run pytest tests/unit/test_person_matcher.py \
  tests/unit/test_token_manager.py \
  tests/unit/test_daemon_controller.py \
  tests/integration/test_notion_users_api.py \
  tests/integration/test_gmail_token_refresh.py \
  tests/e2e/test_production_fixes.py \
  -v

# Expected: All tests pass
```

#### 6.2 Generate Test Report

```bash
# Run full test suite with Markdown report
uv run collabiq test run --report markdown --output phase_017_report.md

# View report
cat phase_017_report.md

# Check pass rate ≥86.5% baseline
# Check quality metrics:
# - Person assignment: 95%+
# - Summary quality: 90%+
# - UUID error rate: <5%
```

#### 6.3 Baseline Comparison

```bash
# Save current metrics as baseline
uv run collabiq test run --report json --output baseline_phase017.json

# Later, compare against baseline
uv run collabiq test run --report markdown --baseline baseline_phase017.json

# Report shows improvements:
# Pass rate: +2.3%
# Coverage: +2.1%
# Person assignment: 0% → 96.2%
# Summary quality: 75% → 91.5%
```

---

## Common Issues & Troubleshooting

### Issue 1: Person matching returns no results

**Symptom**: Warning logs "Person matching confidence below threshold"

**Solution**:
```bash
# Lower threshold temporarily
export PERSON_MATCH_THRESHOLD=75

# Or check if name is in workspace
uv run python -c "
from collabiq.notion_integrator.person_matcher import NotionUserService
service = NotionUserService()
users = service.get_all_users()
print([u.name for u in users])
"
```

### Issue 2: Token refresh fails with invalid_grant

**Symptom**: Critical log "Token refresh FAILED: invalid_grant"

**Solution**:
```bash
# User revoked access, must re-authenticate
uv run python -m collabiq.email_receiver.oauth_setup

# New tokens will be saved
```

### Issue 3: Daemon crashes after a few hours

**Symptom**: Daemon stops without logs

**Solution**:
```bash
# Check for unhandled exceptions in logs
tail -100 daemon.log | grep -i error

# Enable verbose logging
uv run collabiq run --daemon --interval 15m --verbose

# Check system resources
free -h  # Memory
df -h    # Disk space
```

### Issue 4: UUID validation still fails frequently

**Symptom**: UUID error rate >5%

**Solution**:
```bash
# Check LLM provider status
uv run collabiq config validate

# Verify retry logic is working
grep "UUID retry" daemon.log

# If Gemini is having issues, temporarily switch to Claude
export PRIMARY_LLM=claude
```

---

## Performance Expectations

Based on success criteria (SC-001 to SC-012):

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Person assignment success | 95% | Check phase_017_report.md quality metrics |
| Summary quality rating | 90% | Manual review of 20 samples |
| Token auto-refresh | 30+ days | Check daemon logs after 30 days |
| UUID error rate | <5% | phase_017_report.md quality metrics |
| Person matching speed | <2s per email | Check daemon cycle logs |
| Multi-LLM summary | <8s per email | Check daemon cycle logs |
| Token refresh | <5s | Check token-status logs |
| 50 emails processing | <12 minutes | Manual mode: `time collabiq run --max-emails 50` |
| Daemon stability | 24+ hours | Check daemon status after 24 hours |
| Daemon graceful shutdown | <10s | `time collabiq daemon stop` |
| Test pass rate | ≥86.5% | phase_017_report.md summary |
| Test report generation | Markdown | Check phase_017_report.md exists |

---

## Next Steps After Phase 017

1. **Monitor Production**: Run daemon for 7 days, check error rates
2. **Tune Thresholds**: Adjust person matching threshold based on false positive/negative rate
3. **Performance Optimization**: If summary generation >8s, consider caching LLM results
4. **Alerting**: Set up monitoring for daemon health and token refresh failures
5. **Documentation**: Update main README with daemon mode instructions

---

## Additional Resources

- **Phase 017 Spec**: [spec.md](spec.md)
- **Research Decisions**: [research.md](research.md)
- **Data Model**: [data-model.md](data-model.md)
- **API Contracts**: [contracts/](contracts/)
- **Main README**: [../../README.md](../../README.md)
- **Testing Guide**: [../../docs/testing/E2E_TESTING.md](../../docs/testing/E2E_TESTING.md)
- **CLI Reference**: [../../docs/cli/CLI_REFERENCE.md](../../docs/cli/CLI_REFERENCE.md)

---

## Getting Help

If you encounter issues:

1. Check daemon logs: `tail -f daemon.log`
2. Run with verbose logging: `--verbose` flag
3. Check test failures: `uv run pytest -v --tb=short`
4. Review error logs in `data/logs/`
5. Verify configuration: `uv run collabiq config validate`

**Ready to implement?** Proceed to `/speckit.tasks` to generate implementation tasks.
