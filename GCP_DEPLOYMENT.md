# Deploy CAT Cost Intelligence on Google Cloud

This guide deploys the demo to one Google Compute Engine VM at **https://cat-proto.duckdns.org**. It uses Docker Compose, Caddy for automatic HTTPS, the existing Nginx frontend, FastAPI, and PostgreSQL.

## Recommended instance

Use an **`e2-standard-2` VM: 2 vCPUs and 8 GB RAM**, with a **30 GB balanced persistent boot disk** and Ubuntu 24.04 LTS.

This is the recommended demo size because the VM runs four containers and also builds the Node and Python images in place. The steady-state resource limits in `docker-compose.prod.yaml` total roughly 4 GB, leaving capacity for the operating system, Docker, image builds, filesystem cache, and short traffic bursts. Google documents `e2-standard-2` as 2 vCPUs and 8 GB RAM; E2 is its cost-optimized general-purpose family. See [Google Cloud E2 machine types](https://docs.cloud.google.com/compute/docs/general-purpose-machines).

- **Minimum for private testing:** `e2-medium`, 4 GB RAM. Build images elsewhere or add swap; concurrent image builds can exhaust memory.
- **Recommended demo:** `e2-standard-2`, 8 GB RAM.
- **Move to `e2-standard-4`:** if the VM regularly exceeds 65% CPU, PostgreSQL grows materially, or more than roughly 20–30 concurrent demo users are expected.

This is a single-VM demo architecture, not a high-availability production design. The database and application share one failure domain.

## Included production configuration

[`docker-compose.prod.yaml`](docker-compose.prod.yaml) provides:

- Only ports 80 and 443 exposed publicly.
- PostgreSQL and FastAPI reachable only inside the Compose network.
- Automatic TLS and HTTP-to-HTTPS redirects through Caddy.
- Persistent volumes for PostgreSQL and Caddy certificates.
- Restart policies, health checks, and rotating 10 MB container logs.
- CPU and memory limits based on Docker's [Compose resource specification](https://docs.docker.com/reference/compose-file/deploy/).
- VM-attached Google service-account authentication, avoiding a JSON key inside the repository or VM filesystem.

## 1. Google Cloud preparation

Set local CLI values:

```bash
export PROJECT_ID="your-project-id"
export REGION="asia-south1"
export ZONE="asia-south1-a"
gcloud config set project "$PROJECT_ID"
gcloud services enable compute.googleapis.com aiplatform.googleapis.com
```

Create a VM service account and grant only Vertex AI access:

```bash
gcloud iam service-accounts create cat-proto-vm \
  --display-name="CAT prototype VM"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:cat-proto-vm@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

Reserve a regional static IP, then create the VM:

```bash
gcloud compute addresses create cat-proto-ip --region="$REGION"

gcloud compute instances create cat-proto \
  --zone="$ZONE" \
  --machine-type=e2-standard-2 \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-balanced \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --address=cat-proto-ip \
  --service-account="cat-proto-vm@${PROJECT_ID}.iam.gserviceaccount.com" \
  --scopes=cloud-platform \
  --tags=cat-proto-web
```

Google's current VM creation reference is [Create and start a Compute Engine instance](https://docs.cloud.google.com/compute/docs/instances/create-start-instance).

Allow only web traffic to the tagged VM:

```bash
gcloud compute firewall-rules create allow-cat-proto-web \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80,tcp:443,udp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=cat-proto-web
```

Use Google Cloud IAP or a tightly scoped source range for SSH rather than exposing port 22 globally. See [Google Cloud firewall rules](https://docs.cloud.google.com/firewall/docs/using-firewalls).

## 2. Point DuckDNS at the VM

Read the reserved address:

```bash
export STATIC_IP="$(gcloud compute addresses describe cat-proto-ip --region="$REGION" --format='value(address)')"
echo "$STATIC_IP"
```

In DuckDNS, create or select the `cat-proto` subdomain and set it to this IP. The equivalent API request is:

```bash
curl "https://www.duckdns.org/update?domains=cat-proto&token=YOUR_DUCKDNS_TOKEN&ip=${STATIC_IP}"
```

Do not commit the DuckDNS token. Verify DNS before starting Caddy:

```bash
dig +short cat-proto.duckdns.org
```

The returned address must equal `$STATIC_IP`. DuckDNS documents the update endpoint in its [official API specification](https://www.duckdns.org/spec.jsp).

## 3. Install Docker on the VM

Connect using the Google Cloud console or `gcloud compute ssh cat-proto --zone="$ZONE"`, then install Docker Engine from Docker's official Ubuntu repository. Follow [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/); do not use the convenience script for a shared demo host.

After installation:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker version
docker compose version
```

## 4. Copy and configure the application

Clone or copy this repository to the VM and enter it:

```bash
git clone YOUR_REPOSITORY_URL cat-ci-proto
cd cat-ci-proto
```

Create `.env` without committing it:

```bash
cat > .env <<EOF
POSTGRES_DB=cat_ci
POSTGRES_USER=cat_ci
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DEMO_AUTH_SECRET=$(openssl rand -hex 32)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
GEMINI_MODEL=gemini-2.5-flash
EOF
chmod 600 .env
```

Replace `your-project-id`. The production Compose file deliberately does not mount a service-account JSON key. Google authentication will use the service account attached to the VM.

## 5. Start and verify

Validate and start the production stack:

```bash
docker compose --env-file .env -f docker-compose.prod.yaml config
docker compose --env-file .env -f docker-compose.prod.yaml up -d --build
docker compose -f docker-compose.prod.yaml ps
docker compose -f docker-compose.prod.yaml logs --tail=100 caddy backend
```

Caddy will request and renew the TLS certificate automatically once DNS resolves and inbound ports 80/443 reach the VM. Caddy documents automatic certificate management in [Automatic HTTPS](https://caddyserver.com/docs/caddyfile/options#auto-https), and the proxy behavior in [reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

Verify:

```bash
curl -I https://cat-proto.duckdns.org
curl https://cat-proto.duckdns.org/api/v1/health
```

Then open **https://cat-proto.duckdns.org**.

## Operations

View resource usage:

```bash
docker stats
df -h
```

Deploy an update:

```bash
git pull --ff-only
docker compose --env-file .env -f docker-compose.prod.yaml up -d --build
docker image prune -f
```

Back up PostgreSQL before significant changes:

```bash
mkdir -p backups
docker compose --env-file .env -f docker-compose.prod.yaml exec -T postgres \
  pg_dump -U cat_ci -d cat_ci -Fc > "backups/cat-ci-$(date +%F-%H%M).dump"
```

Also enable scheduled snapshots for the VM's persistent disk. Keep at least one database backup outside this VM.

## Security note

This repository still uses demo authentication and fixed demo passwords. HTTPS protects transport but does not turn the demo login into production-grade identity. Restrict the firewall by source IP, place the site behind an identity-aware proxy, or replace demo authentication with SSO before exposing sensitive or real procurement data.
