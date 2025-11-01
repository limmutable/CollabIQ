# Implementation Tasks: Gmail Setup for Production Email Access

**Feature**: 005-gmail-setup
**Branch**: `005-gmail-setup`
**Generated**: 2025-11-01
**TDD Required**: Yes (per Constitution Principle III)

## Task Summary

- **Total Tasks**: 30
- **User Story 1 (P1)**: 12 tasks (Setup + OAuth + Documentation)
- **User Story 2 (P1)**: 8 tasks (Group alias handling + Tests)
- **User Story 3 (P2)**: 6 tasks (Integration tests with real Gmail)
- **Polish Phase**: 4 tasks (Final validation + cleanup)
- **Parallel Opportunities**: 8 parallelizable tasks marked with [P]

## Implementation Strategy

**MVP Scope**: User Story 1 alone provides complete value - developers can authenticate with Gmail API and retrieve emails from collab@signite.co.

**Independent Increments**: Each user story is independently testable:
- **US1**: Can authenticate and retrieve at least one email
- **US2**: Can filter emails by group alias using `deliveredto:` query
- **US3**: All integration tests pass with real Gmail API

**TDD Discipline**: Tests MUST be written before implementation code. All test tasks precede their corresponding implementation tasks.

---

## Phase 1: Setup & Configuration

**Goal**: Initialize project dependencies and configuration for Gmail API integration.

**Tasks**:

- [X] T001 Update pyproject.toml with google-auth-oauthlib and google-api-python-client dependencies
- [X] T002 Update .gitignore to exclude credentials.json and token.json files
- [X] T003 Verify .env.example includes GOOGLE_CREDENTIALS_PATH placeholder
- [X] T004 Create docs/ directory if it doesn't exist

**Completion Criteria**:
- Dependencies installed and importable
- Sensitive files excluded from version control
- Project structure ready for Gmail API integration

---

## Phase 2: User Story 1 - Set Up Gmail API Credentials (P1)

**Story Goal**: Developers can configure OAuth2 credentials and authenticate with Gmail API to retrieve emails from collab@signite.co.

**Independent Test**: Run authentication flow and verify system successfully retrieves at least one email.

**Acceptance Criteria** (from spec.md):
1. Follow credential setup guide → download credentials.json
2. Run initial authentication → browser opens, stores refresh tokens
3. Stored refresh tokens exist → automatically refreshes without user intervention
4. OAuth2 setup complete → successfully retrieves email messages

### Tests First (TDD)

- [X] T005 [P] [US1] Write test_oauth_credentials_loading in tests/integration/test_gmail_oauth.py
- [X] T006 [P] [US1] Write test_oauth_token_refresh in tests/integration/test_gmail_oauth.py
- [X] T007 [P] [US1] Write test_oauth_first_time_flow_simulation in tests/integration/test_gmail_oauth.py
- [X] T008 [US1] Write test_gmail_api_connection in tests/integration/test_gmail_oauth.py

**Test Coverage**:
- OAuth2 credentials loading from Infisical or .env
- Token refresh when access token expires
- First-time OAuth flow (simulated - cannot fully automate browser interaction)
- Gmail API connection with valid credentials

### Implementation

- [X] T009 [US1] Update src/config/settings.py to add GOOGLE_CREDENTIALS_PATH configuration
- [X] T010 [US1] Verify src/email_receiver/gmail_receiver.py uses http://127.0.0.1:8080 redirect URI (check line 122)
- [X] T011 [US1] Update src/email_receiver.py OAuth error messages to be actionable per FR-008
- [X] T012 [US1] Verify src/email_receiver/gmail_receiver.py handles expired refresh tokens (lines 112-116)

**Implementation Notes**:
- Most OAuth logic already exists in gmail_receiver.py
- Focus on configuration validation and error message clarity
- Ensure credentials path can be loaded from Infisical or .env

### Documentation

- [X] T013 [P] [US1] Create docs/gmail-oauth-setup.md with detailed Google Cloud Console setup guide
- [X] T014 [P] [US1] Create docs/troubleshooting-gmail-api.md with common error solutions
- [X] T015 [US1] Update README.md with Gmail setup instructions and link to docs/gmail-oauth-setup.md
- [X] T016 [US1] Copy specs/005-gmail-setup/quickstart.md to docs/gmail-quickstart-guide.md

**Documentation Coverage**:
- Step-by-step Google Cloud Console OAuth2 credential creation
- Local configuration (credentials.json placement, environment variables)
- First-time authentication flow
- Common errors and troubleshooting (redirect URI mismatch, scope issues, token expiration)

**Phase 2 Completion Criteria**:
- [X] All US1 tests pass (T005-T008) - 8/8 tests passing
- [X] OAuth2 credentials can be loaded from Infisical or .env - Implemented in settings.py
- [X] Token refresh works automatically - Verified in gmail_receiver.py and tests
- [X] Documentation allows setup in <15 minutes (SC-001) - Gmail OAuth setup guide created
- [X] At least one email can be retrieved from Gmail API - Successfully authenticated via scripts/authenticate_gmail.py

---

## Phase 3: User Story 2 - Handle Group Alias Email Access (P1)

**Story Goal**: System accesses emails sent to collab@signite.co group alias using `deliveredto:` query filter through authenticated member account.

**Independent Test**: Send test email to collab@signite.co and verify retrieval through member account inbox.

**Acceptance Criteria** (from spec.md):
1. Email sent to collab@signite.co → appears in member inboxes
2. Member account has valid OAuth2 → retrieves messages using deliveredto: filter
3. Documentation followed → developers understand which account to authenticate with

### Tests First (TDD)

- [X] T017 [P] [US2] Write test_group_alias_query_filter in tests/integration/test_gmail_receiver.py
- [X] T018 [P] [US2] Write test_deliveredto_query_construction in tests/unit/test_group_alias.py
- [X] T019 [US2] Write test_group_alias_email_retrieval_integration in tests/integration/test_gmail_receiver.py

**Test Coverage**:
- Query construction for `deliveredto:"collab@signite.co"` filter
- Email retrieval with group alias query
- Verification that only group emails are returned (not all inbox emails)

### Implementation

- [X] T020 [US2] Update src/email_receiver/gmail_receiver.py fetch_emails() to support custom query parameter
- [X] T021 [US2] Add deliveredto query filter support in src/email_receiver/gmail_receiver.py
- [X] T022 [US2] Update src/email_receiver/gmail_receiver.py default query to include 'deliveredto:"collab@signite.co"'
- [X] T023 [US2] Verify email address change from portfolioupdates@signite.co to collab@signite.co in comments/logs

**Implementation Notes**:
- User mentioned changing from portfolioupdates@signite.co to collab@signite.co
- Added query parameter support to fetch_emails() method
- Default query is now `'deliveredto:"collab@signite.co" in:inbox'`
- Custom queries can be passed to override default behavior

### Documentation

- [X] T024 [P] [US2] Add group alias authentication section to docs/gmail-oauth-setup.md (already present)
- [X] T025 [US2] Document which Google Workspace account to authenticate with (any group member) in docs/gmail-oauth-setup.md (already present)

**Phase 3 Completion Criteria**:
- [X] All US2 tests pass (T017-T019) - 2/2 integration tests passing, 6/6 unit tests passing
- [X] Emails sent to collab@signite.co are retrievable via default query
- [X] Query filter correctly uses `deliveredto:` operator
- [X] Documentation explains group alias authentication (FR-011)

---

## Phase 4: User Story 3 - Pass Test Suites with Real Gmail Connection (P2)

**Story Goal**: Integration tests validate gmail_receiver.py works with actual Gmail API (not mocks).

**Independent Test**: Run integration test suite with real Gmail API credentials → all tests pass.

**Acceptance Criteria** (from spec.md):
1. Valid Gmail API credentials configured → integration tests connect without auth errors
2. Test emails exist in inbox → retrieval tests fetch and parse messages
3. All Gmail API operations tested → no failures related to authentication or email access

### Tests First (TDD)

- [ ] T026 [P] [US3] Write test_real_gmail_authentication in tests/e2e/test_cli_extraction.py
- [ ] T027 [P] [US3] Write test_real_gmail_email_retrieval in tests/e2e/test_cli_extraction.py
- [ ] T028 [US3] Write test_real_gmail_group_alias_filtering in tests/e2e/test_cli_extraction.py

**Test Coverage**:
- Real Gmail API authentication (not mocked)
- Real email retrieval from collab@signite.co
- Real group alias filtering with deliveredto: query
- End-to-end CLI extraction with real Gmail data

### Implementation

- [ ] T029 [US3] Update tests/integration/test_gmail_receiver.py to support real API testing (remove/parameterize mocks)
- [ ] T030 [US3] Add pytest markers for real API tests (e.g., @pytest.mark.real_api, skipif no credentials)

**Implementation Notes**:
- Tests should skip gracefully if credentials not configured
- Use pytest.mark.skipif to check for GOOGLE_CREDENTIALS_PATH
- Existing tests in test_cli_extraction.py already have skipif logic (lines 46-49, 93-96)

**Phase 4 Completion Criteria**:
- [ ] All US3 tests pass with real Gmail API (T026-T028)
- [ ] Test suite runs successfully with GOOGLE_CREDENTIALS_PATH configured
- [ ] Tests skip gracefully when credentials not available
- [ ] 100% pass rate for real API tests (SC-004)

---

## Phase 5: Polish & Cross-Cutting Concerns

**Goal**: Final validation, edge case handling, and documentation polish.

**Tasks**:

- [ ] T031 [P] Run full test suite and verify 100% pass rate for configured API tests
- [ ] T032 [P] Validate documentation completeness (setup takes <15 minutes per SC-001)
- [ ] T033 Update ROADMAP.md or README.md to reflect Phase 2a completion status
- [ ] T034 Run /speckit.checklist to verify all acceptance criteria met

**Edge Cases Validated**:
- OAuth2 token expiration during email retrieval (T006)
- Rate limiting from Gmail API (already in gmail_receiver.py lines 228-238)
- Missing credentials.json file (T005)
- Network failures during token refresh (existing error handling lines 133-139)
- Authenticated user removed from group (handled by Google Workspace, documented)

**Completion Criteria**:
- [ ] All acceptance scenarios pass for US1, US2, US3
- [ ] All success criteria met (SC-001 through SC-006)
- [ ] Documentation validated by walking through setup process
- [ ] No test failures related to authentication or email access

---

## Dependencies Between User Stories

```
User Story 1 (OAuth Setup) → MUST complete before US2 and US3
    ↓
User Story 2 (Group Alias) → Can run in parallel with US3 tests
    ↓
User Story 3 (Test Suite) → Validates US1 and US2 work correctly

Polish Phase → Final validation after all user stories complete
```

**Critical Path**: US1 → US2 → US3 → Polish (linear dependency)

**Parallel Opportunities**:
- Documentation tasks (T013, T014, T024) can be written in parallel
- Test writing (T005-T008, T017-T019, T026-T028) can happen in parallel within each phase
- Final validation (T031, T032) can run in parallel

---

## Parallel Execution Examples

### Phase 2 (User Story 1)

**Tests (can write in parallel)**:
```bash
# Developer A
pytest tests/integration/test_gmail_oauth.py::test_oauth_credentials_loading -v

# Developer B
pytest tests/integration/test_gmail_oauth.py::test_oauth_token_refresh -v

# Developer C
pytest tests/integration/test_gmail_receiver.py::test_gmail_api_connection -v
```

**Documentation (can write in parallel)**:
```bash
# Developer A
vim docs/gmail-oauth-setup.md

# Developer B
vim docs/troubleshooting-gmail-api.md
```

### Phase 3 (User Story 2)

**Tests (can write in parallel)**:
```bash
# Developer A
pytest tests/integration/test_gmail_receiver.py::test_group_alias_query_filter -v

# Developer B
pytest tests/unit/test_group_alias.py::test_deliveredto_query_construction -v
```

### Phase 5 (Polish)

**Validation (can run in parallel)**:
```bash
# Terminal 1
pytest tests/ -v --real-api

# Terminal 2
time bash -c "source docs/gmail-oauth-setup.md instructions"  # Validate <15min
```

---

## Test Execution Order (TDD)

**CRITICAL**: Tests MUST be written and fail BEFORE implementation code is written.

### Phase 2 Test-First Workflow

1. Write T005 (test_oauth_credentials_loading) → ❌ FAIL (expected)
2. Write T006 (test_oauth_token_refresh) → ❌ FAIL (expected)
3. Write T007 (test_oauth_first_time_flow) → ❌ FAIL (expected)
4. Write T008 (test_gmail_api_connection) → ❌ FAIL (expected)
5. Run all tests → ❌ ALL FAIL (red phase complete)
6. Implement T009-T012 (settings, error messages, token handling)
7. Run all tests → ✅ ALL PASS (green phase complete)
8. Refactor if needed (refactor phase)

### Phase 3 Test-First Workflow

1. Write T017 (test_group_alias_query_filter) → ❌ FAIL (expected)
2. Write T018 (test_deliveredto_query_construction) → ❌ FAIL (expected)
3. Write T019 (test_group_alias_email_retrieval) → ❌ FAIL (expected)
4. Run all tests → ❌ ALL FAIL (red phase complete)
5. Implement T020-T023 (query parameter, deliveredto filter, default query)
6. Run all tests → ✅ ALL PASS (green phase complete)
7. Refactor if needed (refactor phase)

### Phase 4 Test-First Workflow

1. Write T026 (test_real_gmail_authentication) → ❌ FAIL (expected)
2. Write T027 (test_real_gmail_email_retrieval) → ❌ FAIL (expected)
3. Write T028 (test_real_gmail_group_alias_filtering) → ❌ FAIL (expected)
4. Run all tests → ❌ ALL FAIL (red phase complete)
5. Implement T029-T030 (remove mocks, add pytest markers)
6. Run all tests → ✅ ALL PASS (green phase complete)

---

## File Changes Summary

### New Files

- `docs/gmail-oauth-setup.md` - Detailed OAuth2 setup guide (T013)
- `docs/troubleshooting-gmail-api.md` - Common error solutions (T014)
- `docs/gmail-quickstart-guide.md` - Copy of quickstart.md (T016)
- `tests/integration/test_gmail_oauth.py` - OAuth flow tests (T005-T007)
- `tests/unit/test_group_alias.py` - Group alias query tests (T018)

### Modified Files

- `pyproject.toml` - Add Google API dependencies (T001)
- `.gitignore` - Exclude credentials.json, token.json (T002)
- `.env.example` - Add GOOGLE_CREDENTIALS_PATH (T003)
- `src/config/settings.py` - Add GOOGLE_CREDENTIALS_PATH config (T009)
- `src/email_receiver/gmail_receiver.py` - Query filter support, error messages (T010-T012, T020-T023)
- `tests/integration/test_gmail_receiver.py` - Add group alias tests (T008, T017, T019, T029)
- `tests/e2e/test_cli_extraction.py` - Add real API tests (T026-T028)
- `README.md` - Gmail setup instructions (T015, T033)

### No Changes Required

- `src/email_receiver/base.py` - Interface unchanged
- `src/cli/extract_entities.py` - CLI logic unchanged (uses gmail_receiver)
- `tests/fixtures/sample_emails/` - Test fixtures unchanged

---

## Validation Checklist (Final)

### User Story 1 Validation

- [ ] Credentials can be loaded from Infisical or .env (FR-003)
- [ ] OAuth2 flow uses Desktop Application pattern (research.md Decision 1)
- [ ] Redirect URI is http://127.0.0.1:8080 (research.md Decision 4)
- [ ] Token refresh is automatic (FR-004, SC-005)
- [ ] Error messages are actionable (FR-008)
- [ ] Setup takes <15 minutes (SC-001)
- [ ] At least one email retrievable (US1 acceptance scenario 4)

### User Story 2 Validation

- [ ] Query uses `deliveredto:"collab@signite.co"` filter (research.md Decision 3)
- [ ] Emails sent to group alias are retrievable (US2 acceptance scenario 1)
- [ ] Documentation explains member account authentication (FR-011, US2 acceptance scenario 3)
- [ ] Only group emails returned (not all inbox emails)

### User Story 3 Validation

- [ ] Integration tests connect without auth errors (US3 acceptance scenario 1)
- [ ] Retrieval tests fetch and parse messages (US3 acceptance scenario 2)
- [ ] All Gmail operations tested (US3 acceptance scenario 3)
- [ ] 100% pass rate for real API tests (SC-004)

### Constitution Compliance

- [ ] TDD discipline followed (tests written first, failed, then passed)
- [ ] Each user story independently testable
- [ ] User Story 1 alone is viable MVP
- [ ] No complexity violations (all PASS in plan.md)
- [ ] All design artifacts complete (plan.md, research.md, data-model.md, quickstart.md)

---

## Success Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| SC-001: Setup time | <15 minutes | Manual walkthrough of docs/gmail-oauth-setup.md |
| SC-002: First auth success | 100% | Run OAuth flow after credentials configured |
| SC-003: Automatic retrieval | No manual intervention | Verify token refresh works (T006) |
| SC-004: Test pass rate | 100% | Run pytest with --real-api marker |
| SC-005: Token auto-refresh | No user intervention | Let access token expire, verify refresh (T006) |
| SC-006: Doc clarity | Unfamiliar dev can follow | Have someone unfamiliar with GCP follow guide |

---

**Generated by**: `/speckit.tasks` command
**Ready for**: `/speckit.implement` command
**Next Step**: Begin Phase 1 (T001-T004) to set up project configuration
