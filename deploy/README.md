# Deploy

Single stateless container — SPA + API on port 8000. No database, no volumes, no
secrets.

```sh
docker compose -f deploy/compose.yaml up -d --build
curl -s localhost:8000/api/health
```

Or without compose:

```sh
docker build -f app/Dockerfile -t hero-siege-filter .
docker run --rm -p 8000:8000 hero-siege-filter
```

Put it behind any reverse proxy / TLS terminator you like. The app has no auth of
its own — it only reads a bundled catalog and returns a generated text file — so
front it with your proxy's auth if you don't want it public.
