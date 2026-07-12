# Local Deployment

## Shape

```text
Knowledge Fabric
Intent Fabric
Private Adapter Service
```

## Suggested environment variables

```text
KNOWLEDGE_FABRIC_URL=http://localhost:8080
INTENT_FABRIC_URL=http://localhost:8081
ADAPTER_ENV=local
```

## How to run (no TLS — dev only)

```bash
docker compose -f deploy/local/docker-compose.yml up --build
curl http://localhost:8080/healthz
```

## How to run with TLS (Caddy reverse proxy)

```bash
export ADAPTER_API_KEY="$(openssl rand -hex 32)"
docker compose -f deploy/local/docker-compose-tls.yml up --build
curl https://localhost/healthz
curl https://localhost/ -H "Authorization: Bearer $ADAPTER_API_KEY"
```

Caddy automatically provisions a localhost self-signed certificate.
For a real domain, replace `localhost` in `deploy/local/Caddyfile` with
your domain name and Caddy will fetch a Let's Encrypt certificate automatically.

## Notes

- Keep local deployments private.
- Do not commit secrets or internal endpoints.
- Start with read-only adapters before enabling write actions.
