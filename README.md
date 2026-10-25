# saadaltamari.com

Personal site of Saad Tamari, AI engineer in Amman. It's an exact export of the design canvas, served as a static site by a Cloudflare Worker.

## Layout

| Path | What it is |
| --- | --- |
| `public/` | **The deployed site.** Generated, so don't edit it by hand |
| `design-source/` | Original design files (`*.dc.html`, `site.css`, `motion.js`, `canvas.json`, CVs, logos). The source of truth |
| `static/` | Hand-written files copied into `public/` as they are |
| `tools/build.py` | Builds `public/` from `design-source/` + `static/` |
| `tools/prerender.cjs` | Bakes the rendered HTML into every page and writes `llms-full.txt` |
| `wrangler.jsonc` | Cloudflare Worker config (static assets from `public/`, custom domain) |

`static/` holds:

- `dc-runtime.js`, the component runtime (bundles React, MIT licence);
- `_headers` and `_redirects`;
- the 404 page, icons, web manifest, `humans.txt` and `.well-known/security.txt`;
- the images in `assets/img/`.

## What the build adds for search and AI assistants

- **Readable HTML for every crawler.** Each page ships its fully rendered HTML (`#ssr`). Crawlers that don't run JavaScript, which includes most AI crawlers, can read every word. In a browser, the live components replace it straight away.
- **Clean URLs and metadata:**
  - URLs like `/about` and `/case-mcp-hub`; the old `.html` paths redirect.
  - Canonical links on every page.
  - A unique title and description on every page.
  - Open Graph and Twitter cards. Every case study and article has its own 1200×630 preview card (its hero), in `static/assets/og/`.
- **Structured data (JSON-LD):**
  - `Person` and `WebSite` on Home, `ProfilePage` on About, and services as `Offer`s.
  - `TechArticle`/`BlogPosting` for the writing, `CreativeWork` for the case studies.
  - `BreadcrumbList` and `CollectionPage` lists.
- **Crawl files:**
  - `robots.txt` allows every search and AI crawler by name, and points to the sitemap.
  - `sitemap.xml`.
  - `llms.txt`, a plain summary and page index for language models.
  - `llms-full.txt`, every page as Markdown.
  - `feed.xml`, an Atom feed of the writing.
  - An image sitemap, hreflang tags, and an IndexNow key (`tools/indexnow.sh` pings Bing and the other IndexNow engines).
- **Security and caching headers:** HSTS, nosniff, referrer policy, frame options, and long cache times for images.

## Update the site

1. Change the pages in the design canvas and copy the changed files into `design-source/`.
2. Build:
   ```bash
   python3 tools/build.py
   npx wrangler dev --port 8799 &          # serve public/ locally
   node tools/prerender.cjs                # needs: npm i playwright && npx playwright install chromium
   node tools/ogcards.cjs                  # only when a hero changed: regenerates preview cards
   ```
3. Commit and push. Cloudflare redeploys `main` on its own.
4. Optional: `bash tools/indexnow.sh` to tell search engines the pages changed.

If you add a new image in the design canvas, add its `/_blob/<id>` and local path to `BLOBS` in `tools/build.py`.

## Hosting

The site is hosted on Cloudflare Workers (worker `saadaltamari`), connected to this repo with Workers Builds. The settings are: deploy command `npx wrangler deploy`, no build command. The custom domain `saadaltamari.com` is set in `wrangler.jsonc`.

Cloudflare zone settings that go with it:

- `www`: a proxied A record (`192.0.2.1`) plus the redirect rule "Redirect from WWW to root" (301, keeps the path and query).
- Always Use HTTPS and Crawler Hints are on.
- Email anti-spoofing: `v=spf1 -all` on the root and `v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s` on `_dmarc`. Change both if you start sending email from this domain.

To run it by hand instead:

```bash
npx wrangler login && npx wrangler deploy
```
