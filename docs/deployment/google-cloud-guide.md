# CollabIQ Google Cloud Deployment Guide

This guide walks you through deploying CollabIQ to Google Cloud Run. No prior cloud deployment experience is required.

**Table of Contents:**
- [Prerequisites & Google Cloud Account Setup](#prerequisites--google-cloud-account-setup)
- [Local Tools Installation](#local-tools-installation)
- [Enable Required Google Cloud APIs](#enable-required-google-cloud-apis)
- [Phase 2: Containerization](#phase-2-containerization)
- [Phase 3: Cloud Run Job Deployment](#phase-3-cloud-run-job-deployment)
- [Troubleshooting](#troubleshooting)
- [Monitoring and Logging](#monitoring-and-logging)
- [Cost Optimization](#cost-optimization)
- [Update and Redeployment](#update-and-redeployment)
- [Quick Reference](#quick-reference)

---

## Prerequisites & Google Cloud Account Setup

### Creating a Google Cloud Account

If you don't have a Google Cloud account:

1. **Visit Google Cloud Console**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Sign in with your Google account (Gmail)

2. **Accept Terms of Service**
   - Review and accept the Google Cloud Platform Terms of Service
   - New users get $300 in free credits (valid for 90 days)

3. **Set Up Billing**
   - Click "Activate" to set up your billing account
   - Enter your payment information (required even for free tier)
   - **Note:** You won't be charged until you explicitly upgrade to a paid account

### Creating a New Google Cloud Project

Every Google Cloud deployment lives in a project. Here's how to create one:

1. **Navigate to Project Selection**
   - In the Google Cloud Console, click the project dropdown in the top navigation bar
   - Click "New Project"

2. **Configure Project Settings**
   - **Project Name:** Use a descriptive name (e.g., `collabiq-production` or `collabiq-dev`)
   - **Project ID:** Auto-generated or customize (must be globally unique)
     - Example: `collabiq-prod-12345`
     - This ID is permanent and cannot be changed
   - **Organization:** Leave as "No organization" (unless you have a Google Workspace)
   - Click "Create"

3. **Wait for Project Creation**
   - Project creation takes 10-30 seconds
   - You'll receive a notification when complete

### Best Practices for Project Naming and Organization

**Naming Conventions:**
```
Environment-based naming:
  - collabiq-dev-[unique-suffix]
  - collabiq-staging-[unique-suffix]
  - collabiq-prod-[unique-suffix]

User-based naming (for personal projects):
  - collabiq-[yourname]-dev
  - collabiq-[yourname]-prod
```

**Project Organization Tips:**
- **Separate Environments:** Create separate projects for development, staging, and production
- **Consistent Naming:** Use consistent prefixes across all your projects
- **Document Project IDs:** Save your project IDs in a secure location (you'll need them frequently)
- **Budget Alerts:** Set up budget alerts for each project (covered in Cost Optimization section)

**Important Notes:**
- Project IDs are globally unique across all Google Cloud users
- Once created, a project ID cannot be changed
- Deleting a project has a 30-day recovery period before permanent deletion

---

## Local Tools Installation

Before deploying to Google Cloud, you need to install two essential tools on your local machine:
1. **gcloud CLI** - Command-line interface for Google Cloud
2. **Docker Desktop** - Container platform for building images

### gcloud CLI Installation

The Google Cloud CLI (`gcloud`) allows you to manage Google Cloud resources from your terminal.

#### macOS Installation

**Option 1: Homebrew (Recommended for Apple Silicon)**
```bash
# Install gcloud CLI
brew install --cask google-cloud-sdk

# Add gcloud to your PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"' >> ~/.zshrc
echo 'source "$(brew --prefix)/share/google-cloud-sdk/completion.zsh.inc"' >> ~/.zshrc

# Reload shell configuration
source ~/.zshrc
```

**Option 2: Manual Installation**
```bash
# Download the installer
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz

# For Intel Macs, use this URL instead:
# curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-x86_64.tar.gz

# Extract the archive
tar -xf google-cloud-cli-darwin-arm.tar.gz

# Run the install script
./google-cloud-sdk/install.sh

# Follow the prompts:
# - Accept default installation location
# - Yes to updating PATH
# - Yes to command completion

# Restart your terminal or run:
source ~/.zshrc
```

#### Linux Installation

```bash
# Add the Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the Cloud SDK
sudo apt-get update && sudo apt-get install google-cloud-cli
```

#### Windows Installation

1. Download the installer from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
2. Run the `.exe` installer
3. Follow the installation wizard
4. Check "Start Google Cloud SDK Shell" when installation completes
5. The installer will open a terminal and run initialization

**Windows Note:** Use PowerShell or Command Prompt (not Git Bash) for gcloud commands.

#### Initializing gcloud CLI

After installation, initialize gcloud to authenticate and configure defaults:

```bash
# Initialize gcloud (opens browser for authentication)
gcloud init

# Follow the prompts:
# 1. Log in with your Google account
# 2. Select or create a Google Cloud project
# 3. Choose a default compute region (recommend: us-central1)
```

**Alternative: Initialize without browser (for remote servers)**
```bash
gcloud init --console-only
```

#### Setting Default Project

After initialization, set your CollabIQ project as the default:

```bash
# List all your projects
gcloud projects list

# Set default project (replace with your project ID)
gcloud config set project collabiq-prod-12345

# Verify configuration
gcloud config list
```

**Expected Output:**
```
[core]
account = your.email@gmail.com
disable_usage_reporting = False
project = collabiq-prod-12345

Your active configuration is: [default]
```

#### Verifying Installation

Test that gcloud is properly installed and authenticated:

```bash
# Check gcloud version
gcloud version

# Verify authentication
gcloud auth list

# Test API access
gcloud projects describe $(gcloud config get-value project)
```

**Expected Output for Version Check:**
```
Google Cloud SDK 456.0.0
bq 2.0.101
core 2024.01.01
gcloud-crc32c 1.0.0
gsutil 5.27
```

**Common Installation Issues:**

**Issue:** `gcloud: command not found`
- **Solution:** Ensure gcloud is in your PATH. Restart your terminal or run:
  ```bash
  source ~/.zshrc  # macOS/Linux
  ```

**Issue:** `ERROR: (gcloud.init) Unable to find project`
- **Solution:** Make sure you created a project in Google Cloud Console first

**Issue:** Authentication browser window doesn't open
- **Solution:** Use `gcloud auth login --no-launch-browser` and follow the manual authentication flow

---

### Docker Desktop Installation

Docker is required to build container images for Cloud Run deployment.

#### macOS Installation

**For Apple Silicon (M1/M2/M3 Macs):**
```bash
# Option 1: Homebrew
brew install --cask docker

# Option 2: Manual Download
# Visit: https://desktop.docker.com/mac/main/arm64/Docker.dmg
# Download and install Docker.dmg
```

**For Intel Macs:**
```bash
# Option 1: Homebrew
brew install --cask docker

# Option 2: Manual Download
# Visit: https://desktop.docker.com/mac/main/amd64/Docker.dmg
# Download and install Docker.dmg
```

**After Installation:**
1. Open Docker Desktop from Applications
2. Accept the service agreement
3. Wait for Docker to start (whale icon in menu bar)
4. Docker is ready when the whale icon is static (not animated)

#### Linux Installation (Docker Engine)

**Ubuntu/Debian:**
```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Set up Docker repository
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group (avoid using sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

**Fedora/RHEL/CentOS:**
```bash
# Install Docker using dnf
sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
```

#### Windows Installation

1. **System Requirements:**
   - Windows 10/11 64-bit (Pro, Enterprise, or Education)
   - Hyper-V and Containers Windows features enabled
   - WSL 2 installed

2. **Install WSL 2 (if not already installed):**
   ```powershell
   # Run in PowerShell as Administrator
   wsl --install
   ```

3. **Install Docker Desktop:**
   - Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Run the installer
   - Ensure "Use WSL 2 instead of Hyper-V" is checked
   - Restart your computer when prompted

4. **Configure WSL 2 Integration:**
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration with your WSL 2 distros

#### Verifying Docker Installation

Test that Docker is properly installed and running:

```bash
# Check Docker version
docker --version

# Verify Docker is running
docker ps

# Run hello-world test
docker run hello-world
```

**Expected Output for `docker --version`:**
```
Docker version 24.0.7, build afdd53b
```

**Expected Output for `docker run hello-world`:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

**Common Docker Installation Issues:**

**Issue:** `Cannot connect to the Docker daemon`
- **macOS:** Make sure Docker Desktop is running (check menu bar)
- **Linux:** Start Docker service: `sudo systemctl start docker`
- **Windows:** Ensure WSL 2 is running and Docker Desktop is started

**Issue:** `permission denied while trying to connect to the Docker daemon socket`
- **Linux:** You need to add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker  # Or log out and back in
  ```

**Issue:** Docker Desktop won't start on macOS
- **Solution:** Reset Docker Desktop from Troubleshoot → Reset to factory defaults

**Issue:** WSL 2 not enabled (Windows)
- **Solution:** Run in PowerShell as Administrator:
  ```powershell
  dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
  dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
  ```

---

## Enable Required Google Cloud APIs

Google Cloud services are accessed through APIs that must be explicitly enabled for each project.

### APIs Required for CollabIQ

CollabIQ requires three Google Cloud APIs:

1. **Cloud Run API** (`run.googleapis.com`)
   - Serverless container deployment platform
   - Used to host the CollabIQ daemon

2. **Artifact Registry API** (`artifactregistry.googleapis.com`)
   - Docker container image storage
   - Used to store your CollabIQ Docker images

3. **Secret Manager API** (`secretmanager.googleapis.com`)
   - Secure storage for sensitive configuration
   - Used to store API keys and credentials

### Enable All APIs at Once

The fastest way to enable all required APIs:

```bash
# Enable all CollabIQ-required APIs in one command
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

**Expected Output:**
```
Operation "operations/acf.p2-123456789-abcd-ef01-2345-6789abcdef01" finished successfully.
```

**Note:** Enabling APIs can take 30-60 seconds. You only need to do this once per project.

### Enable APIs Individually

If you prefer to enable APIs one at a time:

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com
```

### Verify APIs are Enabled

Check which APIs are currently enabled:

```bash
# List all enabled APIs
gcloud services list --enabled

# Check specific APIs
gcloud services list --enabled --filter="name:(run.googleapis.com OR artifactregistry.googleapis.com OR secretmanager.googleapis.com)"
```

**Expected Output:**
```
NAME                              TITLE
artifactregistry.googleapis.com   Artifact Registry API
run.googleapis.com                Cloud Run Admin API
secretmanager.googleapis.com      Secret Manager API
```

### Enable APIs via Google Cloud Console (Alternative Method)

If you prefer using the web interface:

1. **Navigate to APIs & Services**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Click "APIs & Services" → "Library" in the left sidebar

2. **Search and Enable Each API:**
   - Search for "Cloud Run API" → Click → Enable
   - Search for "Artifact Registry API" → Click → Enable
   - Search for "Secret Manager API" → Click → Enable

3. **Verify Enablement**
   - Go to "APIs & Services" → "Dashboard"
   - You should see all three APIs listed

### Common Permission Issues and Solutions

**Issue:** `ERROR: (gcloud.services.enable) User [user@example.com] does not have permission to access project`
- **Cause:** You don't have sufficient permissions on the project
- **Solution:**
  - Ensure you're using the correct project: `gcloud config get-value project`
  - Verify you're logged in: `gcloud auth list`
  - If someone else owns the project, ask them to grant you "Editor" or "Owner" role:
    ```bash
    gcloud projects add-iam-policy-binding PROJECT_ID \
      --member="user:YOUR_EMAIL" \
      --role="roles/editor"
    ```

**Issue:** `ERROR: (gcloud.services.enable) The project is not linked to a billing account`
- **Cause:** Billing is not enabled for the project
- **Solution:**
  - Go to [console.cloud.google.com/billing](https://console.cloud.google.com/billing)
  - Select your project
  - Link it to a billing account (even free tier requires billing setup)

**Issue:** API enable command times out
- **Cause:** Network issues or temporary Google Cloud outage
- **Solution:**
  - Wait 1-2 minutes and try again
  - Check Google Cloud Status: [status.cloud.google.com](https://status.cloud.google.com)

**Issue:** `Service 'run.googleapis.com' not found`
- **Cause:** Typo in API name or invalid project
- **Solution:**
  - Double-check the API name (case-sensitive)
  - Verify project is set: `gcloud config list project`

### Understanding API Quotas and Limits

Each Google Cloud API has quotas and rate limits:

**Default Quotas for New Projects:**
- **Cloud Run:** 1,000 requests per second per region
- **Artifact Registry:** 50 GB storage (free tier)
- **Secret Manager:** 6 secret versions per secret (free tier)

**View Current Quotas:**
```bash
# View quotas for Cloud Run
gcloud compute project-info describe --project=$(gcloud config get-value project)
```

**Note:** For most CollabIQ deployments, default quotas are more than sufficient. Enterprise users may need to request quota increases.

---

## Phase 2: Containerization

Containerization packages CollabIQ and its dependencies into a portable Docker image that can run consistently anywhere. This section explains the existing Dockerfile, how to build your image, and how to push it to Google Artifact Registry.

### Understanding the Dockerfile

CollabIQ includes a production-ready Dockerfile at `/Users/jlim/Projects/CollabIQ/Dockerfile`. Let's break down what each section does:

#### Base Image Selection
```dockerfile
FROM python:3.12-slim-bookworm AS base
```
- **python:3.12-slim-bookworm**: Debian-based minimal Python image
- **Why slim?** Smaller size (130 MB vs 1 GB for full Python image)
- **Why bookworm?** Latest stable Debian release with security updates
- **AS base**: Named stage for potential multi-stage builds

#### Environment Configuration
```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:$PATH"
```
- **PYTHONUNBUFFERED=1**: Python outputs directly to terminal (essential for Docker logs)
- **PYTHONDONTWRITEBYTECODE=1**: Skip .pyc file generation (reduces image size)
- **UV_SYSTEM_PYTHON=1**: Tell UV to use system Python instead of creating venv
- **PATH update**: Ensures UV binaries are accessible

#### System Dependencies
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```
- **curl**: Required to download UV installer
- **ca-certificates**: Needed for HTTPS connections to APIs
- **--no-install-recommends**: Skip unnecessary packages (reduces size)
- **rm -rf /var/lib/apt/lists/**: Clean up package manager cache

#### UV Package Manager Installation
```dockerfile
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
```
- Installs UV directly in the container
- UV provides fast, reliable dependency management
- Alternative to pip with better performance

#### Layer Caching Strategy
```dockerfile
WORKDIR /app
COPY pyproject.toml ./
COPY uv.lock* ./

RUN uv sync --frozen --no-dev --no-install-project
```
- **Why copy pyproject.toml first?** Docker caches layers; dependencies rarely change
- **uv.lock***: Copies lockfile if it exists (ensures reproducible builds)
- **--frozen**: Use exact versions from lockfile (no updates)
- **--no-dev**: Skip development dependencies (testing, linting tools)
- **--no-install-project**: Install dependencies only, not the project yet

#### Application Code
```dockerfile
COPY src/ ./src/
COPY README.md ./
RUN uv sync --frozen --no-dev
```
- Copy source code **after** installing dependencies (better caching)
- Second `uv sync` installs the CollabIQ package itself
- Changing code doesn't rebuild dependency layer

#### Runtime Directories
```dockerfile
RUN mkdir -p /app/credentials /app/data /app/logs
```
- **/app/credentials**: For mounted Gmail/Notion credentials
- **/app/data**: For state files (daemon state, caches)
- **/app/logs**: For application logs

#### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run collabiq config validate || exit 1
```
- **interval=30s**: Check health every 30 seconds
- **timeout=10s**: Fail if check takes longer than 10 seconds
- **start-period=5s**: Wait 5 seconds before first check (allow startup)
- **retries=3**: Declare unhealthy after 3 consecutive failures
- **Command**: Runs `collabiq config validate` to verify configuration

#### Entrypoint Configuration
```dockerfile
ENTRYPOINT ["uv", "run", "collabiq"]
CMD ["--help"]
```
- **ENTRYPOINT**: Always runs `uv run collabiq`
- **CMD**: Default argument (shows help if no command specified)
- **Example usage**: `docker run collabiq:latest daemon start` runs `uv run collabiq daemon start`

#### Benefits of This Dockerfile Design

1. **Small Image Size**: ~250 MB (vs 1+ GB for naive Dockerfiles)
2. **Fast Builds**: Layer caching means rebuilds only process changed code
3. **Reproducible**: Locked dependencies ensure consistent environments
4. **Production-Ready**: No dev dependencies or unnecessary tools
5. **Health Monitoring**: Built-in health checks for Cloud Run
6. **Secure**: Minimal attack surface with slim base image

---

### Setting Up Google Artifact Registry

Artifact Registry is Google Cloud's Docker image storage service. It's more secure and better integrated than Docker Hub for GCP deployments.

#### Creating a Docker Repository

Create a dedicated repository for CollabIQ images:

```bash
# Create repository in us-central1 region
gcloud artifacts repositories create collabiq-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="CollabIQ Docker images"
```

**Command Breakdown:**
- **collabiq-repo**: Repository name (customize as needed)
- **--repository-format=docker**: Specifies Docker image format
- **--location=us-central1**: Choose region (use same region as Cloud Run deployment)
- **--description**: Optional human-readable description

**Expected Output:**
```
Create request issued for: [collabiq-repo]
Waiting for operation [projects/PROJECT_ID/locations/us-central1/operations/abc123] to complete...done.
Created repository [collabiq-repo].
```

**Region Selection Tips:**
- **us-central1** (Iowa): Good default, low-cost, reliable
- **us-east1** (South Carolina): Low latency for East Coast
- **us-west1** (Oregon): Low latency for West Coast
- **Use same region** as your Cloud Run deployment for faster pulls

#### Verify Repository Creation

List all Artifact Registry repositories:

```bash
# List all repositories
gcloud artifacts repositories list

# Filter for Docker repositories only
gcloud artifacts repositories list --filter="format:docker"
```

**Expected Output:**
```
REPOSITORY       FORMAT  LOCATION      DESCRIPTION
collabiq-repo    DOCKER  us-central1   CollabIQ Docker images
```

#### Configuring Docker Authentication

Before pushing images, configure Docker to authenticate with Artifact Registry:

```bash
# Configure Docker authentication for us-central1 region
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**Expected Output:**
```
Adding credentials for: us-central1-docker.pkg.dev
After update, the following will be written to your Docker config file located at [/Users/yourname/.docker/config.json]:
{
  "credHelpers": {
    "us-central1-docker.pkg.dev": "gcloud"
  }
}

Do you want to continue (Y/n)? Y

Docker configuration file updated.
```

**What This Does:**
- Adds `us-central1-docker.pkg.dev` to Docker's credential helpers
- Tells Docker to use `gcloud` for authentication to this registry
- You only need to do this once per machine

**For Multiple Regions:**
If you use multiple regions, add them all:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev,us-east1-docker.pkg.dev
```

#### Verify Authentication

Test that Docker can authenticate to Artifact Registry:

```bash
# Verify Docker can access Artifact Registry
docker pull us-central1-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0
```

**Note:** This pulls a public test image to verify connectivity. If this succeeds, your authentication is working.

---

### Building and Pushing Docker Image

Now you're ready to build the CollabIQ Docker image and push it to Artifact Registry.

#### Understanding Image Tags

Docker images use a naming convention:
```
REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME/IMAGE_NAME:TAG
```

**Example:**
```
us-central1-docker.pkg.dev/collabiq-prod-12345/collabiq-repo/collabiq:v1.0.0
```

**Components:**
- **us-central1-docker.pkg.dev**: Artifact Registry region endpoint
- **collabiq-prod-12345**: Your Google Cloud project ID
- **collabiq-repo**: Repository name (created earlier)
- **collabiq**: Image name
- **v1.0.0**: Version tag

**Recommended Tagging Strategy:**

1. **Semantic Versions**: `v1.0.0`, `v1.0.1`, `v1.1.0`
2. **Git Commit Hash**: `abc1234` (for traceability)
3. **Environment Tags**: `dev`, `staging`, `prod`
4. **Latest Tag**: `latest` (always points to most recent build)

**Example Multi-Tag Build:**
```bash
# Tag with version, commit hash, and latest
docker build -t collabiq:v1.0.0 .
docker tag collabiq:v1.0.0 collabiq:latest
docker tag collabiq:v1.0.0 collabiq:abc1234
```

#### Building the Docker Image Locally

Navigate to your CollabIQ project and build the image:

```bash
# Navigate to project directory
cd /Users/jlim/Projects/CollabIQ

# Set your project ID (replace with your actual project ID)
export PROJECT_ID=$(gcloud config get-value project)


# Build the Docker image
docker build -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest .
```

**Expected Output:**
```
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.12-slim-bookworm
 => [base 1/8] FROM docker.io/library/python:3.12-slim-bookworm
 => [base 2/8] RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
 => [base 3/8] RUN curl -LsSf https://astral.sh/uv/install.sh | sh
 => [base 4/8] WORKDIR /app
 => [base 5/8] COPY pyproject.toml ./
 => [base 6/8] COPY uv.lock* ./
 => [base 7/8] RUN uv sync --frozen --no-dev --no-install-project
 => [base 8/8] COPY src/ ./src/
 => [base 9/8] COPY README.md ./
 => [base 10/8] RUN uv sync --frozen --no-dev
 => [base 11/8] RUN mkdir -p /app/credentials /app/data /app/logs
 => exporting to image
 => => exporting layers
 => => writing image sha256:abc123...
 => => naming to us-central1-docker.pkg.dev/PROJECT_ID/collabiq-repo/collabiq:latest
```

**Build Time Expectations:**
- **First build**: 2-5 minutes (downloads base image, installs dependencies)
- **Subsequent builds**: 10-30 seconds (uses cached layers if only code changed)

**Multi-Tag the Image:**
```bash
# Tag with additional versions
docker tag us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest \
           us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:v1.0.0

# Tag with git commit hash (optional but recommended)
GIT_COMMIT=$(git rev-parse --short HEAD)
docker tag us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest \
           us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:${GIT_COMMIT}
```

#### Testing the Image Locally

**Critical: Always test locally before pushing to the cloud!**

Test that the image works correctly:

```bash
# Test help command
docker run --rm us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest --help

# Expected output: CollabIQ help text
```

**Test with Mounted Credentials (Advanced):**
```bash
# Mount your local credentials for testing
docker run --rm \
  -v ~/.config/gcloud/application_default_credentials.json:/app/credentials/gcloud.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcloud.json \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest \
  config validate
```

**Common Test Commands:**
```bash
# Test config validation
docker run --rm collabiq:latest config validate

# Test CLI help
docker run --rm collabiq:latest --help

# Test specific command help
docker run --rm collabiq:latest daemon --help

# Inspect image layers
docker history us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest
```

#### Pushing the Image to Artifact Registry

Push all tags to Artifact Registry:

```bash
# Push latest tag
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest

# Push version tag
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:v1.0.0

# Push commit hash tag (if created)
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:${GIT_COMMIT}
```

**Expected Output:**
```
The push refers to repository [us-central1-docker.pkg.dev/PROJECT_ID/collabiq-repo/collabiq]
abc123: Pushed
def456: Pushed
ghi789: Pushed
v1.0.0: digest: sha256:abc123... size: 1234
```

**Push Time Expectations:**
- **First push**: 1-3 minutes (uploads all layers)
- **Subsequent pushes**: 10-30 seconds (only changed layers)

#### Verifying the Image in Artifact Registry

Confirm your image is available in Artifact Registry:

```bash
# List all images in the repository
gcloud artifacts docker images list us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo

# View specific image tags
gcloud artifacts docker images list us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq
```

**Expected Output:**
```
IMAGE                                                                    DIGEST         CREATE_TIME          UPDATE_TIME
us-central1-docker.pkg.dev/PROJECT_ID/collabiq-repo/collabiq             sha256:abc123  2025-11-27T10:30:00  2025-11-27T10:30:00

TAGS: latest, v1.0.0, abc1234
```

**View in Google Cloud Console:**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Navigate to "Artifact Registry" → "Repositories"
3. Click "collabiq-repo"
4. You should see your `collabiq` image with all tags

---

### Common Build and Push Issues

#### Issue: `docker: command not found`
**Cause:** Docker is not installed or not in PATH

**Solution:**
```bash
# Check Docker installation
docker --version

# If not installed, see "Docker Desktop Installation" section above
```

#### Issue: `denied: Permission "artifactregistry.repositories.uploadArtifacts" denied`
**Cause:** Your gcloud credentials don't have permission to push images

**Solution:**
```bash
# Re-authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Verify gcloud authentication
gcloud auth list

# If needed, re-login
gcloud auth login
```

#### Issue: `ERROR: failed to solve: python:3.12-slim-bookworm: failed to resolve source metadata`
**Cause:** Docker cannot reach Docker Hub (network issue)

**Solution:**
```bash
# Check internet connection
ping google.com

# If behind proxy, configure Docker proxy settings
# Edit ~/.docker/config.json or Docker Desktop settings
```

#### Issue: Build fails with `uv: command not found`
**Cause:** UV installation failed in Dockerfile

**Solution:**
```bash
# Check if curl is available in base image
docker run --rm python:3.12-slim-bookworm curl --version

# If curl missing, add to Dockerfile:
RUN apt-get update && apt-get install -y curl
```

#### Issue: `COPY failed: file not found`
**Cause:** Files referenced in COPY command don't exist

**Solution:**
```bash
# Verify files exist locally
ls pyproject.toml src/ README.md

# Check .dockerignore isn't excluding required files
cat .dockerignore
```

#### Issue: Build is very slow (5+ minutes every time)
**Cause:** Docker not using layer cache

**Solution:**
```bash
# Check if you're modifying files that break cache
# Common culprits: pyproject.toml, uv.lock

# Verify layer cache is working
docker build --progress=plain -t collabiq:test .
# Should show "CACHED" for unchanged layers

# If still slow, try:
docker system prune -a  # Clean up old images
docker builder prune    # Clean build cache
```

#### Issue: Image size is very large (1+ GB)
**Cause:** Including unnecessary files or using wrong base image

**Solution:**
```bash
# Check current image size
docker images | grep collabiq

# Create .dockerignore to exclude:
cat > .dockerignore <<EOF
.git
.venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
tests/
docs/
*.md
.env
credentials/
EOF

# Rebuild
docker build -t collabiq:latest .
```

#### Issue: Push fails with `unauthorized: authentication required`
**Cause:** Docker credentials for Artifact Registry expired or misconfigured

**Solution:**
```bash
# Reconfigure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Verify credential helper is configured
cat ~/.docker/config.json | grep credHelpers

# If needed, manually refresh gcloud credentials
gcloud auth application-default login
```

#### Issue: Health check always fails
**Cause:** `collabiq config validate` requires environment variables

**Solution:**
```bash
# Test health check locally
docker run --rm -e SOME_REQUIRED_VAR=value collabiq:latest config validate

# Or modify Dockerfile to use simpler health check:
HEALTHCHECK CMD python --version || exit 1
```

---

### Best Practices for Production Images

1. **Use .dockerignore**: Exclude unnecessary files to reduce image size
   ```
   .git
   .venv
   __pycache__
   tests/
   docs/
   *.md
   .env
   ```

2. **Pin Dependencies**: Always use `uv.lock` for reproducible builds
   ```dockerfile
   COPY uv.lock ./
   RUN uv sync --frozen
   ```

3. **Multi-Tag Strategy**: Tag images with version, commit, and latest
   ```bash
   docker tag IMAGE:latest IMAGE:v1.0.0
   docker tag IMAGE:latest IMAGE:$(git rev-parse --short HEAD)
   ```

4. **Test Before Pushing**: Always run basic tests locally
   ```bash
   docker run --rm IMAGE:latest --help
   ```

5. **Scan for Vulnerabilities**: Use Docker Scout or Trivy
   ```bash
   docker scout cves IMAGE:latest
   ```

6. **Monitor Image Size**: Keep images under 500 MB for faster deploys
   ```bash
   docker images | grep collabiq
   ```

7. **Use Build Args for Flexibility**: Parameterize builds
   ```dockerfile
   ARG PYTHON_VERSION=3.12
   FROM python:${PYTHON_VERSION}-slim-bookworm
   ```

8. **Document Image Tags**: Keep a changelog of what each tag contains
   ```bash
   # v1.0.0 - Initial release
   # v1.0.1 - Bug fix for daemon mode
   # v1.1.0 - Added Gemini support
   ```

---

## Phase 3: Cloud Run Job Deployment

This section covers deploying CollabIQ as a Cloud Run Job, which is designed for task-based workloads like CLI applications and scheduled jobs.

**Prerequisites:**
- Completed Phase 1 (Tools Installation & API Enablement)
- Completed Phase 2 (Containerization)
- Docker image pushed to Artifact Registry
- Project ID and region configured in gcloud

**Table of Contents:**
- [Why Cloud Run Jobs (Not Services)](#why-cloud-run-jobs-not-services)
- [Deploying as a Cloud Run Job](#deploying-as-a-cloud-run-job)
- [Configuring Environment Variables](#configuring-environment-variables)
- [Setting Up Google Secret Manager](#setting-up-google-secret-manager)
- [Integrating Secrets with Cloud Run Job](#integrating-secrets-with-cloud-run-job)
- [Configuring Persistent Storage](#configuring-persistent-storage)
- [Executing and Verifying the Job](#executing-and-verifying-the-job)

---

### Why Cloud Run Jobs (Not Services)

CollabIQ is a CLI application designed for batch processing (e.g., processing emails periodically), not serving web requests. Here's why Cloud Run Jobs are the right choice:

**Cloud Run Jobs (Recommended for CollabIQ):**
- ✅ Designed for task-based workloads that run to completion
- ✅ Execute on-demand or on a schedule (with Cloud Scheduler)
- ✅ Automatically shut down after task completion (cost-effective)
- ✅ Support for retries and task parallelization
- ✅ No need to keep a web server running

**Cloud Run Services (Not Recommended for CollabIQ):**
- ❌ Designed for web applications that respond to HTTP requests
- ❌ Must continuously listen on a port
- ❌ Incur costs for always-on instances
- ❌ Require HTTP health checks and request handling

**Use Case Comparison:**
```
CollabIQ Workflow:
1. Fetch emails from Gmail
2. Process emails with LLM
3. Update Notion databases
4. Exit when complete

Cloud Run Job: Perfect for this pattern (run → process → exit)
Cloud Run Service: Would require artificial HTTP wrapper
```

---

### Deploying as a Cloud Run Job

#### Basic Job Creation Command

Create a Cloud Run Job to run CollabIQ commands:

```bash
# Set environment variables for convenience
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export JOB_NAME="collabiq-processor"
export IMAGE_URL="us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest"

# Create the Cloud Run Job
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Command Breakdown:**

| Parameter | Description | Example Value |
|-----------|-------------|---------------|
| `--image` | Container image from Artifact Registry | `us-central1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:latest` |
| `--region` | Google Cloud region for deployment | `us-central1` (recommended for most users) |
| `--command` | Entrypoint command (overrides Dockerfile ENTRYPOINT) | `collabiq` |
| `--args` | Command arguments | `run` (single cycle) or `run,--daemon,--interval,5` (continuous) |
| `--max-retries` | Number of retry attempts on failure | `3` (0-10 allowed) |
| `--task-timeout` | Maximum execution time per task | `30m` (format: `1h`, `45m`, `3600s`) |
| `--memory` | Memory allocation | `512Mi` (256Mi-32Gi available) |
| `--cpu` | CPU allocation | `1` (0.5-8 CPUs available) |

**Region Selection Guidance:**

Choose a region based on your location and data residency requirements:

```bash
# North America
us-central1     # Iowa (recommended for US users - lowest latency)
us-east1        # South Carolina
us-west1        # Oregon

# Europe
europe-west1    # Belgium (recommended for EU users)
europe-west4    # Netherlands

# Asia Pacific
asia-northeast1 # Tokyo (recommended for Asia users)
asia-southeast1 # Singapore

# See all regions: gcloud run regions list
```

**Cost Optimization Tip:** Use `us-central1` for the best balance of price and performance.

#### Customizing CollabIQ Commands

You can deploy different Cloud Run Jobs for different CollabIQ operations:

**Example 1: Daemon Mode (Continuous Processing)**
```bash
gcloud run jobs create collabiq-daemon \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --max-retries=1 \
  --task-timeout=60m \
  --memory=512Mi \
  --cpu=1
```

**Example 2: One-Time Email Processing**
```bash
gcloud run jobs create collabiq-process \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="process","--max-emails","50" \
  --max-retries=3 \
  --task-timeout=15m \
  --memory=512Mi \
  --cpu=1
```

**Example 3: Configuration Validation**
```bash
gcloud run jobs create collabiq-validate \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="config","validate" \
  --max-retries=0 \
  --task-timeout=5m \
  --memory=256Mi \
  --cpu=0.5
```

#### Verifying Job Creation

After creating the job, verify it was created successfully:

```bash
# List all Cloud Run Jobs
gcloud run jobs list --region=${REGION}

# Describe specific job
gcloud run jobs describe ${JOB_NAME} --region=${REGION}
```

**Expected Output:**
```
✔ Deploying... Done.
  ✔ Creating Job...
Job [collabiq-processor] created successfully.
```

---

### Configuring Environment Variables

Environment variables configure CollabIQ's runtime behavior. Use `--set-env-vars` for non-sensitive configuration.

#### Recommended Environment Variables

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `NOTION_DATABASE_ID_COLLABIQ` | Notion database for storing emails | `a1b2c3d4e5f6...` |
| `EMAIL_ADDRESS` | Gmail account to monitor | `user@gmail.com` |
| `LOG_LEVEL` | Logging verbosity | `INFO` (DEBUG, INFO, WARNING, ERROR) |
| `GEMINI_MODEL` | Google Gemini model | `gemini-2.0-flash-exp` |
| `CLAUDE_MODEL` | Anthropic Claude model | `claude-3-5-sonnet-20241022` |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o` |
| `SELECTED_MODEL` | Default LLM provider | `gemini`, `claude`, or `openai` |

#### Setting Environment Variables During Job Creation

```bash
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="NOTION_DATABASE_ID_COLLABIQ=a1b2c3d4e5f6,EMAIL_ADDRESS=user@gmail.com,LOG_LEVEL=INFO,GEMINI_MODEL=gemini-2.0-flash-exp,CLAUDE_MODEL=claude-3-5-sonnet-20241022,OPENAI_MODEL=gpt-4o,SELECTED_MODEL=gemini" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Note:** Environment variables are comma-separated with no spaces.

#### Updating Environment Variables on Existing Job

To update environment variables without redeploying:

```bash
# Update existing job with new environment variables
gcloud run jobs update ${JOB_NAME} \
  --region=${REGION} \
  --set-env-vars="LOG_LEVEL=DEBUG,SELECTED_MODEL=claude"
```

**To add variables while keeping existing ones:**
```bash
gcloud run jobs update ${JOB_NAME} \
  --region=${REGION} \
  --update-env-vars="NEW_VARIABLE=value"
```

**To remove environment variables:**
```bash
gcloud run jobs update ${JOB_NAME} \
  --region=${REGION} \
  --remove-env-vars="VARIABLE_TO_REMOVE"
```

#### Viewing Current Environment Variables

```bash
# View all environment variables for a job
gcloud run jobs describe ${JOB_NAME} \
  --region=${REGION} \
  --format="value(template.template.containers.env)"
```

---

### Setting Up Google Secret Manager

Sensitive data (API keys, credentials) should **never** be stored as plain environment variables. Use Google Secret Manager for secure storage.

#### Step 1: Create Secrets for Sensitive Data

**Create secrets for API keys:**

```bash
# Notion API Key
echo -n "YOUR_NOTION_API_KEY" | gcloud secrets create notion-api-key \
  --replication-policy="automatic" \
  --data-file=-

# Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --replication-policy="automatic" \
  --data-file=-

# Anthropic API Key
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key \
  --replication-policy="automatic" \
  --data-file=-

# OpenAI API Key
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key \
  --replication-policy="automatic" \
  --data-file=-
```

**Create secrets for Gmail credentials (JSON files):**

```bash
# Gmail credentials.json (OAuth client credentials)
gcloud secrets create gmail-credentials-json \
  --replication-policy="automatic" \
  --data-file=path/to/credentials.json

# Gmail token.json (OAuth access token)
gcloud secrets create gmail-token-json \
  --replication-policy="automatic" \
  --data-file=path/to/token.json
```

**Security Best Practice:** Use `echo -n` (no newline) to avoid trailing newlines in API keys.

**Replication Policy Options:**
- `automatic`: Replicate to all regions (recommended for high availability)
- `user-managed`: Specify exact regions (for data residency compliance)

#### Step 2: Verify Secrets Were Created

```bash
# List all secrets
gcloud secrets list

# View secret metadata (does NOT show the actual secret value)
gcloud secrets describe notion-api-key

# View secret versions
gcloud secrets versions list notion-api-key
```

**Expected Output:**
```
NAME                   CREATED              REPLICATION_POLICY  LOCATIONS
anthropic-api-key      2025-11-27T12:00:00  automatic           -
gemini-api-key         2025-11-27T12:00:00  automatic           -
gmail-credentials-json 2025-11-27T12:00:00  automatic           -
gmail-token-json       2025-11-27T12:00:00  automatic           -
notion-api-key         2025-11-27T12:00:00  automatic           -
openai-api-key         2025-11-27T12:00:00  automatic           -
```

#### Step 3: Grant IAM Permissions to Cloud Run Service Account

Cloud Run Jobs need permission to access secrets. Grant the service account "Secret Manager Secret Accessor" role:

```bash
# Get the default Cloud Run service account
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant secret access for each secret
gcloud secrets add-iam-policy-binding notion-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gmail-credentials-json \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gmail-token-json \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

**Alternative: Grant access to ALL secrets at once (less secure, but convenient for development):**
```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

**Security Note:** Granting project-wide access is convenient but violates least-privilege principle. Use per-secret permissions in production.

#### Step 4: Verify Secrets Are Accessible

Test that the service account can access secrets:

```bash
# Test secret access (requires impersonation permissions)
gcloud secrets versions access latest \
  --secret="notion-api-key" \
  --impersonate-service-account="${SERVICE_ACCOUNT}"
```

If you see the secret value, permissions are correctly configured.

---

### Integrating Secrets with Cloud Run Job

Cloud Run supports two methods for accessing secrets:
1. **Environment variables** (for API keys)
2. **Volume mounts** (for JSON credential files)

#### Method 1: Secrets as Environment Variables

Use `--set-secrets` to inject secrets as environment variables:

```bash
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="NOTION_DATABASE_ID_COLLABIQ=a1b2c3d4e5f6,EMAIL_ADDRESS=user@gmail.com,LOG_LEVEL=INFO" \
  --set-secrets="NOTION_API_KEY=notion-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Secret Format:** `ENV_VAR_NAME=secret-name:version`

| Component | Description | Example |
|-----------|-------------|---------|
| `ENV_VAR_NAME` | Environment variable name CollabIQ expects | `NOTION_API_KEY` |
| `secret-name` | Secret name in Secret Manager | `notion-api-key` |
| `version` | Secret version (`latest` or version number) | `latest` or `1` |

**Using Specific Secret Versions:**
```bash
--set-secrets="NOTION_API_KEY=notion-api-key:1,GEMINI_API_KEY=gemini-api-key:2"
```

**Best Practice:** Use `latest` during development, pin to specific versions in production for stability.

#### Method 2: Secrets as Volume Mounts (for Credential Files)

Gmail credentials (`credentials.json`, `token.json`) are JSON files that must be mounted as files:

```bash
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="NOTION_DATABASE_ID_COLLABIQ=a1b2c3d4e5f6,EMAIL_ADDRESS=user@gmail.com,LOG_LEVEL=INFO" \
  --set-secrets="NOTION_API_KEY=notion-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,/secrets/gmail/credentials.json=gmail-credentials-json:latest,/secrets/gmail/token.json=gmail-token-json:latest" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Volume Mount Format:** `/path/in/container=secret-name:version`

| Component | Description | Example |
|-----------|-------------|---------|
| `/path/in/container` | File path inside the container | `/secrets/gmail/credentials.json` |
| `secret-name` | Secret name in Secret Manager | `gmail-credentials-json` |
| `version` | Secret version | `latest` |

**Important:** Update your CollabIQ code to read Gmail credentials from `/secrets/gmail/`:
```python
# In email_receiver/receiver.py or configuration
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "/secrets/gmail/credentials.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "/secrets/gmail/token.json")
```

#### Complete Deployment Command with All Secrets

Here's the full command with both environment variable secrets and file-based secrets:

```bash
gcloud run jobs create collabiq-processor \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest \
  --region=us-central1 \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="NOTION_DATABASE_ID_COLLABIQ=a1b2c3d4e5f6789012345678,EMAIL_ADDRESS=user@gmail.com,LOG_LEVEL=INFO,GEMINI_MODEL=gemini-2.0-flash-exp,CLAUDE_MODEL=claude-3-5-sonnet-20241022,OPENAI_MODEL=gpt-4o,SELECTED_MODEL=gemini,GMAIL_CREDENTIALS_PATH=/secrets/gmail/credentials.json,GMAIL_TOKEN_PATH=/secrets/gmail/token.json" \
  --set-secrets="NOTION_API_KEY=notion-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,/secrets/gmail/credentials.json=gmail-credentials-json:latest,/secrets/gmail/token.json=gmail-token-json:latest" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

#### Updating Secrets

To rotate API keys or update credentials:

```bash
# 1. Update the secret in Secret Manager
echo -n "NEW_API_KEY" | gcloud secrets versions add notion-api-key --data-file=-

# 2. No need to update the job if using :latest
# Cloud Run will automatically use the new version on next execution

# 3. To force immediate update (redeploy job)
gcloud run jobs update ${JOB_NAME} --region=${REGION}
```

**Pinning to Specific Versions:**
```bash
# Update job to use specific secret version
gcloud run jobs update ${JOB_NAME} \
  --region=${REGION} \
  --set-secrets="NOTION_API_KEY=notion-api-key:2"
```

---

### Configuring Persistent Storage

CollabIQ may need persistent storage for caching, state management, or logs. Cloud Run Jobs are ephemeral, so data must be stored externally.

#### Option 1: Cloud Storage FUSE (Recommended - Simplest)

Cloud Storage FUSE allows mounting a Google Cloud Storage bucket as a filesystem inside your container.

**Step 1: Create a Cloud Storage Bucket**

```bash
# Create a bucket for CollabIQ data
export BUCKET_NAME="${PROJECT_ID}-collabiq-data"

gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BUCKET_NAME}/

# Verify bucket creation
gsutil ls gs://${BUCKET_NAME}/
```

**Bucket Naming Rules:**
- Must be globally unique
- Use lowercase letters, numbers, hyphens
- Cannot start/end with hyphen
- Example: `my-project-123-collabiq-data`

**Step 2: Grant Cloud Run Service Account Access**

```bash
# Grant Storage Object Admin role (read/write)
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectAdmin \
  gs://${BUCKET_NAME}
```

**Alternative: Read-only access (for logs only):**
```bash
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectViewer \
  gs://${BUCKET_NAME}
```

**Step 3: Update Dockerfile to Include gcsfuse**

Add to your `Dockerfile`:
```dockerfile
# Install gcsfuse for Cloud Storage mounting
RUN apt-get update && apt-get install -y \
    gnupg lsb-release wget && \
    export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s` && \
    echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list && \
    wget -O - https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update && \
    apt-get install -y gcsfuse && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

**Step 4: Deploy Job with Storage Mount**

```bash
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="COLLABIQ_DATA_DIR=/mnt/data" \
  --execution-environment=gen2 \
  --mount-type=cloud-storage \
  --mount-path=/mnt/data \
  --mount-bucket=${BUCKET_NAME} \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Mount Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--execution-environment=gen2` | Required for volume mounts | `gen2` |
| `--mount-type` | Type of volume mount | `cloud-storage` |
| `--mount-path` | Path inside container | `/mnt/data` |
| `--mount-bucket` | GCS bucket name | `my-project-collabiq-data` |

**Accessing Mounted Storage in CollabIQ:**
```python
import os

# Read data directory from environment
data_dir = os.getenv("COLLABIQ_DATA_DIR", "/mnt/data")

# Write cache file
cache_file = os.path.join(data_dir, "user_cache.json")
with open(cache_file, "w") as f:
    json.dump(cache_data, f)
```

**Important Notes:**
- Files written to `/mnt/data` persist across job executions
- FUSE mounts have some performance overhead (use for config/cache, not high-throughput operations)
- gen2 execution environment required (gen1 does not support volume mounts)

#### Option 2: Programmatic Access via google-cloud-storage Library

For more control, use the `google-cloud-storage` Python library to interact with Cloud Storage directly.

**Step 1: Add Dependency to pyproject.toml**

```toml
[project]
dependencies = [
    # ... existing dependencies
    "google-cloud-storage>=2.10.0",
]
```

Rebuild Docker image after adding dependency.

**Step 2: Grant Storage Permissions (Same as Option 1)**

```bash
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectAdmin \
  gs://${BUCKET_NAME}
```

**Step 3: Implement Storage Client in CollabIQ**

```python
from google.cloud import storage
import os
import json

class CloudStorageCache:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def save_cache(self, filename: str, data: dict):
        """Save data to Cloud Storage as JSON"""
        blob = self.bucket.blob(filename)
        blob.upload_from_string(json.dumps(data), content_type='application/json')

    def load_cache(self, filename: str) -> dict:
        """Load data from Cloud Storage"""
        blob = self.bucket.blob(filename)
        if blob.exists():
            return json.loads(blob.download_as_string())
        return {}
```

**Step 4: Deploy with Storage Configuration**

```bash
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="GCS_BUCKET_NAME=${BUCKET_NAME}" \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1
```

**Pros of Programmatic Access:**
- Better performance (no FUSE overhead)
- More control over read/write operations
- Supports advanced features (object versioning, lifecycle policies)

**Cons:**
- Requires code changes
- More complex than FUSE mounting

#### Storage Best Practices

**For CollabIQ, use Cloud Storage for:**
- User cache (`user_cache.json`)
- Daemon state (`daemon/state.json`) - **Required for preventing duplicate email processing**
- Token storage (if not using Secret Manager)
- Logs (if not using Cloud Logging)

#### Daemon State Persistence (Required)

CollabIQ's daemon uses state persistence to track which emails have been processed. Without GCS state persistence, each Cloud Run job execution would re-process all recent emails, creating duplicates in Notion.

**How it works:**
1. On job start, the daemon loads state from GCS (including `last_successful_fetch_timestamp`)
2. Emails are fetched using Gmail's `after:` query with this timestamp
3. Only NEW emails since the last run are processed
4. On success, the new timestamp is saved to GCS

**Step 1: Create State Bucket**

```bash
# Create a bucket for daemon state
export STATE_BUCKET="${PROJECT_ID}-state"

gcloud storage buckets create gs://${STATE_BUCKET} \
  --project=${PROJECT_ID} \
  --location=${REGION} \
  --uniform-bucket-level-access

# Grant service account access
gcloud storage buckets add-iam-policy-binding gs://${STATE_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"
```

**Step 2: Deploy with State Bucket Environment Variable**

```bash
gcloud run jobs update ${JOB_NAME} \
  --region=${REGION} \
  --set-env-vars="GCS_STATE_BUCKET=${STATE_BUCKET}"
```

**Step 3: Verify State Persistence**

After a successful job run, check the state file:
```bash
gcloud storage cat gs://${STATE_BUCKET}/daemon/state.json
```

Expected output:
```json
{
  "daemon_start_timestamp": "2025-11-28T23:00:58.974341",
  "last_check_timestamp": "2025-11-28T23:04:03.282933",
  "last_successful_fetch_timestamp": "2025-11-28T23:04:03.422293",
  "total_processing_cycles": 1,
  "emails_processed_count": 10,
  "error_count": 0,
  "current_status": "sleeping"
}
```

**Troubleshooting State Persistence:**

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate emails in Notion | State not persisting | Verify `GCS_STATE_BUCKET` env var is set |
| "No existing state in GCS" on every run | Bucket not accessible | Check service account IAM permissions |
| State file not created | Job failing before completion | Check logs for errors |

**Cost Optimization:**
- Use `STANDARD` storage class for frequently accessed data
- Use `NEARLINE` for logs/backups accessed monthly
- Set lifecycle policies to delete old logs:
  ```bash
  # Create lifecycle policy (delete objects older than 30 days)
  echo '{
    "lifecycle": {
      "rule": [{
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }]
    }
  }' > lifecycle.json

  gsutil lifecycle set lifecycle.json gs://${BUCKET_NAME}
  ```

---

### Executing and Verifying the Job

Once the job is deployed, you can execute it manually or on a schedule.

#### Manual Job Execution

Run the job immediately:

```bash
# Execute the job
gcloud run jobs execute ${JOB_NAME} --region=${REGION}
```

**Expected Output:**
```
✔ Creating execution collabiq-processor-abc123... Done.
  ✔ Starting execution...
Execution [collabiq-processor-abc123] is running.
```

**Wait for Completion:**
```bash
# Watch job execution status
gcloud run jobs executions describe collabiq-processor-abc123 \
  --region=${REGION} \
  --format="value(status.conditions[0].status)"
```

**Check Execution History:**
```bash
# List all executions
gcloud run jobs executions list --job=${JOB_NAME} --region=${REGION}
```

**Expected Output:**
```
EXECUTION                       STATUS     CREATED              COMPLETED
collabiq-processor-abc123       Succeeded  2025-11-27 12:00:00  2025-11-27 12:05:00
collabiq-processor-xyz456       Failed     2025-11-27 11:00:00  2025-11-27 11:02:00
```

#### Viewing Job Logs in Cloud Logging

Cloud Run automatically sends logs to Cloud Logging:

**View Logs in Console:**
1. Go to [console.cloud.google.com/logs](https://console.cloud.google.com/logs)
2. Filter by resource: Cloud Run Job → `collabiq-processor`
3. View real-time logs

**View Logs via gcloud:**
```bash
# Stream logs for latest execution
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}" \
  --limit=50 \
  --format="table(timestamp,jsonPayload.message)"

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}"
```

**Filter Logs by Severity:**
```bash
# Show only errors
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME} AND severity>=ERROR" \
  --limit=20
```

**Advanced Log Filtering:**
```bash
# Logs from last hour
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME} AND timestamp>\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --limit=100
```

#### Checking Job Status and History

**Get Job Details:**
```bash
# View job configuration
gcloud run jobs describe ${JOB_NAME} --region=${REGION}

# View specific execution details
gcloud run jobs executions describe EXECUTION_NAME --region=${REGION}
```

**Check Last Execution Status:**
```bash
# Get latest execution name
LATEST_EXECUTION=$(gcloud run jobs executions list \
  --job=${JOB_NAME} \
  --region=${REGION} \
  --limit=1 \
  --format="value(name)")

# Check status
gcloud run jobs executions describe ${LATEST_EXECUTION} \
  --region=${REGION} \
  --format="value(status.conditions[0].type,status.conditions[0].status)"
```

**Troubleshooting Failed Executions:**
```bash
# View failure reason
gcloud run jobs executions describe ${LATEST_EXECUTION} \
  --region=${REGION} \
  --format="value(status.conditions[0].message)"
```

#### Setting Up Scheduled Execution with Cloud Scheduler

Automate job execution with Cloud Scheduler (cron-like scheduling):

**Step 1: Enable Cloud Scheduler API**

```bash
gcloud services enable cloudscheduler.googleapis.com
```

**Step 2: Create a Scheduled Job**

```bash
# Run every 15 minutes
gcloud scheduler jobs create http collabiq-scheduled \
  --location=${REGION} \
  --schedule="*/15 * * * *" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
  --http-method=POST \
  --oauth-service-account-email=${SERVICE_ACCOUNT}
```

**Schedule Format (Cron Syntax):**

| Expression | Description |
|------------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour (on the hour) |
| `0 9 * * *` | Every day at 9:00 AM UTC |
| `0 9 * * 1` | Every Monday at 9:00 AM UTC |
| `0 0 1 * *` | First day of every month at midnight |

**Example Schedules:**
```bash
# Every 15 minutes
--schedule="*/15 * * * *"

# Every hour at minute 30
--schedule="30 * * * *"

# Every day at 6 AM and 6 PM (UTC)
--schedule="0 6,18 * * *"

# Every weekday at 9 AM (UTC)
--schedule="0 9 * * 1-5"
```

**Step 3: Verify Scheduler Job**

```bash
# List scheduled jobs
gcloud scheduler jobs list --location=${REGION}

# Describe specific job
gcloud scheduler jobs describe collabiq-scheduled --location=${REGION}
```

**Step 4: Test Scheduled Job Manually**

```bash
# Trigger the scheduler job immediately (doesn't wait for schedule)
gcloud scheduler jobs run collabiq-scheduled --location=${REGION}
```

**Step 5: View Scheduler Logs**

```bash
# View scheduler execution logs
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=collabiq-scheduled" \
  --limit=10
```

**Scheduler Best Practices:**
- Use UTC times for schedules (Cloud Scheduler uses UTC)
- Avoid very frequent executions (<5 minutes) to reduce costs
- Set `--attempt-deadline` to prevent stuck jobs:
  ```bash
  gcloud scheduler jobs update http collabiq-scheduled \
    --location=${REGION} \
    --attempt-deadline=30m
  ```

#### Monitoring and Alerting

Set up alerts for job failures:

**Create Alert Policy (via Console):**
1. Go to [console.cloud.google.com/monitoring](https://console.cloud.google.com/monitoring)
2. Navigate to Alerting → Create Policy
3. Add Condition:
   - Resource: Cloud Run Job
   - Metric: Execution count
   - Filter: `status = "Failed"`
   - Threshold: > 0
4. Add Notification Channel (email, Slack, PagerDuty)
5. Save Policy

**Create Alert via gcloud (advanced):**
```bash
# Create a notification channel (email)
gcloud alpha monitoring channels create \
  --display-name="CollabIQ Alerts" \
  --type=email \
  --channel-labels=email_address=admin@example.com

# Create alert policy for job failures
# (Requires complex JSON configuration - use Console for simpler setup)
```

#### Cleanup and Deletion

**Delete a Job Execution:**
```bash
gcloud run jobs executions delete EXECUTION_NAME --region=${REGION}
```

**Delete a Job:**
```bash
gcloud run jobs delete ${JOB_NAME} --region=${REGION}
```

**Delete Scheduled Job:**
```bash
gcloud scheduler jobs delete collabiq-scheduled --location=${REGION}
```

**Note:** Deleting a job does NOT delete the container image in Artifact Registry or secrets in Secret Manager.

---

## Summary of Key Deployment Commands

Here's a quick reference for deploying CollabIQ to Cloud Run:

```bash
# 1. Set environment variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export JOB_NAME="collabiq-processor"
export IMAGE_URL="us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest"
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
export BUCKET_NAME="${PROJECT_ID}-collabiq-data"

# 2. Create secrets
echo -n "YOUR_NOTION_API_KEY" | gcloud secrets create notion-api-key --replication-policy="automatic" --data-file=-
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --replication-policy="automatic" --data-file=-
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --replication-policy="automatic" --data-file=-
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --replication-policy="automatic" --data-file=-
gcloud secrets create gmail-credentials-json --replication-policy="automatic" --data-file=credentials.json
gcloud secrets create gmail-token-json --replication-policy="automatic" --data-file=token.json

# 3. Grant secret access
for secret in notion-api-key gemini-api-key anthropic-api-key openai-api-key gmail-credentials-json gmail-token-json; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
done

# 4. Create storage bucket
gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BUCKET_NAME}/
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectAdmin gs://${BUCKET_NAME}

# 5. Deploy Cloud Run Job
gcloud run jobs create ${JOB_NAME} \
  --image=${IMAGE_URL} \
  --region=${REGION} \
  --command="collabiq" \
  --args="run" \
  --set-env-vars="NOTION_DATABASE_ID_COLLABIQ=YOUR_NOTION_DB_ID,EMAIL_ADDRESS=user@gmail.com,LOG_LEVEL=INFO,GEMINI_MODEL=gemini-2.0-flash-exp,CLAUDE_MODEL=claude-3-5-sonnet-20241022,OPENAI_MODEL=gpt-4o,SELECTED_MODEL=gemini,GMAIL_CREDENTIALS_PATH=/secrets/gmail/credentials.json,GMAIL_TOKEN_PATH=/secrets/gmail/token.json,COLLABIQ_DATA_DIR=/mnt/data" \
  --set-secrets="NOTION_API_KEY=notion-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,/secrets/gmail/credentials.json=gmail-credentials-json:latest,/secrets/gmail/token.json=gmail-token-json:latest" \
  --execution-environment=gen2 \
  --mount-type=cloud-storage \
  --mount-path=/mnt/data \
  --mount-bucket=${BUCKET_NAME} \
  --max-retries=3 \
  --task-timeout=30m \
  --memory=512Mi \
  --cpu=1

# 6. Execute job manually
gcloud run jobs execute ${JOB_NAME} --region=${REGION}

# 7. Set up scheduled execution (every 5 minutes)
gcloud services enable cloudscheduler.googleapis.com
gcloud scheduler jobs create http collabiq-scheduled \
  --location=${REGION} \
  --schedule="*/5 * * * *" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
  --http-method=POST \
  --oauth-service-account-email=${SERVICE_ACCOUNT}

# 8. View logs
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}"
```

**Next Steps:**
- Monitor job executions in Cloud Console
- Set up alerting for failures
- Optimize resource allocation (CPU/memory) based on actual usage
- Review logs for errors and performance issues

---

## Troubleshooting

This section covers common issues you may encounter when deploying CollabIQ to Google Cloud Run, along with their solutions.

### Google Cloud API Permission Errors

#### Issue: "Permission denied" when enabling APIs
**Error Message:**
```
ERROR: (gcloud.services.enable) User [user@example.com] does not have permission to access project [PROJECT_ID]
```

**Cause:** Your Google account doesn't have sufficient permissions on the project.

**Solutions:**

1. **Verify you're logged into the correct account:**
   ```bash
   gcloud auth list
   # Ensure the active account has project access
   ```

2. **Switch to the correct account:**
   ```bash
   gcloud config set account correct-account@gmail.com
   ```

3. **Request access from project owner:**
   If someone else owns the project, ask them to grant you the "Editor" or "Owner" role:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="user:YOUR_EMAIL@gmail.com" \
     --role="roles/editor"
   ```

4. **Verify project ownership:**
   ```bash
   gcloud projects get-iam-policy $(gcloud config get-value project)
   ```

#### Issue: Missing IAM roles for Cloud Run Job
**Error Message:**
```
ERROR: (gcloud.run.jobs.create) User does not have permission to create jobs in project [PROJECT_ID]
```

**Cause:** Your account lacks the `run.jobs.create` permission.

**Solution:**
```bash
# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/run.admin"
```

#### Issue: Service account cannot access secrets
**Error Message:**
```
ERROR: Secret [SECRET_NAME] not found or permission denied
```

**Cause:** Cloud Run service account doesn't have Secret Manager permissions.

**Solutions:**

1. **Verify secret exists:**
   ```bash
   gcloud secrets list | grep SECRET_NAME
   ```

2. **Grant Secret Manager access:**
   ```bash
   export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
   export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

   gcloud secrets add-iam-policy-binding SECRET_NAME \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Verify permissions were granted:**
   ```bash
   gcloud secrets get-iam-policy SECRET_NAME
   ```

#### Issue: "Billing account not linked" error
**Error Message:**
```
ERROR: (gcloud.services.enable) The project is not linked to a billing account
```

**Cause:** Google Cloud requires billing to be enabled, even for free tier usage.

**Solution:**
1. Go to [console.cloud.google.com/billing](https://console.cloud.google.com/billing)
2. Select your project
3. Click "Link a billing account"
4. Select or create a billing account (you won't be charged for free tier usage)

---

### Conflicting Configuration Issues

#### Issue: Duplicate resource names
**Error Message:**
```
ERROR: (gcloud.artifacts.repositories.create) Resource [collabiq-repo] already exists
```

**Cause:** A resource with the same name already exists in your project.

**Solutions:**

1. **List existing resources:**
   ```bash
   # For Artifact Registry
   gcloud artifacts repositories list

   # For Cloud Run Jobs
   gcloud run jobs list --region=us-central1
   ```

2. **Use a different name:**
   ```bash
   gcloud artifacts repositories create collabiq-repo-v2 \
     --repository-format=docker \
     --location=us-central1
   ```

3. **Delete the existing resource (if it's safe to do so):**
   ```bash
   # Delete Artifact Registry repository (WARNING: Deletes all images!)
   gcloud artifacts repositories delete collabiq-repo --location=us-central1

   # Delete Cloud Run Job
   gcloud run jobs delete JOB_NAME --region=us-central1
   ```

#### Issue: Region mismatch between resources
**Error Message:**
```
ERROR: Image not found in region [us-west1]
```

**Cause:** Your Docker image is in `us-central1` but you're deploying a job in `us-west1`.

**Solutions:**

1. **Use the same region for all resources:**
   ```bash
   export REGION="asia-northeast1"

   # Ensure all commands use the same region
   gcloud run jobs create JOB_NAME --region=${REGION} ...
   ```

2. **Copy image to another region (if needed):**
   ```bash
   # Pull from original region
   docker pull us-central1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:latest

   # Tag for new region
   docker tag us-central1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:latest \
              us-west1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:latest

   # Push to new region
   docker push us-west1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:latest
   ```

3. **Verify all resources are in the same region:**
   ```bash
   # Check Artifact Registry
   gcloud artifacts repositories list --filter="location:us-central1"

   # Check Cloud Run Jobs
   gcloud run jobs list --region=us-central1
   ```

---

### Billing Issues

#### Issue: "Billing not enabled" when enabling APIs
**Error Message:**
```
ERROR: (gcloud.services.enable) Billing must be enabled for activation of service
```

**Cause:** Project doesn't have a billing account linked.

**Solution:**
1. Visit [console.cloud.google.com/billing/linkedaccount](https://console.cloud.google.com/billing/linkedaccount)
2. Select your project
3. Link to a billing account (even for free tier usage)
4. Wait 2-3 minutes for propagation
5. Retry the command

#### Issue: Quota exceeded errors
**Error Message:**
```
ERROR: (gcloud.run.jobs.execute) Quota exceeded for quota metric 'Run job executions' and limit 'Run job executions per region per day'
```

**Cause:** You've hit the free tier or project quota limits.

**Solutions:**

1. **Check current quotas:**
   ```bash
   gcloud compute project-info describe --project=$(gcloud config get-value project)
   ```

2. **View quota usage in console:**
   - Go to [console.cloud.google.com/iam-admin/quotas](https://console.cloud.google.com/iam-admin/quotas)
   - Filter for "Cloud Run"
   - Review current usage

3. **Request quota increase:**
   - Click "Edit Quotas" in the console
   - Select the quota to increase
   - Submit a request (typically approved within 24-48 hours)

4. **Temporary workaround - use a different region:**
   ```bash
   # Quotas are per-region
   gcloud run jobs create JOB_NAME --region=us-east1 ...
   ```

#### Issue: Free tier limits exceeded
**Error Message:**
```
You have exceeded your free tier limits. Additional usage will be charged.
```

**Cause:** You've used up the $300 free credits or 90-day trial period.

**Solutions:**

1. **Review current billing:**
   - Go to [console.cloud.google.com/billing/reports](https://console.cloud.google.com/billing/reports)
   - Analyze spend by service

2. **Optimize resources (see Cost Optimization section below)**

3. **Set up budget alerts:**
   ```bash
   # Via console at console.cloud.google.com/billing/budgets
   # Set a budget of $10/month with 50%, 75%, 90%, 100% alerts
   ```

---

### Docker Build Failures

#### Issue: Docker build fails with dependency errors
**Error Message:**
```
ERROR: failed to solve: process "/bin/sh -c uv sync --frozen --no-dev" did not complete successfully: exit code: 1
```

**Cause:** Dependencies in `pyproject.toml` cannot be resolved or UV lockfile is outdated.

**Solutions:**

1. **Update UV lockfile locally:**
   ```bash
   cd /Users/jlim/Projects/CollabIQ
   uv lock
   git add uv.lock
   git commit -m "Update UV lockfile"
   ```

2. **Remove `--frozen` flag temporarily (for debugging):**
   ```dockerfile
   # In Dockerfile, change:
   RUN uv sync --frozen --no-dev
   # To:
   RUN uv sync --no-dev
   ```

3. **Check for platform-specific dependencies:**
   ```bash
   # Verify dependencies install on Linux
   docker run --rm -v $(pwd):/app python:3.12-slim-bookworm \
     /bin/bash -c "cd /app && pip install uv && uv sync --no-dev"
   ```

#### Issue: Platform compatibility (ARM vs x86)
**Error Message:**
```
WARNING: The requested image's platform (linux/arm64) does not match the detected host platform (linux/amd64)
```

**Cause:** Building on Apple Silicon (M1/M2/M3) Mac but Cloud Run uses x86_64.

**Solutions:**

1. **Build for x86_64 platform explicitly:**
   ```bash
   docker buildx build --platform linux/amd64 \
     -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest .
   ```

2. **Install buildx if not available:**
   ```bash
   # Check if buildx is available
   docker buildx version

   # If not, update Docker Desktop to latest version
   brew upgrade --cask docker
   ```

3. **Create a multi-platform builder:**
   ```bash
   docker buildx create --name multiplatform --use
   docker buildx build --platform linux/amd64,linux/arm64 \
     -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest --push .
   ```

#### Issue: COPY fails - file not found
**Error Message:**
```
ERROR: failed to compute cache key: "/pyproject.toml" not found
```

**Cause:** Docker build context doesn't include required files.

**Solutions:**

1. **Verify files exist:**
   ```bash
   ls -la pyproject.toml uv.lock src/ README.md
   ```

2. **Check .dockerignore isn't excluding required files:**
   ```bash
   cat .dockerignore

   # Ensure these are NOT in .dockerignore:
   # - pyproject.toml
   # - uv.lock
   # - src/
   # - README.md
   ```

3. **Build from project root:**
   ```bash
   cd /Users/jlim/Projects/CollabIQ
   docker build -t collabiq:latest .
   ```

#### Issue: Build is extremely slow
**Cause:** Docker not using layer cache or re-downloading dependencies every time.

**Solutions:**

1. **Verify layer caching:**
   ```bash
   docker build --progress=plain -t collabiq:test .
   # Look for "CACHED" messages
   ```

2. **Optimize Dockerfile layer order:**
   ```dockerfile
   # Copy dependencies first (changes infrequently)
   COPY pyproject.toml uv.lock ./
   RUN uv sync --frozen --no-dev --no-install-project

   # Copy source code last (changes frequently)
   COPY src/ ./src/
   COPY README.md ./
   RUN uv sync --frozen --no-dev
   ```

3. **Clean Docker cache:**
   ```bash
   docker system prune -a
   docker builder prune
   ```

---

### Cloud Run Job Failures

#### Issue: Job timeout errors
**Error Message:**
```
ERROR: Job execution exceeded timeout of 10m
```

**Cause:** CollabIQ daemon or processing takes longer than the configured timeout.

**Solutions:**

1. **Increase task timeout:**
   ```bash
   gcloud run jobs update JOB_NAME \
     --region=us-central1 \
     --task-timeout=60m
   ```

2. **Optimize CollabIQ batch size:**
   ```bash
   # Reduce emails processed per run
   --args="run","--daemon","--interval","5","--max-emails","10"
   ```

3. **Check logs for bottlenecks:**
   ```bash
   gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=WARNING" \
     --limit=50 \
     --format="table(timestamp,jsonPayload.message)"
   ```

#### Issue: Memory or CPU limits exceeded
**Error Message:**
```
ERROR: Memory limit of 512Mi exceeded
```

**Cause:** CollabIQ is using more resources than allocated.

**Solutions:**

1. **Increase memory allocation:**
   ```bash
   gcloud run jobs update JOB_NAME \
     --region=us-central1 \
     --memory=1Gi \
     --cpu=2
   ```

2. **Monitor resource usage:**
   ```bash
   # View execution metrics
   gcloud run jobs executions describe EXECUTION_NAME \
     --region=us-central1 \
     --format="yaml(status.resourceUsage)"
   ```

3. **Optimize memory usage in code:**
   - Process emails in smaller batches
   - Clear LLM response caches after processing
   - Use streaming for large API responses

#### Issue: Secret access failures
**Error Message:**
```
ERROR: Secret "notion-api-key" not accessible
```

**Cause:** Service account doesn't have permissions or secret doesn't exist.

**Solutions:**

1. **Verify secret exists and is accessible:**
   ```bash
   gcloud secrets versions access latest --secret=notion-api-key
   ```

2. **Check IAM permissions:**
   ```bash
   gcloud secrets get-iam-policy notion-api-key
   ```

3. **Grant access to service account:**
   ```bash
   export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
   export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

   gcloud secrets add-iam-policy-binding notion-api-key \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/secretmanager.secretAccessor"
   ```

4. **Verify job is using correct secret reference:**
   ```bash
   gcloud run jobs describe JOB_NAME --region=us-central1 \
     --format="yaml(template.template.containers[0].env)"
   ```

#### Issue: Storage mount problems
**Error Message:**
```
ERROR: Failed to mount Cloud Storage bucket
```

**Cause:** Bucket doesn't exist, wrong permissions, or gen1 execution environment.

**Solutions:**

1. **Verify bucket exists:**
   ```bash
   gsutil ls -p $(gcloud config get-value project)
   ```

2. **Check bucket permissions:**
   ```bash
   gsutil iam get gs://BUCKET_NAME
   ```

3. **Ensure using gen2 execution environment:**
   ```bash
   gcloud run jobs update JOB_NAME \
     --region=us-central1 \
     --execution-environment=gen2
   ```

4. **Grant storage permissions:**
   ```bash
   export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
   gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectAdmin gs://BUCKET_NAME
   ```

---

### Authentication Issues

#### Issue: gcloud authentication expired
**Error Message:**
```
ERROR: (gcloud) Your current active account [USER@gmail.com] does not have any valid credentials
```

**Cause:** Your gcloud credentials have expired (typically after 1 hour).

**Solutions:**

1. **Re-authenticate:**
   ```bash
   gcloud auth login
   ```

2. **Refresh application default credentials:**
   ```bash
   gcloud auth application-default login
   ```

3. **For CI/CD environments, use service account:**
   ```bash
   gcloud auth activate-service-account --key-file=key.json
   ```

#### Issue: Docker authentication to Artifact Registry
**Error Message:**
```
unauthorized: authentication required
```

**Cause:** Docker credentials for Artifact Registry are not configured or expired.

**Solutions:**

1. **Configure Docker authentication:**
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

2. **Verify Docker config:**
   ```bash
   cat ~/.docker/config.json | grep credHelpers
   ```

3. **Manually refresh credentials:**
   ```bash
   gcloud auth application-default login
   gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
   ```

4. **Test authentication:**
   ```bash
   docker pull us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest
   ```

#### Issue: Service account key issues
**Error Message:**
```
ERROR: Could not find service account key file
```

**Cause:** Service account key file is missing or path is incorrect.

**Solutions:**

1. **Create a new service account key:**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=${SERVICE_ACCOUNT}
   ```

2. **Verify key file exists:**
   ```bash
   ls -la key.json
   cat key.json | jq '.type'  # Should output "service_account"
   ```

3. **Use key file for authentication:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   gcloud auth activate-service-account --key-file=key.json
   ```

---

### General Debugging Tips

#### Viewing Real-Time Logs
```bash
# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME"

# Filter for errors only
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=ERROR"
```

#### Testing Locally Before Deploying
```bash
# Test Docker image locally with secrets
docker run --rm \
  -e NOTION_API_KEY="your-key" \
  -e GEMINI_API_KEY="your-key" \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest \
  config validate

# Test with mounted credentials
docker run --rm \
  -v ~/.config/collabiq/credentials:/secrets/gmail:ro \
  -e GMAIL_CREDENTIALS_PATH=/secrets/gmail/credentials.json \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest \
  daemon run --interval 60
```

#### Checking Cloud Run Job Status
```bash
# Get latest execution
LATEST=$(gcloud run jobs executions list --job=JOB_NAME --region=us-central1 --limit=1 --format="value(name)")

# Describe execution
gcloud run jobs executions describe ${LATEST} --region=us-central1

# Check failure reason
gcloud run jobs executions describe ${LATEST} \
  --region=us-central1 \
  --format="value(status.conditions[0].message)"
```

#### Common Log Queries
```bash
# All logs from last hour
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND timestamp>\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --limit=100

# Errors only
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=ERROR" \
  --limit=50

# Search for specific text
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND textPayload=~\"Failed to process\"" \
  --limit=20
```

---

### Getting Help

If you're still stuck after trying these solutions:

1. **Check Google Cloud Status:**
   - [status.cloud.google.com](https://status.cloud.google.com)

2. **Review Official Documentation:**
   - [Cloud Run Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting)
   - [Artifact Registry Troubleshooting](https://cloud.google.com/artifact-registry/docs/troubleshooting)

3. **Community Support:**
   - [Stack Overflow - google-cloud-run tag](https://stackoverflow.com/questions/tagged/google-cloud-run)
   - [Google Cloud Community](https://www.googlecloudcommunity.com/)

4. **Contact Google Cloud Support:**
   - Basic support included with all projects
   - Paid support plans available for production workloads

---

## Monitoring and Logging

Cloud Run integrates with Google Cloud's observability tools for comprehensive monitoring and logging.

### Cloud Logging

Cloud Run automatically streams all application logs to Cloud Logging.

#### Viewing Logs in Google Cloud Console

1. **Navigate to Cloud Logging:**
   - Go to [console.cloud.google.com/logs](https://console.cloud.google.com/logs)
   - Or: Navigation menu → Logging → Logs Explorer

2. **Filter by Resource:**
   - Resource Type: Cloud Run Job
   - Job Name: Select your job (e.g., `collabiq-processor`)
   - Region: Select your deployment region

3. **Apply Time Filters:**
   - Last 1 hour (default)
   - Last 24 hours
   - Custom time range

4. **Filter by Severity:**
   - Click severity dropdown
   - Select: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### Viewing Logs via gcloud CLI

**Stream Real-Time Logs:**
```bash
# Tail logs (like tail -f)
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME"

# Tail with severity filter
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=WARNING"

# Tail specific fields only
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME" \
  --format="table(timestamp,severity,jsonPayload.message)"
```

**Read Historical Logs:**
```bash
# Last 100 log entries
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME" \
  --limit=100 \
  --format="table(timestamp,severity,jsonPayload.message)"

# Logs from specific time range
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND timestamp>=\"2025-11-27T10:00:00Z\" AND timestamp<=\"2025-11-27T12:00:00Z\"" \
  --limit=100

# Filter by severity
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=ERROR" \
  --limit=50
```

**Advanced Log Filtering:**
```bash
# Search for specific text in logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND textPayload=~\"Failed to process\"" \
  --limit=20

# Filter by execution ID
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND labels.execution_name=EXECUTION_ID" \
  --limit=100

# Combine multiple filters
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=WARNING AND timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --limit=50
```

#### Setting Up Log-Based Alerts

Create alerts that trigger when specific log patterns appear:

**Via Google Cloud Console:**

1. **Navigate to Alerting:**
   - Go to [console.cloud.google.com/monitoring/alerting](https://console.cloud.google.com/monitoring/alerting)
   - Click "Create Policy"

2. **Add Condition:**
   - Select "Log-based metric"
   - Filter: `resource.type="cloud_run_job" AND resource.labels.job_name="JOB_NAME" AND severity>=ERROR`
   - Aggregation: Count
   - Threshold: > 0 errors in 5 minutes

3. **Configure Notifications:**
   - Add notification channel (email, Slack, PagerDuty)
   - Customize alert message

4. **Save Policy**

**Example Alert Policies:**

**Alert on Job Failures:**
```
resource.type=cloud_run_job
AND resource.labels.job_name=JOB_NAME
AND severity=ERROR
AND jsonPayload.message=~"execution failed"
```

**Alert on High Error Rate:**
```
resource.type=cloud_run_job
AND resource.labels.job_name=JOB_NAME
AND severity>=ERROR
```

**Alert on Timeout Errors:**
```
resource.type=cloud_run_job
AND resource.labels.job_name=JOB_NAME
AND jsonPayload.message=~"timeout"
```

#### Log Retention and Storage

**Default Retention:**
- Cloud Logging retains logs for 30 days (default)
- Can be extended up to 3650 days (10 years) for a fee

**Configure Custom Retention:**
1. Go to [console.cloud.google.com/logs/storage](https://console.cloud.google.com/logs/storage)
2. Select "_Default" bucket
3. Click "Edit"
4. Set retention period (30-3650 days)
5. Click "Update"

**Export Logs to Cloud Storage (for long-term archival):**
```bash
# Create a Cloud Storage bucket for logs
gsutil mb -p ${PROJECT_ID} -c STANDARD -l us-central1 gs://${PROJECT_ID}-logs/

# Create log sink
gcloud logging sinks create collabiq-logs-sink \
  gs://${PROJECT_ID}-logs/ \
  --log-filter='resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME'
```

---

### Cloud Monitoring

Google Cloud Monitoring provides metrics, dashboards, and alerting for Cloud Run Jobs.

#### Key Metrics to Monitor

**Execution Metrics:**
- **Execution Count:** Number of job executions
- **Execution Duration:** Time taken to complete
- **Success Rate:** Percentage of successful executions
- **Failure Rate:** Percentage of failed executions

**Resource Metrics:**
- **CPU Utilization:** Percentage of allocated CPU used
- **Memory Utilization:** Percentage of allocated memory used
- **Request Count:** Number of API requests (for Cloud Run Services)
- **Billable Time:** Total compute time charged

#### Viewing Metrics in Console

1. **Navigate to Cloud Monitoring:**
   - Go to [console.cloud.google.com/monitoring](https://console.cloud.google.com/monitoring)
   - Select "Metrics Explorer"

2. **Select Resource:**
   - Resource Type: Cloud Run Job
   - Job Name: `collabiq-processor`

3. **Choose Metrics:**
   - `run.googleapis.com/job/completed_execution_count`
   - `run.googleapis.com/job/execution_latencies`
   - `run.googleapis.com/container/cpu/utilizations`
   - `run.googleapis.com/container/memory/utilizations`

4. **Customize Visualization:**
   - Chart type: Line, stacked area, heatmap
   - Aggregation: Mean, sum, max, min
   - Time range: 1 hour, 1 day, 1 week

#### Creating Dashboards

**Custom Dashboard for CollabIQ:**

1. **Create Dashboard:**
   - Go to [console.cloud.google.com/monitoring/dashboards](https://console.cloud.google.com/monitoring/dashboards)
   - Click "Create Dashboard"
   - Name: "CollabIQ Production Monitoring"

2. **Add Widgets:**

**Execution Count Widget:**
```
Resource: Cloud Run Job (collabiq-processor)
Metric: run.googleapis.com/job/completed_execution_count
Aggregation: Sum
Filter: status="success"
```

**Failure Rate Widget:**
```
Resource: Cloud Run Job (collabiq-processor)
Metric: run.googleapis.com/job/completed_execution_count
Aggregation: Sum
Filter: status="failed"
```

**CPU Utilization Widget:**
```
Resource: Cloud Run Job (collabiq-processor)
Metric: run.googleapis.com/container/cpu/utilizations
Aggregation: Mean
```

**Memory Utilization Widget:**
```
Resource: Cloud Run Job (collabiq-processor)
Metric: run.googleapis.com/container/memory/utilizations
Aggregation: Mean
```

**Execution Duration Widget:**
```
Resource: Cloud Run Job (collabiq-processor)
Metric: run.googleapis.com/job/execution_latencies
Aggregation: 50th, 95th, 99th percentile
```

3. **Arrange and Save Dashboard**

#### Setting Up Alerting Policies

**Alert on Job Failures:**

1. **Create Alert Policy:**
   - Go to [console.cloud.google.com/monitoring/alerting](https://console.cloud.google.com/monitoring/alerting)
   - Click "Create Policy"

2. **Add Condition:**
   ```
   Resource Type: Cloud Run Job
   Metric: run.googleapis.com/job/completed_execution_count
   Filter: status="failed" AND job_name="collabiq-processor"
   Condition: Any time series violates
   Threshold: > 0 failures in 5 minutes
   ```

3. **Configure Notifications:**
   - Notification channel: Email, Slack, SMS, PagerDuty
   - Alert message template:
     ```
     CollabIQ job execution failed!
     Job: ${resource.labels.job_name}
     Execution: ${metric.labels.execution_name}
     Time: ${condition.time}
     ```

4. **Save Policy**

**Alert on High Memory Usage:**
```
Resource Type: Cloud Run Job
Metric: run.googleapis.com/container/memory/utilizations
Filter: job_name="collabiq-processor"
Condition: Any time series violates
Threshold: > 90% for 5 minutes
```

**Alert on Slow Executions:**
```
Resource Type: Cloud Run Job
Metric: run.googleapis.com/job/execution_latencies
Filter: job_name="collabiq-processor"
Condition: 95th percentile exceeds
Threshold: > 1800 seconds (30 minutes)
```

#### Integration with Notification Channels

**Supported Notification Channels:**
- Email
- SMS (via Cloud Mobile App)
- Slack
- PagerDuty
- Webhook (for custom integrations)
- Pub/Sub (for event-driven workflows)

**Setting Up Slack Notifications:**

1. **Create Slack App:**
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Create new app
   - Add Incoming Webhook

2. **Add Notification Channel in GCP:**
   - Go to [console.cloud.google.com/monitoring/alerting/notifications](https://console.cloud.google.com/monitoring/alerting/notifications)
   - Click "Add New"
   - Select "Slack"
   - Paste Webhook URL
   - Test notification

3. **Use in Alert Policies:**
   - When creating alert, select Slack channel
   - Customize message format

---

### Job Status Monitoring

#### Using gcloud to Check Job Status

**List All Job Executions:**
```bash
# List recent executions
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --limit=10

# Filter by status
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --filter="status.conditions[0].type=Completed AND status.conditions[0].status=True"
```

**Get Detailed Execution Information:**
```bash
# Describe specific execution
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1

# Get execution status only
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1 \
  --format="value(status.conditions[0].status)"

# Get failure reason
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1 \
  --format="value(status.conditions[0].message)"
```

**Check Execution History:**
```bash
# List executions with timestamps
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --format="table(name,status.completionTime,status.conditions[0].status)"

# Count successes vs failures
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --format="value(status.conditions[0].status)" | sort | uniq -c
```

#### Monitoring Script Example

Create a script to monitor job health:

```bash
#!/bin/bash
# File: monitor-collabiq.sh

JOB_NAME="collabiq-processor"
REGION="asia-northeast1"

# Get latest execution
LATEST=$(gcloud run jobs executions list \
  --job=${JOB_NAME} \
  --region=${REGION} \
  --limit=1 \
  --format="value(name)")

# Check status
STATUS=$(gcloud run jobs executions describe ${LATEST} \
  --region=${REGION} \
  --format="value(status.conditions[0].status)")

# Get completion time
COMPLETED=$(gcloud run jobs executions describe ${LATEST} \
  --region=${REGION} \
  --format="value(status.completionTime)")

echo "Latest Execution: ${LATEST}"
echo "Status: ${STATUS}"
echo "Completed: ${COMPLETED}"

# Alert if failed
if [ "${STATUS}" != "True" ]; then
  echo "ALERT: Job execution failed!"
  # Send notification (email, Slack, etc.)
fi
```

**Schedule this script with cron:**
```bash
# Run every 10 minutes
*/10 * * * * /path/to/monitor-collabiq.sh
```

#### Identifying Failed Executions

**Find Recent Failures:**
```bash
# Get all failed executions from last 24 hours
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity=ERROR AND timestamp>=\"$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --limit=50 \
  --format="table(timestamp,labels.execution_name,jsonPayload.message)"
```

**Analyze Failure Patterns:**
```bash
# Get failure reasons
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --filter="status.conditions[0].status=False" \
  --format="table(name,status.completionTime,status.conditions[0].message)"
```

**Get Metrics for Failed Executions:**
```bash
# Resource usage for failed execution
gcloud run jobs executions describe FAILED_EXECUTION_NAME \
  --region=us-central1 \
  --format="yaml(status.resourceUsage)"
```

---

### Best Practices for Monitoring

1. **Set Up Alerts for Critical Issues:**
   - Job failures (alert immediately)
   - Memory/CPU exceeding 80% (warning)
   - Execution time exceeding normal threshold (warning)

2. **Create a Monitoring Dashboard:**
   - Pin to Google Cloud Console homepage
   - Include key metrics: success rate, execution time, resource usage
   - Share with team members

3. **Regular Log Reviews:**
   - Check logs weekly for warnings
   - Look for patterns in errors
   - Identify performance bottlenecks

4. **Track Trends Over Time:**
   - Monitor execution duration trends
   - Track resource usage growth
   - Identify when scaling is needed

5. **Use Structured Logging in CollabIQ:**
   ```python
   import logging
   import json

   logger = logging.getLogger(__name__)

   # Structured logging for better Cloud Logging integration
   logger.info(json.dumps({
       "message": "Processed emails",
       "count": 10,
       "duration_seconds": 45.2,
       "status": "success"
   }))
   ```

6. **Set Up Uptime Checks (Optional):**
   - Create synthetic monitor to test job health
   - Schedule manual execution via Cloud Scheduler
   - Alert if scheduled execution doesn't occur

---

## Cost Optimization

Cloud Run Jobs offer excellent cost efficiency with pay-per-use pricing. This section helps you minimize costs while maintaining performance.

### Understanding Cloud Run Jobs Pricing

Cloud Run Jobs charge only for actual compute time (no idle costs).

#### Pricing Components

**1. CPU and Memory:**
- Charged per second while job is running
- Minimum billing increment: 100ms
- Pricing tiers (as of 2025, us-central1 region):

| Resource | Price per second |
|----------|------------------|
| 1 vCPU | $0.00002400 |
| 1 GB Memory | $0.00000250 |

**2. Request Count:**
- Cloud Run Jobs: No request charges (unlike Services)
- Only pay for execution time

**3. Networking:**
- Ingress: Free
- Egress to Google Services: Free
- Egress to internet: $0.12/GB (first 1 GB free per month)

**4. Storage (if using Cloud Storage FUSE):**
- Standard Storage: $0.020/GB/month
- Operations: $0.005 per 10,000 operations

**5. Secret Manager:**
- Active secret versions: $0.06 per version per month
- Access operations: $0.03 per 10,000 accesses

#### Cost Calculation Example

**Scenario:** CollabIQ runs every 5 minutes, each execution takes 2 minutes, using 512 MB memory and 1 CPU.

```
Executions per month: (60 / 5) * 24 * 30 = 8,640 executions
Total runtime: 8,640 * 2 minutes = 17,280 minutes = 1,036,800 seconds

CPU cost: 1,036,800 * $0.00002400 = $24.88
Memory cost: 1,036,800 * 0.5 GB * $0.00000250 = $1.30
Total compute: $26.18/month

Additional costs:
- Secret Manager (6 secrets): 6 * $0.06 = $0.36/month
- Cloud Storage (1 GB data): $0.02/month
- Networking (minimal): ~$0

Estimated total: ~$26.56/month
```

**Free Tier:**
- Cloud Run: 2 million requests/month + 360,000 GB-seconds free
- Secret Manager: 6 active secret versions free
- Cloud Storage: 5 GB free

**Typical CollabIQ monthly cost: $5-30 depending on usage**

---

### Cost Reduction Strategies

#### 1. Right-Size Memory and CPU Allocation

**Monitor Actual Usage:**
```bash
# Check memory utilization for recent executions
gcloud run jobs executions list \
  --job=JOB_NAME \
  --region=us-central1 \
  --limit=10 \
  --format="table(name,status.resourceUsage.memory.max)"

# Get CPU utilization
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME" \
  --limit=100 \
  --format="value(jsonPayload.cpu_utilization)"
```

**Optimization Recommendations:**

If memory usage is consistently < 50%, reduce allocation:
```bash
# Reduce from 512Mi to 256Mi
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --memory=256Mi
```

If memory usage is > 90%, increase to avoid failures:
```bash
# Increase from 512Mi to 1Gi
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --memory=1Gi
```

**CPU Optimization:**
```bash
# Use 0.5 vCPU for light workloads (saves 50%)
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --cpu=0.5 \
  --memory=256Mi

# Use 1 vCPU for standard workloads
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --cpu=1 \
  --memory=512Mi
```

#### 2. Optimize Job Execution Frequency

**Analyze Email Volume Patterns:**
- Do you really need to check every 5 minutes?
- Are emails mostly received during business hours?

**Adjust Schedule Based on Patterns:**

**Frequent checks during business hours, less frequent at night:**
```bash
# Business hours (6 AM - 6 PM): every 5 minutes
gcloud scheduler jobs create http collabiq-business-hours \
  --location=us-central1 \
  --schedule="*/5 6-18 * * *" \
  --uri="..." \
  --oauth-service-account-email=${SERVICE_ACCOUNT}

# Off-hours: every 30 minutes
gcloud scheduler jobs create http collabiq-off-hours \
  --location=us-central1 \
  --schedule="*/30 0-5,19-23 * * *" \
  --uri="..." \
  --oauth-service-account-email=${SERVICE_ACCOUNT}
```

**Cost Savings Example:**
```
5-minute interval: 8,640 executions/month → $26/month
15-minute interval: 2,880 executions/month → $9/month
Savings: $17/month (65% reduction)
```

#### 3. Batch Processing for Efficiency

**Process Multiple Emails Per Execution:**
```bash
# Update job to process up to 50 emails at once
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --update-env-vars="MAX_EMAILS_PER_RUN=50"
```

**Benefits:**
- Amortize startup costs across multiple emails
- Reduce total number of executions
- Better LLM API usage (batch requests where possible)

**Trade-off:** Longer individual execution times (ensure timeout is adequate)

#### 4. Use Lifecycle Policies for Storage

**Delete Old Logs and Cache Files:**
```bash
# Create lifecycle policy to delete objects older than 30 days
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://${BUCKET_NAME}
```

**Archive to Nearline Storage:**
```bash
# Move logs older than 90 days to cheaper Nearline storage
cat > lifecycle-archive.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle-archive.json gs://${BUCKET_NAME}
```

**Cost Savings:**
- Standard Storage: $0.020/GB/month
- Nearline Storage: $0.010/GB/month (50% cheaper, slightly slower access)

#### 5. Clean Up Old Container Images

**List Images in Artifact Registry:**
```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq \
  --format="table(image,createTime,updateTime)"
```

**Delete Old Images:**
```bash
# Delete specific image version
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:old-tag \
  --delete-tags

# Delete images older than 30 days (manual script)
# Create a cleanup script to run monthly
```

**Artifact Registry Storage Costs:**
- $0.10/GB/month
- Keeping 10 old images (~2.5 GB) = $0.25/month wasted

#### 6. Optimize Secret Manager Usage

**Current Secrets (Example):**
- notion-api-key
- gemini-api-key
- anthropic-api-key
- openai-api-key
- gmail-credentials-json
- gmail-token-json

**Total: 6 secrets × $0.06/month = $0.36/month**

**Optimization:**
- Delete unused LLM API secrets if you only use one provider
- Combine secrets where possible (use JSON for multiple keys)

**Example Combined Secret:**
```bash
# Create single API keys secret
cat > api-keys.json <<EOF
{
  "notion": "YOUR_NOTION_KEY",
  "gemini": "YOUR_GEMINI_KEY"
}
EOF

echo -n "$(cat api-keys.json)" | gcloud secrets create api-keys \
  --replication-policy="automatic" \
  --data-file=-

# Delete individual secrets
gcloud secrets delete notion-api-key
gcloud secrets delete gemini-api-key

# Savings: $0.12/month (reduced from 6 to 4 secrets)
```

**Trade-off:** Slightly more complex secret parsing in code.

#### 7. Choose Cost-Effective Regions

**Regional Pricing Differences (approximate):**
- us-central1 (Iowa): Lowest cost (baseline)
- us-east1, us-west1: Similar to us-central1
- europe-west1: ~10% more expensive
- asia-northeast1: ~15% more expensive

**Recommendation:** Use `us-central1` unless you have specific latency requirements.

#### 8. Monitor and Optimize LLM API Costs

**CollabIQ's Largest External Cost: LLM APIs**

**Gemini Pricing (Google AI):**
- Gemini 2.0 Flash: $0.075 / 1M input tokens, $0.30 / 1M output tokens
- Gemini 1.5 Pro: $1.25 / 1M input tokens, $5.00 / 1M output tokens

**Optimization Strategies:**
- Use Gemini Flash instead of Pro (10-20x cheaper)
- Reduce prompt size (remove unnecessary context)
- Cache LLM responses for similar emails
- Use structured output to reduce token usage

**Example Savings:**
```
100 emails/day, avg 500 tokens input + 200 tokens output per email

Gemini 1.5 Pro cost:
- Input: 100 * 500 * 30 days = 1.5M tokens → $1.88
- Output: 100 * 200 * 30 days = 0.6M tokens → $3.00
- Total: $4.88/month

Gemini 2.0 Flash cost:
- Input: 1.5M tokens → $0.11
- Output: 0.6M tokens → $0.18
- Total: $0.29/month

Savings: $4.59/month (94% reduction!)
```

**Switch to Flash Model:**
```bash
gcloud run jobs update JOB_NAME \
  --region=us-central1 \
  --update-env-vars="GEMINI_MODEL=gemini-2.0-flash-exp"
```

---

### Setting Up Budget Alerts

Prevent unexpected charges with budget alerts.

#### Creating a Budget via Console

1. **Navigate to Billing:**
   - Go to [console.cloud.google.com/billing/budgets](https://console.cloud.google.com/billing/budgets)
   - Click "Create Budget"

2. **Configure Budget:**
   - **Name:** "CollabIQ Monthly Budget"
   - **Projects:** Select your CollabIQ project
   - **Services:** All services (or specific: Cloud Run, Secret Manager, Cloud Storage)
   - **Time Range:** Monthly

3. **Set Budget Amount:**
   - **Budget type:** Specified amount
   - **Target amount:** $50/month (adjust based on usage)

4. **Set Alert Thresholds:**
   - 50% ($25) → Email warning
   - 75% ($37.50) → Email warning
   - 90% ($45) → Email alert
   - 100% ($50) → Email + Slack alert
   - 110% ($55) → Email + Slack + disable Cloud Scheduler (optional)

5. **Configure Notifications:**
   - Add email addresses
   - Add Pub/Sub topic (for automated actions)
   - Link to Slack/PagerDuty

6. **Save Budget**

#### Automated Budget Enforcement (Advanced)

**Create Pub/Sub Topic for Budget Alerts:**
```bash
gcloud pubsub topics create budget-alerts
```

**Create Cloud Function to Disable Job on Budget Exceeded:**
```python
# cloud_function/main.py
import os
from googleapiclient.discovery import build

def stop_jobs_on_budget_exceeded(data, context):
    """Cloud Function triggered by budget alert"""
    import base64
    import json

    budget_data = json.loads(base64.b64decode(data['data']).decode('utf-8'))
    cost_amount = budget_data['costAmount']
    budget_amount = budget_data['budgetAmount']

    # Stop jobs if 100% budget exceeded
    if cost_amount >= budget_amount:
        project_id = os.environ['GCP_PROJECT']
        region = 'us-central1'
        job_name = 'collabiq-processor'

        # Disable Cloud Scheduler job
        scheduler_client = build('cloudscheduler', 'v1')
        name = f'projects/{project_id}/locations/{region}/jobs/{job_name}'
        scheduler_client.projects().locations().jobs().pause(name=name).execute()

        print(f"Budget exceeded! Paused job: {job_name}")
```

**Deploy Cloud Function:**
```bash
gcloud functions deploy budget-enforcer \
  --runtime=python312 \
  --trigger-topic=budget-alerts \
  --entry-point=stop_jobs_on_budget_exceeded \
  --region=us-central1
```

**Link Budget to Pub/Sub Topic:**
- In budget configuration, select "Pub/Sub topic"
- Choose `budget-alerts` topic

---

### Estimating Monthly Costs

Use this worksheet to estimate your CollabIQ costs:

#### Cost Estimation Worksheet

**1. Execution Frequency:**
```
Executions per day: _____ (e.g., 288 for every 5 minutes)
Days per month: 30
Total executions: _____ * 30 = _____
```

**2. Execution Duration:**
```
Average runtime per execution: _____ seconds (e.g., 120 seconds)
Total compute seconds: _____ executions * _____ seconds = _____
```

**3. Resource Configuration:**
```
CPU allocation: _____ vCPU (e.g., 1)
Memory allocation: _____ GB (e.g., 0.5)
```

**4. Compute Costs:**
```
CPU cost: _____ seconds * _____ vCPU * $0.00002400 = $_____
Memory cost: _____ seconds * _____ GB * $0.00000250 = $_____
Total compute: $_____
```

**5. Additional Costs:**
```
Secret Manager: _____ secrets * $0.06 = $_____
Cloud Storage: _____ GB * $0.02 = $_____
Artifact Registry: _____ GB * $0.10 = $_____
Total additional: $_____
```

**6. Total Estimated Cost:**
```
Compute: $_____
Additional: $_____
Grand Total: $_____ per month
```

#### Example Calculations

**Scenario 1: Light Usage (Every 15 minutes)**
```
Executions: 96/day * 30 = 2,880/month
Runtime: 60 seconds each
CPU: 0.5 vCPU
Memory: 256 MB (0.25 GB)

Compute seconds: 2,880 * 60 = 172,800
CPU cost: 172,800 * 0.5 * $0.00002400 = $2.07
Memory cost: 172,800 * 0.25 * $0.00000250 = $0.11
Secret Manager: 4 * $0.06 = $0.24
Cloud Storage: 0.5 GB * $0.02 = $0.01

Total: ~$2.43/month (well within free tier!)
```

**Scenario 2: Moderate Usage (Every 5 minutes)**
```
Executions: 288/day * 30 = 8,640/month
Runtime: 120 seconds each
CPU: 1 vCPU
Memory: 512 MB (0.5 GB)

Compute seconds: 8,640 * 120 = 1,036,800
CPU cost: 1,036,800 * 1 * $0.00002400 = $24.88
Memory cost: 1,036,800 * 0.5 * $0.00000250 = $1.30
Secret Manager: 6 * $0.06 = $0.36
Cloud Storage: 1 GB * $0.02 = $0.02

Total: ~$26.56/month
```

**Scenario 3: Heavy Usage (Every minute)**
```
Executions: 1,440/day * 30 = 43,200/month
Runtime: 120 seconds each
CPU: 1 vCPU
Memory: 1 GB

Compute seconds: 43,200 * 120 = 5,184,000
CPU cost: 5,184,000 * 1 * $0.00002400 = $124.42
Memory cost: 5,184,000 * 1 * $0.00000250 = $12.96
Secret Manager: 6 * $0.06 = $0.36
Cloud Storage: 2 GB * $0.02 = $0.04

Total: ~$137.78/month
```

---

### Cost Monitoring and Reporting

**View Current Costs:**
```bash
# Open billing reports
open https://console.cloud.google.com/billing/reports
```

**Export Billing Data to BigQuery (for analysis):**
1. Go to [console.cloud.google.com/billing/export](https://console.cloud.google.com/billing/export)
2. Enable "BigQuery Export"
3. Create dataset: `billing_export`
4. Run SQL queries to analyze costs:

```sql
-- Daily Cloud Run costs
SELECT
  DATE(usage_start_time) as date,
  service.description,
  SUM(cost) as total_cost
FROM `project.billing_export.gcp_billing_export_v1_*`
WHERE service.description LIKE '%Cloud Run%'
GROUP BY date, service.description
ORDER BY date DESC
LIMIT 30;
```

**Set Up Cost Anomaly Detection:**
- Go to [console.cloud.google.com/billing/anomaly](https://console.cloud.google.com/billing/anomaly)
- Enable anomaly detection
- Receive alerts for unexpected cost spikes

---

### Best Practices for Cost Management

1. **Start with conservative execution frequency** (e.g., every 15 minutes)
2. **Monitor actual usage** for the first month
3. **Right-size resources** based on metrics
4. **Set up budget alerts** before deploying to production
5. **Review billing reports monthly** to identify optimization opportunities
6. **Use Gemini Flash** instead of Pro for LLM calls
7. **Clean up old container images** quarterly
8. **Archive or delete old logs** after 30-90 days
9. **Consider regional pricing** when choosing deployment region
10. **Leverage free tiers** (Cloud Run, Secret Manager, Cloud Storage)

---

## Update and Redeployment

This section covers how to update your CollabIQ deployment with new features, bug fixes, or configuration changes.

### Updating the Application Code

#### 1. Make Changes Locally

```bash
# Navigate to project directory
cd /Users/jlim/Projects/CollabIQ

# Make code changes
# ... edit files ...

# Test locally
uv run pytest
uv run collabiq config validate
```

#### 2. Build New Docker Image

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export NEW_VERSION="v1.1.0"  # Increment version
export GIT_COMMIT=$(git rev-parse --short HEAD)

# Build new image
docker build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${NEW_VERSION} \
  -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest \
  -t us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${GIT_COMMIT} \
  .
```

#### 3. Test New Image Locally

```bash
# Test help command
docker run --rm \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${NEW_VERSION} \
  --help

# Test config validation (with secrets)
docker run --rm \
  -e NOTION_API_KEY="your-test-key" \
  -e GEMINI_API_KEY="your-test-key" \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${NEW_VERSION} \
  config validate
```

#### 4. Push New Image to Artifact Registry

```bash
# Push all tags
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${NEW_VERSION}
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${GIT_COMMIT}
```

#### 5. Update Cloud Run Job

```bash
# Update job to use new image
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:${NEW_VERSION}

# Or update to latest tag (if you always want newest)
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:latest
```

**Expected Output:**
```
✓ Deploying... Done.
  ✓ Updating Job...
Job [collabiq-processor] has been updated.
```

#### 6. Verify Update

```bash
# Check job configuration
gcloud run jobs describe collabiq-processor \
  --region=${REGION} \
  --format="value(template.template.containers[0].image)"

# Should output: us-central1-docker.pkg.dev/PROJECT_ID/collabiq/collabiq:v1.1.0

# Test execution with new version
gcloud run jobs execute collabiq-processor --region=${REGION}
```

---

### Updating Environment Variables or Secrets

#### Update Environment Variables

```bash
# Update single environment variable
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --update-env-vars="LOG_LEVEL=DEBUG"

# Update multiple variables
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --update-env-vars="LOG_LEVEL=DEBUG,SELECTED_MODEL=claude"

# Remove environment variable
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --remove-env-vars="DEPRECATED_VAR"
```

#### Update Secrets

**Option 1: Add New Version to Existing Secret**
```bash
# Update API key (creates new version)
echo -n "NEW_API_KEY" | gcloud secrets versions add notion-api-key --data-file=-

# If using :latest in job config, it will automatically use new version
# If pinned to specific version, update job:
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --update-secrets="NOTION_API_KEY=notion-api-key:latest"
```

**Option 2: Create New Secret**
```bash
# Create new secret
echo -n "NEW_KEY" | gcloud secrets create new-api-key \
  --replication-policy="automatic" \
  --data-file=-

# Grant access to service account
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding new-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# Add to job
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --update-secrets="NEW_API_KEY=new-api-key:latest"
```

---

### Rolling Back to Previous Version

If a deployment causes issues, roll back to a known-good version.

#### Identify Previous Version

```bash
# List all image tags
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq \
  --format="table(image,tags,createTime)" \
  --sort-by=~createTime

# Identify the previous version (e.g., v1.0.0)
```

#### Rollback to Previous Image

```bash
# Update job to use previous version
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/collabiq/collabiq:v1.0.0
```

#### Verify Rollback

```bash
# Check current image
gcloud run jobs describe collabiq-processor \
  --region=${REGION} \
  --format="value(template.template.containers[0].image)"

# Test execution
gcloud run jobs execute collabiq-processor --region=${REGION}
```

#### Rollback Environment Variables

```bash
# View current configuration
gcloud run jobs describe collabiq-processor \
  --region=${REGION} \
  --format="yaml(template.template.containers[0].env)"

# Reset to previous values
gcloud run jobs update collabiq-processor \
  --region=${REGION} \
  --set-env-vars="LOG_LEVEL=INFO,SELECTED_MODEL=gemini"
```

---

### CI/CD Integration (Future)

Automate deployment with GitHub Actions or Cloud Build.

#### GitHub Actions Workflow (Example)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'Dockerfile'
      - 'pyproject.toml'

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  JOB_NAME: collabiq-processor

jobs:
  deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev

      - name: Build Docker image
        run: |
          docker build \
            --platform linux/amd64 \
            -t ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/collabiq/collabiq:${{ github.sha }} \
            -t ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/collabiq/collabiq:latest \
            .

      - name: Push Docker image
        run: |
          docker push ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/collabiq/collabiq:${{ github.sha }}
          docker push ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/collabiq/collabiq:latest

      - name: Deploy to Cloud Run Job
        run: |
          gcloud run jobs update ${{ env.JOB_NAME }} \
            --region=${{ env.REGION }} \
            --image=${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/collabiq/collabiq:${{ github.sha }}

      - name: Test deployment
        run: |
          gcloud run jobs execute ${{ env.JOB_NAME }} --region=${{ env.REGION }} --wait
```

**Setup Steps:**
1. Create Workload Identity Federation for GitHub Actions
2. Add secrets to GitHub repository settings
3. Push to main branch to trigger deployment

#### Cloud Build Configuration (Example)

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--platform=linux/amd64'
      - '-t'
      - '$_REGION-docker.pkg.dev/$PROJECT_ID/collabiq/collabiq:$COMMIT_SHA'
      - '-t'
      - '$_REGION-docker.pkg.dev/$PROJECT_ID/collabiq/collabiq:latest'
      - '.'

  # Push Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - '$_REGION-docker.pkg.dev/$PROJECT_ID/collabiq/collabiq'

  # Deploy to Cloud Run Job
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'jobs'
      - 'update'
      - '$_JOB_NAME'
      - '--region=$_REGION'
      - '--image=$_REGION-docker.pkg.dev/$PROJECT_ID/collabiq/collabiq:$COMMIT_SHA'

substitutions:
  _REGION: us-central1
  _JOB_NAME: collabiq-processor

options:
  logging: CLOUD_LOGGING_ONLY
```

**Trigger Build:**
```bash
# Manual trigger
gcloud builds submit --config=cloudbuild.yaml

# Automatic trigger on git push
gcloud builds triggers create github \
  --repo-name=CollabIQ \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml
```

---

### Update Checklist

Use this checklist for every deployment:

**Pre-Deployment:**
- [ ] Code changes tested locally
- [ ] All tests passing (`uv run pytest`)
- [ ] Version number incremented in tags
- [ ] Git commit created and pushed
- [ ] Changelog/release notes updated

**Build & Push:**
- [ ] Docker image built for linux/amd64
- [ ] Image tested locally
- [ ] Image pushed to Artifact Registry
- [ ] Image tags include version, commit hash, and latest

**Deployment:**
- [ ] Cloud Run Job updated with new image
- [ ] Environment variables reviewed and updated if needed
- [ ] Secrets rotated if necessary
- [ ] Resource allocation (CPU/memory) reviewed

**Post-Deployment:**
- [ ] Manual execution test successful
- [ ] Logs checked for errors
- [ ] Monitoring dashboard reviewed
- [ ] Budget and cost reviewed
- [ ] Rollback plan documented

---

### Deployment Best Practices

1. **Always Tag Images with Versions:**
   - Use semantic versioning (v1.0.0, v1.1.0)
   - Include git commit hash for traceability
   - Keep `latest` tag updated

2. **Test Before Deploying:**
   - Run tests locally
   - Test Docker image locally
   - Consider blue-green deployment for critical updates

3. **Deploy During Low-Traffic Periods:**
   - Schedule updates during off-hours
   - Avoid deployments during peak usage

4. **Monitor After Deployment:**
   - Watch logs for 15-30 minutes post-deployment
   - Check execution success rate
   - Verify resource utilization is normal

5. **Keep Rollback Plan Ready:**
   - Document previous working version
   - Have rollback command ready to execute
   - Test rollback procedure quarterly

6. **Use CI/CD for Production:**
   - Automate build and deployment process
   - Add automated testing to pipeline
   - Require code review before deployment

7. **Version Environment Variables:**
   - Document configuration changes in git
   - Use infrastructure-as-code (Terraform) for complex setups

8. **Communicate Deployments:**
   - Notify team of deployment schedule
   - Document what changed in each deployment
   - Track deployments in project management tool

---

## Quick Reference

Essential commands for managing your CollabIQ deployment.

### Project Setup
```bash
# Set environment variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export JOB_NAME="collabiq-processor"
export BUCKET_NAME="${PROJECT_ID}-collabiq-data"
```

### Docker Operations
```bash
# Build and push image (recommended for Apple Silicon - uses buildx)
docker buildx build --platform linux/amd64 \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest \
  --push .

# Alternative: Build locally then push (two steps)
docker build --platform linux/amd64 \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest

# Test image locally
docker run --rm ${REGION}-docker.pkg.dev/${PROJECT_ID}/collabiq-repo/collabiq:latest --help

# Configure Docker authentication for registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### Cloud Run Job Management
```bash
# List all jobs (across all regions)
gcloud run jobs list

# Create job
gcloud run jobs create ${JOB_NAME} --image=IMAGE_URL --region=${REGION} ...

# Update job (use this instead of delete+create for configuration changes)
gcloud run jobs update ${JOB_NAME} --region=${REGION} --image=NEW_IMAGE_URL

# Execute job manually
gcloud run jobs execute ${JOB_NAME} --region=${REGION}

# Execute and wait for completion
gcloud run jobs execute ${JOB_NAME} --region=${REGION} --wait

# List executions
gcloud run jobs executions list --job=${JOB_NAME} --region=${REGION}

# View job details
gcloud run jobs describe ${JOB_NAME} --region=${REGION}

# Delete job (required before creating job with same name in different region)
gcloud run jobs delete ${JOB_NAME} --region=${REGION}

# Delete Cloud Scheduler job (if exists)
gcloud scheduler jobs delete ${JOB_NAME}-scheduler --location=${REGION}
```

**Important Notes on Job Management:**
- You **cannot** have two jobs with the same name in different regions
- To move a job to a new region: delete the old job first, then create in the new region
- Use `update` for configuration changes (secrets, env vars, image) - faster than delete+create
- Scheduler jobs are region-specific and linked to Cloud Run jobs in the same region

### Logging and Monitoring
```bash
# Tail logs in real-time
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}"

# View recent logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}" --limit=50

# Check execution status
gcloud run jobs executions describe EXECUTION_NAME --region=${REGION}
```

### Secret Management
```bash
# Create secret
echo -n "SECRET_VALUE" | gcloud secrets create SECRET_NAME --replication-policy="automatic" --data-file=-

# Update secret
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# View secret (requires permissions)
gcloud secrets versions access latest --secret=SECRET_NAME
```

### Billing and Cost Management
```bash
# View billing reports
open https://console.cloud.google.com/billing/reports

# List current costs
gcloud billing accounts list

# View budget alerts
open https://console.cloud.google.com/billing/budgets
```

### Troubleshooting
```bash
# View logs for errors
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME} AND severity>=ERROR" --limit=20

# Check job configuration
gcloud run jobs describe ${JOB_NAME} --region=${REGION}

# Test authentication
gcloud auth list
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# View quota usage
open https://console.cloud.google.com/iam-admin/quotas
```

### Useful Links
- [Google Cloud Console](https://console.cloud.google.com)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Logging](https://console.cloud.google.com/logs)
- [Cloud Monitoring](https://console.cloud.google.com/monitoring)
- [Billing Reports](https://console.cloud.google.com/billing/reports)
- [Artifact Registry](https://console.cloud.google.com/artifacts)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager)

---

---

## Next Steps

Once you've completed the prerequisites and tools installation:

1. **Verify Your Setup:**
   ```bash
   # Check all tools are installed
   gcloud version
   docker --version

   # Verify project and APIs
   gcloud config list
   gcloud services list --enabled
   ```

2. **Prepare for Containerization:**
   - Ensure CollabIQ is working locally
   - Review your configuration and secrets
   - Familiarize yourself with Docker basics

3. **Bookmark Useful Resources:**
   - [Google Cloud Console](https://console.cloud.google.com)
   - [Cloud Run Documentation](https://cloud.google.com/run/docs)
   - [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)

---

**Last Updated:** 2025-11-27
**Version:** 1.0.0
**Phase:** Final Phase Complete (Prerequisites, Containerization, Cloud Run Deployment, Troubleshooting, Monitoring, Cost Optimization)
**Status:** Production Ready
