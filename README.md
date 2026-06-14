# nuuson-api-testing

POC backend service for the nuuson.dev API platform. Runs on VPS, accessible internally at `testing-internal.nuuson.dev` (CF Access gated) and publicly via `api.nuuson.dev/v1/testing/` (API key required).

This repo is also the reference implementation for the sandbox → prod deployment pattern. New service repos should follow the same structure.

## Local development

```bash
conda create -n nuuson-api-testing python=3.14
conda activate nuuson-api-testing
pip install -r requirements-dev.txt
```

Run the service:
```bash
uvicorn app.main:app --reload
# http://localhost:8000
```

Run tests:
```bash
pytest
```

## Deployment pattern

This repo uses a **sandbox → main promotion** workflow:

- `sandbox` branch → deploys to `testing-sandbox-internal.nuuson.dev` → runs smoke tests → opens a PR to `main` if none exists
- `main` branch → deploys to `testing-internal.nuuson.dev` (prod)

PRs from `sandbox` must pass CI before they can be merged. Set `CI/CD / smoke-test-sandbox` as a required status check on `main` in repo settings.

## One-time setup for a new service repo using this pattern

### 1. docker-compose.yml

Commit a `docker-compose.yml` to the repo root. CI copies it to `~/projects/<project>/` on the VPS automatically and writes `.env` from Vault — no manual VPS setup needed.

The `.env` is populated from `secret/projects/<project>/env` in Vault. At minimum it needs `TRAEFIK_ROUTER` and `TRAEFIK_HOST` (Traefik routing labels). Add any app-specific secrets there too. Shared secrets (e.g. `secret/shared/gemini`) are appended via `shared_vault_paths` in the CI workflow.

### 2. Cloudflare Access

Internal subdomains (`testing-internal.nuuson.dev`, `testing-sandbox-internal.nuuson.dev`) are protected by Cloudflare Access. The CF Access application and service token policy are managed by Tofu in `nwmain/infra/environments/prod/`.

### 3. Vault roles

Two JWT roles (prod + sandbox) must exist in Vault, each with a policy granting read on the project's secrets path and any shared paths:

```bash
vault policy write project-nuuson-api-testing - <<'EOF'
path "secret/data/projects/nuuson-api-testing/*" { capabilities = ["read", "list"] }
path "secret/data/shared/gemini" { capabilities = ["read"] }
EOF

vault write auth/jwt/role/project-nuuson-api-testing \
  role_type=jwt bound_audiences="https://vault.nwilson5.dev" \
  user_claim=sub policies=project-nuuson-api-testing ttl=15m

# Repeat for -sandbox variant
```

### 4. GitHub repo config

**Variables:**
- `VAULT_ADDR` — `https://vault.nwilson5.dev`

**Secrets:**
- `VPS_HOST` — VPS IP or hostname
- `VPS_SSH_KEY` — private key for the deploy user (`~/.ssh/deploy_nwmain`)
- `CF_ACCESS_CLIENT_ID` — CF Access service token client ID (from `nwmain` Tofu output `gateway_access_client_id`)
- `CF_ACCESS_CLIENT_SECRET` — CF Access service token client secret

### 5. Gateway route

Add one line to `nuuson-api-gateway/src/routes.js` and open a PR:

```js
'/v1/my-service/': 'https://my-service-internal.nuuson.dev',
```

## Testing

Use the Jupyter notebook in `nwmain/notebooks/sandbox.ipynb` for interactive testing. Set `BASE_URL` to the sandbox or prod internal URL. See `nwmain/notebooks/README.md` for setup.

Public endpoint (requires API key from nuuson-api-admin):
```bash
curl -s -H "Authorization: Bearer nuu_..." https://api.nuuson.dev/v1/testing/hello | jq .
```

## CI/CD

| Branch | Triggered by | Jobs |
|---|---|---|
| `sandbox` or `main` | push | validate → build → push image to ghcr.io |
| `sandbox` | push | + deploy sandbox → smoke test → open promotion PR |
| `main` | push | + deploy prod |
| any | pull_request | validate only |
