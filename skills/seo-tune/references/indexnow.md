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

When you publish, update, OR remove a page, send its URL. Single URL (GET) — the `url`
value must be percent-encoded, or any `&`, `#`, space or non-ASCII character in the path
will break the query string:

```
# encode the URL first, e.g.:
#   ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "SITE_URL/new-page/")
curl "https://api.indexnow.org/indexnow?url=$ENC&key=<key>"
```

Batch (POST, up to 10000 URLs) — the robust form for a build script. `<host>` is your bare
hostname (the host part of `SITE_URL`, no scheme), and EVERY url in `urlList` must be on
that exact host — subdomains count as separate hosts and need their own request:

```
curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "<host>",
    "key": "<key>",
    "keyLocation": "SITE_URL/<key>.txt",
    "urlList": [
      "SITE_URL/page-1/",
      "SITE_URL/page-2/"
    ]
  }'
```

Ping just ONE endpoint — participating engines share submissions with each other, so there
is no need to hit several. `api.indexnow.org` fans out to all participants; hitting
`https://yandex.com/indexnow` or `https://www.bing.com/indexnow` directly with the same
payload is equivalent, not additional.

## 4. Wire it into your publish flow

Add the ping to whatever runs on deploy (a `deploy.sh`, a CI step, a git hook): after the
site is live, POST the changed URLs. Status codes: `200` = received and the key was
validated; `202` = received but key validation is still PENDING — NOT a final success (if
your key file is missing or wrong, the URLs are dropped afterwards). `400` bad request,
`403` key not valid, `422` a url/host mismatch, `429` too many requests.

## Notes

- **DO submit removed / redirected URLs too.** When a page is deleted (404/410) or moved
  (301/302), ping the OLD URL — that is how you tell engines to drop the stale page, so it
  leaves the index faster. IndexNow means "this URL changed", and "this URL is gone" is a
  change. (Only skip URLs that were never meant to be indexed at all.)
- All URLs in one request must belong to the same host as `host` / `keyLocation`;
  subdomains are separate hosts with their own key file and request.
- Keep the key file in place forever; if it disappears, pings start failing.
- IndexNow speeds up *discovery*; ranking still depends on the SEO/AEO work.

Sources: [IndexNow protocol](https://www.indexnow.org/documentation),
[IndexNow FAQ](https://www.indexnow.org/faq),
[Yandex IndexNow reference](https://yandex.com/support/webmaster/en/indexnow/reference).
