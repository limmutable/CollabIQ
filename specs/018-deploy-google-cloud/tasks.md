# Tasks: Deploy CollabIQ to Google Cloud

**Feature Branch**: `018-deploy-google-cloud` | **Date**: November 25, 2025 | **Spec**: /specs/018-deploy-google-cloud/spec.md
**Input**: Implementation plan from `/specs/018-deploy-google-cloud/plan.md`, research from `/specs/018-deploy-google-cloud/research.md`, data model from `/specs/018-deploy-google-cloud/data-model.md`, quickstart from `/specs/018-deploy-google-cloud/quickstart.md`.

## Summary

This document outlines the tasks required to create a step-by-step deployment guide for the CollabIQ Python CLI application on Google Cloud, primarily using Cloud Run Jobs, Cloud Storage, and Secret Manager. The tasks are structured to guide a user with no prior server-side deployment experience through the process, ensuring a smooth setup and operation.

## Phase 1: Setup - Google Cloud & Local Tools

Goal: Prepare the Google Cloud environment and local machine with necessary tools.

- [ ] T001 Document Google Cloud account and project setup, including enabling billing, in `docs/deployment/google-cloud-guide.md`.
- [ ] T002 Document `gcloud CLI` installation, initialization, and Docker Desktop installation in `docs/deployment/google-cloud-guide.md`.
- [ ] T003 Document enabling necessary Google Cloud APIs (Cloud Run, Artifact Registry, Secret Manager) in `docs/deployment/google-cloud-guide.md`.

## Phase 2: Foundational - Containerization

Goal: Prepare the CollabIQ application for containerized deployment.

- [ ] T004 Create a `Dockerfile` in the project root (`./Dockerfile`) that containerizes the CollabIQ application, ensuring Python 3.12+ and `uv` are used for dependencies.
- [ ] T005 Document the `Dockerfile` creation and its purpose in `docs/deployment/google-cloud-guide.md`.
- [ ] T006 Document setting up Google Artifact Registry (creating repository, configuring Docker auth) in `docs/deployment/google-cloud-guide.md`.
- [ ] T007 Document building the Docker image and pushing it to Artifact Registry in `docs/deployment/google-cloud-guide.md`.

## Phase 3: User Story 1 - Deploy CollabIQ to Google Cloud (Priority: P1)

Goal: Successfully deploy the CollabIQ application to Google Cloud Run Jobs.

Independent Test: A user can follow the provided documentation to successfully deploy CollabIQ to a Google Cloud environment, and the deployed application processes emails as expected. This can be fully tested by verifying the operational status of the deployed application and its ability to perform core functions.

- [ ] T008 [US1] Document deploying the containerized CollabIQ application as a Cloud Run Job, including example `gcloud run jobs create` command with image, region, command, and args, in `docs/deployment/google-cloud-guide.md`.
- [ ] T009 [US1] Document configuring non-sensitive environment variables for the Cloud Run Job using `--set-env-vars` in `docs/deployment/google-cloud-guide.md`.
- [ ] T010 [US1] Document setting up Google Secret Manager for sensitive data (creating secrets, granting IAM permissions to service account) in `docs/deployment/google-cloud-guide.md`.
- [ ] T011 [US1] Document integrating Google Secret Manager secrets with the Cloud Run Job using `--set-secrets` (or mounting secrets as files) in `docs/deployment/google-cloud-guide.md`.
- [ ] T012 [US1] Document configuring persistent storage for CollabIQ's `data/` directory using Google Cloud Storage (creating bucket, mounting via Cloud Storage FUSE or programmatic access) in `docs/deployment/google-cloud-guide.md`.
- [ ] T013 [US1] Document instructions on how to execute the deployed Cloud Run Job and verify its output/logs in `docs/deployment/google-cloud-guide.md`.

## Final Phase: Polish & Cross-Cutting Concerns

Goal: Ensure the deployment guide is comprehensive, user-friendly, and addresses potential issues.

- [ ] T014 Review `docs/deployment/google-cloud-guide.md` for clarity, completeness, and adherence to user's experience level, making sure all steps are detailed.
- [ ] T015 Add a troubleshooting section to `docs/deployment/google-cloud-guide.md` addressing common Google Cloud API permission errors, conflicting configurations, and billing issues (derived from Edge Cases in spec.md).
- [ ] T016 Document guidance on monitoring the Cloud Run Job via Google Cloud Logging and Cloud Monitoring in `docs/deployment/google-cloud-guide.md`.
- [ ] T017 Add a section on cost optimization for Google Cloud services used in `docs/deployment/google-cloud-guide.md`.
- [ ] T018 Document a plan for future application updates and redeployments in `docs/deployment/google-cloud-guide.md` (e.g., updating Docker image, rolling out new Cloud Run Job revisions).
- [ ] T019 Document or create utility scripts for common maintenance tasks (e.g., `deploy.sh` for redeployment, `status.sh` for checking job status) in `scripts/deployment/` and describe their usage in `docs/deployment/google-cloud-guide.md`.
- [ ] T020 Document how to monitor the running status and history of the CollabIQ Cloud Run Job, including links to Cloud Monitoring dashboards and relevant `gcloud` logging commands, in `docs/deployment/google-cloud-guide.md`.

## Dependencies

- Phase 1 (Setup) -> Phase 2 (Foundational)
- Phase 2 (Foundational) -> Phase 3 (User Story 1)
- Phase 3 (User Story 1) -> Final Phase (Polish & Cross-Cutting Concerns)

## Parallel Execution Examples

- **User Story 1**: Tasks T008 through T013 are generally sequential for a single deployment, but parts of the documentation could be drafted in parallel if specific sections (e.g., secrets vs. storage) are worked on by different contributors. However, for a single user following instructions, they are sequential.

## Implementation Strategy

The implementation will follow an MVP-first approach, focusing on delivering a working deployment guide for User Story 1 (deploying CollabIQ to Google Cloud) as the initial deliverable. Subsequent iterations, if any, could refine or expand on specific deployment aspects. The guide will be incrementally built and refined based on the structured tasks.