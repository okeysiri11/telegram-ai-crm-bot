# TLS certificates (HTTPS readiness)

Mount production certs here when a domain is attached:

- `fullchain.pem`
- `privkey.pem`

Then uncomment the `listen 443 ssl` server block in `nginx.conf` and add a compose volume:

```yaml
# nginx service volumes (example — enable only with real certs):
# - ./deploy/certs:/etc/nginx/certs:ro
# - ./deploy/certbot-www:/var/www/certbot:ro
```

Until a domain is connected, keep HTTP (:80) only. Do not enable the TLS block with empty files.
