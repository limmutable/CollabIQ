# Data Model: Deploy CollabIQ to Google Cloud

This document outlines the key entities involved in the deployment of the CollabIQ application to Google Cloud, focusing on their conceptual attributes and relationships within the deployment context.

## Key Entities

### 1. Google Cloud Project

**Description**: The fundamental organizational unit within Google Cloud that serves as a container for all Google Cloud resources. It is the top-level entity for managing billing, permissions (IAM), and enabling/disabling Google Cloud services.

**Attributes**:
*   `project_id`: Unique identifier for the Google Cloud project.
*   `project_number`: Numerical identifier for the project.
*   `billing_account`: Associated billing account for resource consumption.
*   `enabled_apis`: List of Google Cloud APIs enabled within the project (e.g., Cloud Run API, Artifact Registry API, Secret Manager API).
*   `service_accounts`: Managed identities used by applications to access Google Cloud resources with specific permissions.

**Relationships**:
*   **Contains**: Deployment Environment, CollabIQ Application (deployed instances), Environment Variables/Secrets (managed via Secret Manager within the project).

### 2. Deployment Environment

**Description**: The specific Google Cloud compute service(s) and associated resources where the CollabIQ application is hosted and executed. Based on research, this will primarily be Google Cloud Run Jobs.

**Attributes**:
*   `service_type`: Type of Google Cloud compute service (e.g., `Cloud Run Job`).
*   `region`: Geographical region where the service is deployed.
*   `service_name`: Name of the deployed Cloud Run Job (e.g., `collabiq-processor`).
*   `container_image`: Reference to the Docker image deployed (from Artifact Registry).
*   `environment_variables`: Non-sensitive configuration passed to the deployed application.
*   `mounted_secrets`: Sensitive secrets securely provided by Secret Manager, potentially mounted as files or environment variables.
*   `persistent_storage_config`: Configuration details for persistent storage (e.g., Cloud Storage bucket name, mount path).

**Relationships**:
*   **Belongs to**: Google Cloud Project.
*   **Hosts**: CollabIQ Application.
*   **Utilizes**: Environment Variables/Secrets, Persistent Storage.

### 3. CollabIQ Application

**Description**: The core Python CLI application, including its source code, dependencies, and runtime configuration, as packaged for deployment.

**Attributes**:
*   `source_code`: Python application files and modules.
*   `dependencies`: List of Python packages required (from `requirements.txt`).
*   `dockerfile`: Instructions for containerizing the application.
*   `runtime_command`: The entrypoint command executed by the deployed service (e.g., `python main.py`).
*   `configuration`: Application-specific settings, some of which are provided via Environment Variables/Secrets.

**Relationships**:
*   **Deployed into**: Deployment Environment.
*   **Requires**: Environment Variables/Secrets.
*   **Interacts with**: Persistent Storage (for data directory), external APIs (Gmail, Notion, LLMs).

### 4. Environment Variables / Secrets

**Description**: Configuration values required for the CollabIQ application to function within the Google Cloud environment. This includes both non-sensitive variables and sensitive API keys/credentials.

**Attributes**:
*   `name`: Key for the environment variable or secret (e.g., `GMAIL_API_KEY`, `NOTION_DATABASE_ID`).
*   `value`: The actual configuration value (masked for secrets).
*   `type`: Indicates if it's an `Environment Variable` (non-sensitive) or `Secret` (sensitive).
*   `source`: Where the value is managed (e.g., `Cloud Run Job configuration`, `Secret Manager`).
*   `access_permissions`: IAM roles defining who can access the secret (if managed by Secret Manager).

**Relationships**:
*   **Configures**: CollabIQ Application.
*   **Managed by**: Google Cloud Project (for environment variables), Google Secret Manager (for secrets).

## Validation Rules

*   A `Google Cloud Project` MUST exist and have billing enabled.
*   The `Deployment Environment` MUST be configured with the necessary Google Cloud APIs enabled (e.g., Cloud Run, Artifact Registry, Secret Manager).
*   The `CollabIQ Application` MUST be containerized using a valid `Dockerfile` and pushed to a `Artifact Registry` repository.
*   All sensitive `Environment Variables / Secrets` MUST be managed via Google Secret Manager.
*   The `Deployment Environment` MUST have appropriate IAM permissions to access secrets from Secret Manager and persistent storage (Cloud Storage).
*   Persistent storage for the CollabIQ data directory MUST be configured and accessible from the `Deployment Environment`.