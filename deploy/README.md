# Deploy — herosiege.clockmost.com

Stateless read-only SPA + API. VPN-only, Authentik forward-auth. No DB, no
secrets, no volumes.

## 1. Vendor the repo

```
cd /home/clockmost-infra/projects
mkdir -p herosiege-filter/app
rsync -a --delete \
  --exclude .git --exclude .venv --exclude node_modules --exclude dist \
  --exclude 'app/backend/.venv' --exclude 'app/backend/static' \
  ~/Projects/hero-siege-filter/ herosiege-filter/app/
cp herosiege-filter/app/deploy/compose.yaml herosiege-filter/compose.yaml
```

(Re-run the rsync + bump the image tag to ship changes, like `caddy` /
`clockmost-console`.)

## 2. Caddy route  (`projects/caddy/Caddyfile`)

```
@herosiege host herosiege.clockmost.com
handle @herosiege {
    import sec_headers
    import authentik_forward
    reverse_proxy herosiege-filter:8000
}
```

`docker exec caddy caddy reload --config /etc/caddy/Caddyfile`

## 3. Authentik  (`projects/authentik/blueprints/forward-auth.yaml`)

Add a proxy provider `provider-herosiege` / app `app-herosiege` for
`https://herosiege.clockmost.com`, list it on the embedded-outpost `providers`,
and bind the app to `authentik Admins` (+ an `hs-filter-users` group for
kuri / andre) in `blueprints/access.yaml`.

## 4. Bring up

```
cd /home/clockmost-infra/projects/herosiege-filter
docker compose up -d --build
curl -s http://herosiege-filter:8000/api/health   # from inside the edge net
```

Commit the infra repo. `clockmost-infra` is DNS-local (`pihole custom-dns`); the
tunnel is **not** extended to this host — VPN only.

## Going public later

Drop the `import authentik_forward` line from the Caddy block, reload. The app
has no auth of its own and exposes nothing but "pick a build → download a text
file", so that's the whole change.
