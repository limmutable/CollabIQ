# Quickstart: Deploy CollabIQ to Google Cloud

This guide provides a high-level overview of the steps required to deploy the CollabIQ Python CLI application to Google Cloud, primarily leveraging Google Cloud Run Jobs for serverless execution. Detailed instructions will be provided in the main deployment documentation.

## 1. Prerequisites

Before you begin, ensure you have:

*   A **Google Cloud Account** with an active project and billing enabled.
*   The **Google Cloud CLI (`gcloud CLI`)** installed and initialized on your local machine, configured to your target Google Cloud project.
*   **Docker Desktop** (or Docker Engine) installed to build container images.
*   Your **CollabIQ application** ready for deployment, including a `requirements.txt` file listing all Python dependencies.

## 2. Prepare Your CollabIQ Application

1.  **Organize Project**: Ensure your CollabIQ project has a clear structure, with your main application logic and `requirements.txt` file.
2.  **Create Dockerfile**: In your project's root directory, create a `Dockerfile` that specifies how to build a Docker image for your Python application. This typically involves defining a base Python image, setting a working directory, copying your application code, installing dependencies, and defining the entrypoint command.

    ```dockerfile
    # Example Dockerfile
    FROM python:3.12-slim-bookworm
    WORKDIR /app
    COPY . /app
    RUN uv sync --system-type=manylinux --python-version=3.12 --target-kind=sdist
    ENTRYPOINT ["uv", "run", "collabiq"]
    ```

## 3. Containerize and Push to Artifact Registry

1.  **Enable Artifact Registry API**: `gcloud services enable artifactregistry.googleapis.com`
2.  **Create Repository**: Create a Docker repository in Google Cloud Artifact Registry.
    `gcloud artifacts repositories create [REPO_NAME] --repository-format=docker --location=[REGION] --description="Docker repository for CollabIQ"`
3.  **Configure Docker Auth**: Configure Docker to authenticate to Artifact Registry.
    `gcloud auth configure-docker [REGION]-docker.pkg.dev`
4.  **Build Image**: Build your Docker image locally.
    `docker build -t [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/collabiq:[TAG] .`
5.  **Push Image**: Push the built Docker image to Artifact Registry.
    `docker push [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/collabiq:[TAG]`

## 4. Deploy to Google Cloud Run Jobs

1.  **Enable Cloud Run API**: `gcloud services enable run.googleapis.com`
2.  **Deploy Job**: Deploy your containerized CollabIQ application as a Cloud Run Job.

    ```bash
    gcloud run jobs create collabiq-processor \
        --image [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/collabiq:[TAG] \
        --region [REGION] \
        --command uv \
        --args run,collabiq,email,fetch,--limit,5 \
        --set-env-vars GMAIL_CREDENTIALS_PATH=/etc/secrets/gmail-creds.json \
        --set-secrets GMAIL_API_KEY=my-gmail-api-key:latest \
        --max-retries 2 \
        --task-timeout 600s # 10 minutes
    ```
    *   **Environment Variables**: Use `--set-env-vars` for non-sensitive configuration.
    *   **Secrets**: Integrate with Google Secret Manager using `--set-secrets` to securely inject sensitive data.

## 5. Persistent Storage with Cloud Storage

CollabIQ uses a `data/` directory for caching and extractions. For persistence on Cloud Run, you will need to configure Google Cloud Storage.

1.  **Create a Cloud Storage Bucket**: Create a bucket to store CollabIQ's data.
    `gsutil mb -p [PROJECT_ID] gs://collabiq-data-bucket-[UNIQUE_SUFFIX]`
2.  **Access from Cloud Run**: You can either:
    *   **Mount via Cloud Storage FUSE**: This requires additional configuration on Cloud Run to mount the bucket as a local filesystem path (e.g., `/app/data`).
    *   **Programmatic Access**: Modify CollabIQ to use the `google-cloud-storage` Python client library to read/write files directly to the bucket.

## 6. Manage Secrets with Google Secret Manager

For sensitive data like API keys (e.g., Gmail, Notion, LLM providers) and credentials, use Google Secret Manager.

1.  **Enable Secret Manager API**: `gcloud services enable secretmanager.googleapis.com`
2.  **Create Secrets**: Create individual secrets for each sensitive piece of information.
    `echo -n "your-api-key-value" | gcloud secrets create my-gmail-api-key --data-file=-`
3.  **Grant Permissions**: Ensure the Cloud Run Job's service account has the "Secret Manager Secret Accessor" role on your secrets.

## 7. Execution and Monitoring

*   **Execute Job**: Trigger your Cloud Run Job manually or on a schedule.
    `gcloud run jobs execute collabiq-processor --region [REGION]`
*   **View Logs**: All application logs (`print()` statements) are sent to Google Cloud Logging. View them in the Google Cloud Console or using `gcloud logging read`.

This quickstart provides a foundation. Refer to the detailed deployment guide for comprehensive instructions.
