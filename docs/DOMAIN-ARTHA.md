# Artha canonical domain

Application: https://artha.rifqisetiawan.my.id
API base: https://artha.rifqisetiawan.my.id/api/v1
API docs: https://artha.rifqisetiawan.my.id/docs
Health: https://artha.rifqisetiawan.my.id/health

DNS already resolves through the existing wildcard to this VPS. Caddy manages automatic HTTPS for the explicit Artha hostname. The frontend uses the relative /api/v1 base, so no cross-domain credentials are needed.

The tracked deploy/caddy/artha.caddy replaces the gateway conf.d/imporjaga.caddy route. Both previous frontend and API domains redirect with HTTP308 to the same path/query on Artha. HTTP methods are preserved. Existing localStorage login tokens belong to the old origin; sign in normally on the new domain.

Append the Artha HTTPS origin to runtime CORS_ALLOWED_ORIGINS before restarting only the application API. Preserve any existing origins. Back up gateway route and environment before applying; validate the full gateway config and reload gracefully. No database, SMTP, AI gateway, or unrelated routes change.
