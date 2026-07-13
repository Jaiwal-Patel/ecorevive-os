# DigitalOcean Deployment

The simplest Student Pack path is a small Ubuntu Droplet running Docker Compose. Student offers change, so verify the current Pack entitlement before creating paid resources.

## Provision

1. Create an Ubuntu LTS Droplet.
2. Add an SSH key; disable password SSH after verification.
3. Reserve a static IP if needed.
4. Point a real domain's DNS `A` record to the server.
5. Install Docker Engine and the Compose plugin.
6. Clone the private repository.
7. Copy `.env.production.example` to `.env.production` and replace every placeholder.
8. Run `./scripts/deploy_production.sh`.
9. Run `./scripts/bootstrap_production_governance.sh` once.
10. Verify HTTPS, backups, email and health checks.

## Initial demo without a domain

Use GitHub Codespaces for a temporary authenticated demonstration. Do not use an unencrypted public IP deployment for real household data.
