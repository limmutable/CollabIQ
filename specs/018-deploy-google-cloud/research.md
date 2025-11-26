# Research: Deploy CollabIQ to Google Cloud

## Decisions and Rationale

### 1. Google Cloud Compute Service Recommendation (FR-007)

*   **Decision**: Google Cloud Run Jobs
*   **Rationale**: Cloud Run Jobs is a fully managed, serverless platform ideal for running containerized tasks to completion, which perfectly suits the nature of a Python CLI application like CollabIQ. It offers significant advantages in ease of use (no infrastructure to manage), cost-effectiveness (pay-per-use, scales to zero when idle, generous free tier), and automatic scaling. This aligns well with the user's preference for Google platforms and their lack of server-side deployment experience.
*   **Alternatives Considered**:
    *   **Cloud Functions**: While serverless and cost-effective, Cloud Functions are more suited for event-driven, short-lived tasks and offer less flexibility for general containerized CLI app functionalities compared to Cloud Run Jobs.
    *   **App Engine (Standard/Flexible)**: App Engine offers PaaS benefits but the Standard environment can be restrictive, and the Flexible environment incurs costs for minimum instances, making it less cost-effective for intermittent CLI usage than Cloud Run.
    *   **Compute Engine (VMs)**: Provides maximum control but comes with the highest operational overhead, requiring manual management of VMs, operating systems, and scaling. This is not ideal for a user without prior deployment experience and for an intermittent CLI application.

### 2. Persistent Storage for CollabIQ's Data Directory (FR-008)

*   **Decision**: Google Cloud Storage (Object Storage).
*   **Rationale**: CollabIQ uses file-based JSON for extractions, caching, and metrics. Cloud Run's local filesystem is ephemeral, so persistent storage must be external. Cloud Storage is a highly scalable, durable, and cost-effective object storage solution that integrates well with Cloud Run. Data can be accessed either by mounting a Cloud Storage bucket as a volume using Cloud Storage FUSE (to provide a file-system-like interface) or by using the `google-cloud-storage` Python client library directly within the application code.
*   **Alternatives Considered**:
    *   **Persistent Disks**: Primarily designed for Compute Engine VMs; not directly applicable or efficient for Cloud Run's stateless nature.
    *   **Cloud SQL / Cloud Firestore**: These are database services (relational and NoSQL, respectively) and would require a significant refactoring of CollabIQ's existing file-based data handling, which is out of scope for a deployment task.
    *   **Google Cloud Filestore**: A managed NFS service, potentially overkill and more expensive for simple file storage needs, especially for a single application instance on Cloud Run.

### 3. Environment Variables and Secrets Management (FR-006)

*   **Decision**:
    *   **Environment Variables (non-sensitive configuration)**: Set directly during Cloud Run Job deployment using the `gcloud CLI` (`--set-env-vars` flag) or via a YAML configuration file.
    *   **Secrets (sensitive data like API keys)**: Utilize Google Secret Manager. Secrets can be securely injected into Cloud Run Jobs as environment variables or mounted as files, or accessed programmatically using the `google-cloud-secret-manager` Python client library.
*   **Rationale**: This approach ensures a secure and managed way to handle both sensitive and non-sensitive configuration data. Secret Manager provides centralized storage, fine-grained access control (IAM), automatic versioning, audit logging, and rotation capabilities, which are crucial for security best practices. Directly embedding secrets in code or configuration files (e.g., Dockerfile) is explicitly avoided.
*   **Alternatives Considered**: Hardcoding secrets or storing them in plain text configuration files (like `app.yaml` or `Dockerfile`) is not secure and violates best practices.

## Deployment Approach Overview

The step-by-step deployment guide for CollabIQ to Google Cloud will focus on Google Cloud Run Jobs. It will cover:

1.  **Prerequisites**: Google Cloud Account, `gcloud CLI` installation and initialization, Docker installation.
2.  **Application Preparation**: Ensuring the Python CLI app is structured with `requirements.txt`.
3.  **Containerization (Dockerfile)**: Creating a `Dockerfile` to package the Python application and its dependencies.
4.  **Artifact Registry**: Building the Docker image and pushing it to Google Cloud Artifact Registry.
5.  **Cloud Run Job Deployment**: Deploying the containerized application as a Cloud Run Job, including configuration for environment variables and integration with Secret Manager for sensitive data.
6.  **Job Execution and Monitoring**: Instructions on how to execute the Cloud Run Job and view logs in Cloud Logging.
7.  **Persistent Storage Configuration**: Guidance on setting up Cloud Storage for persistent data. 

This approach provides a clear, manageable path for users new to server-side deployments while adhering to Google Cloud best practices for serverless applications and security.