# Research: Production Readiness Fixes

**Phase**: 017-production-readiness-fixes
**Date**: 2025-11-19
**Status**: Phase 0 Complete

## Research Questions

### 1. Daemon Process Management Library

**Question**: What library or approach should be used for Python daemon process management with SIGTERM/SIGINT handling?

**Decision**: Use **native Python signal handling** with custom implementation (no external daemon library)

**Rationale**:
1. **Simplicity**: Python's built-in `signal` module provides all needed functionality
2. **Existing Infrastructure**: Typer CLI already handles command execution, don't need process daemonization
3. **Cross-Platform**: Works on both Linux and macOS without additional dependencies
4. **Control**: Custom signal handlers give fine-grained control over shutdown sequence
5. **Testing**: Easy to test with mock signals and state verification

**Alternatives Considered**:
- **python-daemon** (pypi): Full daemonization with PID files, detaching from terminal
  - **Rejected**: Overkill for our use case. We need a long-running CLI process, not a full system daemon
  - Adds complexity for minimal benefit (detaching from terminal not required)
  - Harder to test and debug

- **systemd integration**: Use systemd service files with Type=simple
  - **Rejected**: Out of scope (FR-258 explicitly states no systemd service files)
  - Users will deploy as needed for their environment
  - systemd-specific, not cross-platform

- **APScheduler**: Python scheduling library with background jobs
  - **Rejected**: Too heavyweight, includes job queue and persistence we don't need
  - We need simple interval-based checking, not complex scheduling

**Implementation Approach**:
```python
import signal
import sys
import time
from typing import Callable

class DaemonController:
    def __init__(self):
        self.running = True
        self.shutdown_requested = False

    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown: finish current work, then exit"""
        self.shutdown_requested = True
        # Wait for current email processing to complete

    def run(self, interval_seconds: int, process_func: Callable):
        self.setup_signal_handlers()
        while self.running and not self.shutdown_requested:
            try:
                process_func()  # Process emails
                time.sleep(interval_seconds)
            except Exception as e:
                # Log error, continue on next interval
                pass
```

**References**:
- Python signal module: https://docs.python.org/3/library/signal.html
- Graceful shutdown patterns: https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully

---

### 2. OAuth2 Token Encryption Best Practices

**Question**: What encryption approach should be used for storing Gmail OAuth2 tokens at rest?

**Decision**: Use **Fernet symmetric encryption** from `cryptography` library

**Rationale**:
1. **Built for Purpose**: Fernet is designed for encrypting small data like tokens
2. **Authenticated Encryption**: Provides both confidentiality and integrity (HMAC)
3. **Simple API**: Easy to use correctly (hard to misuse)
4. **Standard**: Based on AES-128-CBC with PKCS7 padding + HMAC-SHA256
5. **Existing Dependency**: `cryptography` already widely used, minimal addition

**Alternatives Considered**:
- **Infisical SDK**: Use existing secrets management
  - **Rejected**: Tokens are ephemeral (expire/refresh), not static secrets
  - Adds API dependency for token storage (network latency)
  - Infisical best for configuration secrets, not dynamic OAuth tokens

- **AES-GCM directly**: Use lower-level cryptography primitives
  - **Rejected**: More error-prone, requires managing nonces correctly
  - Fernet handles key derivation and nonce management automatically

- **Base64 encoding**: Not encryption, just obfuscation
  - **Rejected**: Not security, just encoding (anyone can decode)

**Implementation Approach**:
```python
from cryptography.fernet import Fernet
import os
import json

class TokenManager:
    def __init__(self):
        # Key from environment variable (managed via Infisical or .env)
        encryption_key = os.getenv("GMAIL_TOKEN_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate new key on first run
            encryption_key = Fernet.generate_key().decode()
            # User must persist this key
        self.cipher = Fernet(encryption_key.encode())

    def encrypt_tokens(self, access_token: str, refresh_token: str) -> bytes:
        data = json.dumps({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
        return self.cipher.encrypt(data.encode())

    def decrypt_tokens(self, encrypted_data: bytes) -> dict:
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
```

**Security Notes**:
- Encryption key stored in environment variable (not in code)
- Key managed via existing Infisical + .env infrastructure
- If key is lost, user must re-authenticate with Gmail (acceptable trade-off)
- Token file permissions: 0600 (read/write owner only)

**References**:
- Cryptography Fernet: https://cryptography.io/en/latest/fernet/
- OWASP Token Storage: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html

---

### 3. Korean Name Fuzzy Matching with rapidfuzz

**Question**: What fuzzy matching algorithm and threshold work best for Korean names?

**Decision**: Use **rapidfuzz.fuzz.ratio()** with **≥85% threshold** (configurable)

**Rationale**:
1. **Existing Dependency**: rapidfuzz already used in Phase 014 for company matching
2. **Unicode Support**: Handles Korean Hangul characters correctly
3. **Levenshtein Distance**: Good for name variants (spacing, typos)
4. **Performance**: C++ implementation, fast enough for <100 users
5. **Empirical Testing**: 85% threshold balances precision/recall based on Korean name patterns

**Alternatives Considered**:
- **Exact string matching**: `name1 == name2`
  - **Rejected**: Too strict, fails on spacing differences ("김철수" vs "김 철수")

- **Phonetic matching** (Metaphone, Soundex): Convert to phonetics
  - **Rejected**: Designed for English, doesn't work for Korean Hangul
  - Korean uses syllabic blocks, not phonemes

- **Jaro-Winkler distance**: Fuzzy string matching
  - **Considered**: Good for short strings like names
  - **rapidfuzz.fuzz.ratio() chosen**: More familiar, already in use, similar performance

**Implementation Approach**:
```python
from rapidfuzz import fuzz
from typing import List, Optional

class PersonMatcher:
    def __init__(self, confidence_threshold: float = 85.0):
        self.threshold = confidence_threshold

    def find_best_match(
        self,
        target_name: str,
        candidate_users: List[dict]
    ) -> Optional[dict]:
        """
        Find best matching Notion user for Korean name.

        Args:
            target_name: Korean name from email (e.g., "김철수")
            candidate_users: List of Notion users with 'name' field

        Returns:
            Best matching user dict or None if below threshold
        """
        best_score = 0.0
        best_match = None

        for user in candidate_users:
            # Try matching against user's name field
            score = fuzz.ratio(target_name, user['name'])

            if score > best_score:
                best_score = score
                best_match = user

        if best_score >= self.threshold:
            return best_match
        return None
```

**Edge Cases Handled**:
- Multiple matches above threshold: Return highest score
- No matches above threshold: Return None, log warning
- Empty candidate list: Return None
- Whitespace variations: rapidfuzz handles automatically

**Testing Strategy**:
- Unit tests with known Korean name pairs and expected scores
- Integration tests with real Notion workspace user list
- Edge case tests: similar names (김철수 vs 김철호), spacing variants

**References**:
- rapidfuzz documentation: https://maxbachmann.github.io/RapidFuzz/
- Korean name patterns: https://en.wikipedia.org/wiki/Korean_name

---

### 4. Multi-LLM Orchestration for Summary Quality

**Question**: What orchestration strategy (consensus vs best-match) should be default for collaboration summaries?

**Decision**: Use **consensus strategy** as default, with **best-match as fallback**

**Rationale**:
1. **Quality Over Speed**: Consensus produces more reliable summaries (majority vote)
2. **Existing Infrastructure**: Phase 012 already implements both strategies
3. **Graceful Degradation**: If consensus fails (no majority), fall back to best-match
4. **User Feedback**: Spec notes "inconsistent quality" as #2 complaint, justifies 2-3 LLM calls
5. **Configurable**: Users can switch to best-match if latency is critical

**Alternatives Considered**:
- **Single LLM** (Gemini only): Fastest, no orchestration
  - **Rejected**: Current approach, produces inconsistent summaries (reason for this feature)

- **Weighted voting**: Assign different weights to each LLM
  - **Rejected**: No empirical data on which LLM produces better Korean summaries
  - Adds complexity without clear benefit

- **Sequential refinement**: Use LLM A's output as input to LLM B
  - **Rejected**: Higher latency, more API calls, harder to parallelize
  - Consensus is simpler and well-understood

**Implementation Approach**:
```python
from collabiq.adapters.llm_orchestrator import LLMOrchestrator, OrchestrationStrategy

class SummaryEnhancer:
    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    def generate_summary(self, email_content: str) -> str:
        """
        Generate 1-4 line summary using multi-LLM consensus.

        Tries consensus first, falls back to best-match if no majority.
        """
        prompt = self._build_summary_prompt(email_content)

        try:
            # Try consensus strategy (2+ LLMs agree)
            result = self.orchestrator.orchestrate(
                prompt=prompt,
                strategy=OrchestrationStrategy.CONSENSUS,
                max_length=400  # 1-4 lines
            )
            return result.summary

        except ConsensusFailureError:
            # Fall back to best-match (highest quality score)
            result = self.orchestrator.orchestrate(
                prompt=prompt,
                strategy=OrchestrationStrategy.BEST_MATCH,
                max_length=400
            )
            return result.summary
```

**Performance Considerations**:
- Consensus: 2-3 LLM API calls in parallel → ~5-8 seconds
- Within SC-006 constraint (<8 seconds per email)
- Latency acceptable for improved quality (user feedback-driven)

**References**:
- Phase 012 LLM orchestration implementation
- Multi-agent consensus patterns: https://arxiv.org/abs/2310.20151

---

### 5. Daemon State Persistence Strategy

**Question**: How should daemon state (last processed email ID) be persisted for restart resilience?

**Decision**: Use **JSON file** in `data/daemon/state.json` with atomic writes

**Rationale**:
1. **Simplicity**: JSON is human-readable, easy to debug
2. **Consistency**: Matches existing file-based storage pattern (notion_cache, extractions)
3. **No Dependencies**: No database required for single daemon instance
4. **Atomic Writes**: Use temp file + rename for crash safety
5. **Fast**: File I/O negligible compared to email processing

**Alternatives Considered**:
- **SQLite database**: Structured storage with transactions
  - **Rejected**: Overkill for single key-value pair (last_email_id)
  - Adds dependency and complexity

- **Redis/Memcached**: In-memory cache with persistence
  - **Rejected**: Requires separate service, not portable
  - Out of scope for single-instance deployment

- **Environment variable**: Store state in .env file
  - **Rejected**: .env for configuration, not runtime state
  - Harder to update atomically

**Implementation Approach**:
```python
import json
import os
from pathlib import Path
from typing import Optional

class StateManager:
    def __init__(self, state_file: Path = Path("data/daemon/state.json")):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def save_last_processed_email(self, email_id: str, timestamp: str):
        """Atomically save daemon state."""
        state = {
            "last_email_id": email_id,
            "last_processed_at": timestamp,
            "daemon_start": self._get_daemon_start(),
            "total_emails_processed": self._get_total() + 1
        }

        # Atomic write: temp file + rename
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        temp_file.rename(self.state_file)

    def load_last_processed_email(self) -> Optional[str]:
        """Load last processed email ID, or None if first run."""
        if not self.state_file.exists():
            return None
        with open(self.state_file) as f:
            state = json.load(f)
        return state.get("last_email_id")
```

**Crash Safety**:
- Temp file write + rename ensures atomic update
- If crash during write, old state.json remains intact
- Worst case: Re-process last email (idempotent operations)

**References**:
- Atomic file writes: https://lwn.net/Articles/457667/
- State management patterns: Martin Fowler's "Patterns of Enterprise Application Architecture"

---

### 6. Test Report Generation Format

**Question**: What Markdown format should be used for test reports?

**Decision**: Use **GitHub Flavored Markdown (GFM)** with tables and code blocks

**Rationale**:
1. **User Requirement**: Spec explicitly requests Markdown (not HTML)
2. **Readability**: GFM renders nicely in GitHub, VS Code, IDEs
3. **Parseable**: Can be converted to HTML/PDF if needed later
4. **Tables**: Native support for pass/fail counts, coverage metrics
5. **Existing Tools**: pytest output can be captured and formatted as Markdown

**Implementation Approach**:
```markdown
# Test Execution Report: Phase 017 Production Readiness Fixes

**Date**: 2025-11-19 14:35:22
**Branch**: 017-production-readiness-fixes
**Duration**: 3m 42s

## Summary

| Metric | Value | Baseline | Change |
|--------|-------|----------|--------|
| Total Tests | 1,015 | 989 | +26 |
| Passed | 901 | 856 | +45 |
| Failed | 12 | 18 | -6 |
| Skipped | 102 | 115 | -13 |
| Pass Rate | 88.8% | 86.5% | +2.3% |
| Coverage | 84.2% | 82.1% | +2.1% |

## Test Categories

### Unit Tests
- **Total**: 312 tests (+4 new)
- **Passed**: 308 (98.7%)
- **Failed**: 4
- **Duration**: 12.3s

### Integration Tests
- **Total**: 445 tests (+15 new)
- **Passed**: 428 (96.2%)
- **Failed**: 7
- **Duration**: 1m 48s

### E2E Tests
- **Total**: 12 tests (+3 new)
- **Passed**: 10 (83.3%)
- **Failed**: 1
- **Duration**: 1m 21s

## Failures

### High Priority

```
FAILED tests/integration/test_daemon_lifecycle.py::test_graceful_shutdown_during_processing
AssertionError: Daemon did not complete current email within 10 second timeout
Expected: Email marked as processed
Actual: Email still in progress state
```

## Quality Improvements (Phase 017)

- ✅ Person assignment success rate: 96.2% (target: 95%)
- ✅ Summary quality rating: 91.5% "clear and useful" (target: 90%)
- ✅ UUID validation error rate: 3.8% (target: <5%)
- ⚠️ Daemon stability: 18 hours continuous (target: 24+ hours) - IN PROGRESS
```

**References**:
- GitHub Flavored Markdown: https://github.github.com/gfm/
- Markdown tables: https://www.markdownguide.org/extended-syntax/

---

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Daemon Management | Native Python signal handling | Simplicity, no external deps |
| Token Encryption | Fernet symmetric encryption | Secure, simple API |
| Name Matching | rapidfuzz.fuzz.ratio() ≥85% | Existing dep, proven approach |
| LLM Orchestration | Consensus with best-match fallback | Quality over speed |
| State Persistence | JSON file with atomic writes | Simple, crash-safe |
| Test Reports | GitHub Flavored Markdown | Readable, parseable |

**All NEEDS CLARIFICATION items resolved.** Ready for Phase 1 design.
