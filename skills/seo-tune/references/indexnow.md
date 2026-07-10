# IndexNow — fast indexing on Yandex & Bing

Normally a search engine finds a new page whenever it next crawls you — days later.
IndexNow flips it: you PING the engine the moment you publish, and it comes fetch
the URL. Yandex and Bing support it (Google does not, but IndexNow-submitted URLs
still propagate widely). Free, no account.

## 1. Generate your key (once)

A key is a hex string, 8–128 chars. Generate one and keep it — it's yours, not a
secret, but don't reuse someone else's:

```
# any of these:
openssl rand -hex 16
# or
python3 -c "import secrets; print(secrets.token_hex(16))"
```

## 2. Publish the key file

Put the key in a text file at your site root, named `<key>.txt`, whose ONLY content
is the key itself:

```
SITE_URL/<key>.txt   →   <key>
```

This is how the engine verifies you own the domain.

## 3. Ping on every publish

When you publish or update a page, send its URL. Single URL (GET):

```
curl "https://api.indexnow.org/indexnow?url=SITE_URL/new-page/&key=<key>"
```

Batch (POST, up to 10000 URLs) — the robust form for a build script:

```
curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "example.com",
    "key": "<key>",
    "keyLocation": "SITE_URL/<key>.txt",
    "urlList": [
      "SITE_URL/page-1/",
      "SITE_URL/page-2/"
    ]
  }'
```

`api.indexnow.org` fans out to all participating engines; you can also hit
`https://yandex.com/indexnow` or `https://www.bing.com/indexnow` directly with the
same payload.

## 4. Wire it into your publish flow

Add the ping to whatever runs on deploy (a `deploy.sh`, a CI step, a git hook):
after the site is live, POST the changed URLs. A 200/202 means accepted.

## Notes

- Only ping URLs that are actually live and return 200 — pinging 404s hurts trust.
- Keep the key file in place forever; if it disappears, pings start failing.
- IndexNow speeds up *discovery*; ranking still depends on the SEO/AEO work.
