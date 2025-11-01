# Tasks: Infisical Secret Management Integration

**Input**: Design documents from `/specs/003-infisical-secrets/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/infisical_client.yaml

**Tests**: Tests are included as this feature requires TDD (constitution requirement - tests exist for Phase 1a)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project structure**: `src/`, `tests/` at repository root
- All paths relative to `/Users/jlim/Projects/CollabIQ/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Infisical SDK installation

- [x] T001 Install infisicalsdk dependency via uv add infisicalsdk
- [x] T002 [P] Update pyproject.toml to include infisicalsdk in dependencies list
- [x] T003 [P] Update .env.example with Infisical configuration template (INFISICAL_ENABLED, INFISICAL_HOST, INFISICAL_PROJECT_ID, INFISICAL_ENVIRONMENT, INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, INFISICAL_CACHE_TTL)
- [x] T004 [P] Create test fixtures directory at tests/fixtures/infisical/
- [x] T005 [P] Create mock_secrets.json fixture in tests/fixtures/infisical/mock_secrets.json
- [x] T006 [P] Create mock_auth_responses.json fixture in tests/fixtures/infisical/mock_auth_responses.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Infisical client infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create InfisicalConfig entity in src/config/settings.py (add Infisical configuration fields: infisical_enabled, infisical_host, infisical_project_id, infisical_environment, infisical_client_id, infisical_client_secret, infisical_cache_ttl)
- [x] T008 Add field validators for InfisicalConfig in src/config/settings.py (validate environment_slug is dev/staging/prod, validate required fields when enabled=True)
- [x] T009 Create custom exception types in src/config/infisical_client.py (InfisicalAuthError, InfisicalConnectionError, SecretNotFoundError, InfisicalCacheMissError)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 3: User Story 1 - Secure API Key Storage (Priority: P1) 🎯 MVP

**Goal**: Replace .env file credential storage with Infisical centralized secret management. Application successfully retrieves secrets from Infisical and starts without requiring local .env files.

**Independent Test**: Verify application starts with `INFISICAL_ENABLED=true` and retrieves all API keys (GMAIL_CREDENTIALS_PATH, GEMINI_API_KEY, NOTION_API_KEY) from Infisical, logs show "Retrieved X from infisical" messages

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Contract test for InfisicalClient.get_secret() method in tests/unit/test_infisical_client.py (test success, cache hit, not found, connection error scenarios)
- [x] T011 [P] [US1] Contract test for InfisicalClient.get_all_secrets() method in tests/unit/test_infisical_client.py (test success, connection error scenarios)
- [x] T012 [P] [US1] Contract test for InfisicalClient.is_connected() method in tests/unit/test_infisical_client.py (test reachable and unreachable scenarios)
- [ ] T013 [P] [US1] Integration test for Settings with Infisical enabled in tests/unit/test_settings_infisical.py (test secret retrieval, fallback to .env, cache behavior) **[DEFERRED - Not in MVP]**
- [ ] T014 [P] [US1] Integration test for three-tier fallback (API → cache → .env) in tests/integration/test_infisical_integration.py **[DEFERRED - Not in MVP]**

### Implementation for User Story 1

- [x] T015 [US1] Implement InfisicalClient class in src/config/infisical_client.py (initialize SDK client, authenticate via Universal Auth, implement get_secret with three-tier fallback logic)
- [x] T016 [US1] Implement get_all_secrets() method in src/config/infisical_client.py (fetch all secrets for environment, update cache, return dict)
- [x] T017 [US1] Implement refresh_cache() method in src/config/infisical_client.py (force cache refresh, fetch all secrets)
- [x] T018 [US1] Implement is_connected() method in src/config/infisical_client.py (test API connectivity, return boolean)
- [x] T019 [US1] Integrate InfisicalClient into Settings.__init__() in src/config/settings.py (check INFISICAL_ENABLED, initialize client, fetch secrets, override field values, fall back to .env on error)
- [ ] T020 [US1] Add logging for secret retrieval operations in src/config/infisical_client.py (INFO for success, WARNING for fallback, ERROR for failures, never log secret values per FR-007) **[DEFERRED - Not in MVP]**
- [x] T021 [US1] Implement Settings.get_secret_or_env() method to handle Infisical initialization in src/config/settings.py

**Checkpoint**: At this point, User Story 1 MVP is functional - application can retrieve secrets from Infisical with three-tier fallback ✅

---

## Phase 4: User Story 2 - Developer Onboarding Without Manual Secret Sharing (Priority: P2)

**Goal**: New developers access secrets through Infisical authentication instead of receiving credentials via email/Slack

**Independent Test**: New developer with Infisical access granted authenticates with their machine identity and successfully runs application without receiving any secrets from existing team members

### Tests for User Story 2

- [ ] T022 [P] [US2] Integration test for machine identity authentication in tests/integration/test_infisical_integration.py (test valid credentials, invalid credentials, revoked access scenarios)
- [ ] T023 [P] [US2] Integration test for environment-specific access control in tests/integration/test_infisical_integration.py (test dev identity cannot access prod, staging identity cannot access dev)

### Implementation for User Story 2

- [ ] T024 [US2] Add environment slug validation in src/config/infisical_client.py (ensure environment_slug is one of: dev, staging, prod; fail with clear error if invalid)
- [ ] T025 [US2] Implement clear error messages for authentication failures in src/config/infisical_client.py (InfisicalAuthError with actionable recovery steps)
- [ ] T026 [US2] Add developer onboarding documentation in docs/architecture/TECHSTACK.md (update Infisical section with machine identity setup, environment configuration)
- [ ] T027 [US2] Update README.md with Infisical setup instructions (link to quickstart.md, mention machine identity requirement)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - new developers can onboard via Infisical

---

## Phase 5: User Story 3 - Automated Secret Rotation (Priority: P3)

**Goal**: Rotate API keys in Infisical and have all running instances automatically pick up new values within cache TTL

**Independent Test**: Rotate a secret in Infisical, verify application automatically detects and uses new value within cache TTL period (default 60 seconds) without requiring restart

### Tests for User Story 3

- [ ] T028 [P] [US3] Integration test for cache expiration and refresh in tests/unit/test_infisical_client.py (test cache TTL expiration, automatic refresh on next access)
- [ ] T029 [P] [US3] Integration test for secret rotation detection in tests/integration/test_infisical_integration.py (test updated secret value retrieved after cache expires)

### Implementation for User Story 3

- [ ] T030 [US3] Verify SDK cache_ttl parameter is correctly passed during client initialization in src/config/infisical_client.py (default 60s, configurable via INFISICAL_CACHE_TTL)
- [ ] T031 [US3] Implement cache expiration logic in src/config/infisical_client.py (rely on SDK built-in caching, verify automatic refresh behavior)
- [ ] T032 [US3] Add logging for cache refresh operations in src/config/infisical_client.py (INFO log when cache refreshes, include timestamp and secret count)
- [ ] T033 [US3] Document cache TTL configuration in specs/003-infisical-secrets/quickstart.md (explain INFISICAL_CACHE_TTL parameter, default value, impact on rotation timing)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - secret rotation happens automatically

---

## Phase 6: User Story 4 - Environment-Specific Secret Management (Priority: P2)

**Goal**: Different sets of secrets for development, staging, and production environments stored separately in Infisical with clear isolation

**Independent Test**: Configure different Infisical projects/environments and verify each environment only accesses its designated secrets (dev cannot access prod)

### Tests for User Story 4

- [ ] T034 [P] [US4] Integration test for environment isolation in tests/integration/test_infisical_integration.py (test dev environment retrieves dev secrets, prod environment retrieves prod secrets)
- [ ] T035 [P] [US4] Integration test for access control enforcement in tests/integration/test_infisical_integration.py (test authentication fails when dev identity tries to access prod environment)

### Implementation for User Story 4

- [ ] T036 [US4] Implement environment slug parameter usage in src/config/infisical_client.py (pass environment_slug to SDK list_secrets and get_secret_by_name calls)
- [ ] T037 [US4] Add environment validation on startup in src/config/validation.py (verify environment_slug matches INFISICAL_ENVIRONMENT, fail startup if mismatch)
- [ ] T038 [US4] Document environment organization pattern in specs/003-infisical-secrets/quickstart.md (single project with environment slugs, create environments section with dev/staging/prod examples)
- [ ] T039 [US4] Add environment-specific configuration examples in .env.example (show dev, staging, prod configurations with different machine identities)

**Checkpoint**: All user stories should now be independently functional - complete environment isolation achieved

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final integration

- [ ] T040 [P] Add CLI verify command in src/cli.py (collabiq verify-infisical command to test Infisical connectivity, authentication, and secret retrieval)
- [ ] T041 [P] Implement configuration validation on startup in src/config/validation.py (verify Infisical connectivity, check all required secrets present, fail with clear error if missing)
- [ ] T042 [P] Update docs/architecture/TECHSTACK.md with Infisical integration section (add to Known Technical Debt if applicable, document infisicalsdk dependency, security patterns)
- [ ] T043 [P] Create comprehensive quickstart validation script in scripts/verify_infisical_setup.sh (test all steps from quickstart.md, verify machine identity, check secret retrieval)
- [ ] T044 Code cleanup and refactoring in src/config/infisical_client.py (remove any hardcoded values, ensure all logging follows contract, verify no secret values in logs)
- [ ] T045 Run full test suite and verify coverage in tests/ (target: maintain 45%+ coverage from Phase 1a, run pytest --cov=src --cov-report=html)
- [ ] T046 [P] Update .gitignore to ensure .env file never committed (verify credentials.json, token.json, .env all ignored)
- [ ] T047 Run quickstart.md validation end-to-end (follow all 7 steps, verify application starts with Infisical, check logs for successful secret retrieval)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T006) - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion (T007-T009)
  - User Story 1 (Phase 3): Can start after Foundational
  - User Story 2 (Phase 4): Can start after Foundational, integrates with US1 but independently testable
  - User Story 3 (Phase 5): Can start after Foundational, depends on US1 InfisicalClient implementation (T015-T018)
  - User Story 4 (Phase 6): Can start after Foundational, integrates with US1 but independently testable
- **Polish (Phase 7)**: Depends on all desired user stories being complete (T010-T039)

### User Story Dependencies

- **User Story 1 (P1) - Secure API Key Storage**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ **MVP**
- **User Story 2 (P2) - Developer Onboarding**: Can start after Foundational, integrates with US1 Settings but independently testable (authentication works even without US1 complete)
- **User Story 3 (P3) - Automated Secret Rotation**: Depends on US1 completion (requires InfisicalClient.get_secret implementation T015-T018)
- **User Story 4 (P2) - Environment-Specific Management**: Can start after Foundational, integrates with US1 but independently testable (environment isolation works even without US1 complete)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD requirement)
- InfisicalClient methods (T015-T018) before Settings integration (T019-T021)
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005, T006 can all run in parallel (different files)

**Phase 2 (Foundational)**:
- T007 and T008 must be sequential (field validators depend on fields)
- T009 can run in parallel with T007-T008 (different concern)

**Phase 3 (User Story 1)**:
- All tests (T010-T014) can run in parallel
- InfisicalClient methods (T015-T018) can be implemented in parallel (different methods, same file but independent logic)
- T019-T021 depend on T015-T018 completion

**Phase 4-6 (User Stories 2-4)**:
- US2, US3, US4 can all start in parallel after Foundational completes (if team capacity allows)
- Within each story: tests can run in parallel, implementation tasks have dependencies

**Phase 7 (Polish)**:
- T040, T041, T042, T043, T046 can all run in parallel (different files)
- T044, T045, T047 must be sequential (cleanup before test, test before validation)

---

## Parallel Example: User Story 1

```bash
# Phase 1: Launch all setup tasks together
Task T002: "Update pyproject.toml"
Task T003: "Update .env.example"
Task T004: "Create test fixtures directory"
Task T005: "Create mock_secrets.json"
Task T006: "Create mock_auth_responses.json"

# Phase 3: Launch all tests for User Story 1 together
Task T010: "Contract test for InfisicalClient.get_secret()"
Task T011: "Contract test for InfisicalClient.get_all_secrets()"
Task T012: "Contract test for InfisicalClient.is_connected()"
Task T013: "Integration test for Settings with Infisical"
Task T014: "Integration test for three-tier fallback"

# Phase 3: Launch InfisicalClient methods together (after tests fail)
Task T015: "Implement InfisicalClient class with get_secret"
Task T016: "Implement get_all_secrets() method"
Task T017: "Implement refresh_cache() method"
Task T018: "Implement is_connected() method"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T009) - CRITICAL
3. Complete Phase 3: User Story 1 (T010-T021)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Run `uv run collabiq verify-infisical`
   - Verify logs show "Retrieved X from infisical"
   - Test .env fallback by disabling Infisical
5. Deploy/demo if ready ✅ **MVP Complete**

**MVP Scope**: T001-T021 (21 tasks) delivers fully functional secret retrieval from Infisical

### Incremental Delivery

1. Complete Setup + Foundational (T001-T009) → Foundation ready
2. Add User Story 1 (T010-T021) → Test independently → Deploy/Demo ✅ **MVP!**
3. Add User Story 2 (T022-T027) → Test independently → Deploy/Demo (developer onboarding improved)
4. Add User Story 3 (T028-T033) → Test independently → Deploy/Demo (secret rotation enabled)
5. Add User Story 4 (T034-T039) → Test independently → Deploy/Demo (environment isolation complete)
6. Add Polish (T040-T047) → Final validation → Production-ready ✅ **Feature Complete**

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T009)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T010-T021) - PRIORITY (MVP)
   - **Developer B**: User Story 2 (T022-T027) - Can start in parallel
   - **Developer C**: User Story 4 (T034-T039) - Can start in parallel
3. After US1 complete:
   - **Developer A**: User Story 3 (T028-T033) - Depends on US1
4. After all stories complete:
   - **Team**: Polish (T040-T047) together

**Note**: US3 (Secret Rotation) depends on US1 implementation, so cannot truly start in parallel

---

## Task Summary

**Total Tasks**: 47
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 3 tasks (BLOCKS all user stories)
- **Phase 3 (US1 - P1)**: 12 tasks (7 tests + 5 implementation) ✅ **MVP**
- **Phase 4 (US2 - P2)**: 6 tasks (2 tests + 4 implementation)
- **Phase 5 (US3 - P3)**: 6 tasks (2 tests + 4 implementation)
- **Phase 6 (US4 - P2)**: 6 tasks (2 tests + 4 implementation)
- **Phase 7 (Polish)**: 8 tasks

**Parallel Opportunities**:
- Phase 1: 5 tasks can run in parallel (T002-T006)
- Phase 3: 5 tests can run in parallel (T010-T014), 4 implementation tasks can run in parallel (T015-T018)
- Phase 4-6: User stories can start in parallel after Foundational (US2, US4 independent; US3 depends on US1)
- Phase 7: 5 tasks can run in parallel (T040-T043, T046)

**Independent Test Criteria**:
- **US1**: Application starts with Infisical, retrieves all secrets, logs show "Retrieved X from infisical"
- **US2**: New developer authenticates with machine identity, application starts without manual secret sharing
- **US3**: Secret rotated in Infisical, application uses new value after cache TTL (60s)
- **US4**: Dev environment cannot access prod secrets, authentication fails with clear error

**MVP Scope**: Phase 1-3 (T001-T021, 21 tasks) delivers functional Infisical integration

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability (US1, US2, US3, US4)
- Each user story should be independently completable and testable
- **TDD Required**: Verify tests fail before implementing (T010-T014 before T015-T021)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
