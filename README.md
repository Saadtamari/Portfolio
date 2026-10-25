# Saad Tamari · Portfolio

Personal site of Saad Tamari, AI engineer in Amman. It's a static site with no build step, so it's ready to deploy as it is.

It is an exact export of the Claude Design project. The pages use the same component runtime as the design canvas (`dc-runtime.js`), so the site looks and behaves exactly as it does there:

- light and dark mode;
- the accent colour and Ember mood;
- the scroll animations;
- the shipped-work marquee;
- the phone menu;
- the live clocks and tickers.

## What's in here

| Path | What it is |
| --- | --- |
| `index.html` | Home |
| `work.html`, `services.html`, `about.html`, `writing.html` | Main pages |
| `case-*.html` | The 11 case studies |
| `writing-*.html` | The 12 articles |
| `site.css`, `motion.js` | Shared styles and animation code |
| `dc-runtime.js` | Claude Design component runtime (bundles React, MIT licence) |
| `assets/img/` | Portrait, halftone mask, topography, world map, Ember background, social preview |
| `cv/` | The two CV PDFs behind "Get my CV" |
| `logos/` | Organisation logos on About |
| `404.html` | Not-found page |
| `design-source/` | The original Claude Design files (`*.dc.html`, `canvas.json`), kept as the source of truth |
| `tools/build.py` | Regenerates the site from `design-source/` |

## Run it locally

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

Use a local server rather than opening the files with `file://`.

## Deploy and connect your domain

Any static host works. Each option below is free for a site like this.

### Cloudflare Pages (recommended if your domain is on Cloudflare)

1. In the Cloudflare dashboard, open **Workers & Pages → Create → Pages → Connect to Git**, then pick `Saadtamari/Portfolio`.
2. Set the framework preset to **None**, leave the build command empty, and set the output directory to `/`.
3. After the first deploy, open **Custom domains → Set up a domain**, enter `yourdomain.com` (and `www.yourdomain.com`), and accept the DNS records it offers.

Clean URLs work automatically: `/about` serves `about.html`.

### Vercel

1. Go to **Add New → Project** and import `Saadtamari/Portfolio`.
2. Set the framework to **Other**, with no build command and the output directory `.`.
3. Under **Settings → Domains**, add your domain, then add the records Vercel shows at your registrar:
   - an `A` record for `@` pointing to `76.76.21.21`;
   - a `CNAME` for `www` pointing to `cname.vercel-dns.com`.

`vercel.json` already turns on clean URLs.

### Netlify

1. Go to **Add new site → Import from Git** and pick the repo.
2. Leave the build command empty and set the publish directory to `/`.
3. Under **Domain management → Add a domain**, follow the DNS instructions it gives you.

### GitHub Pages

1. Go to **Settings → Pages**.
2. Set the source to **Deploy from a branch**, with branch `main` and folder `/ (root)`.
3. Under **Custom domain**, enter your domain.
4. At your registrar:
   - add four `A` records for `@` pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and `185.199.111.153`;
   - add a `CNAME` for `www` pointing to `saadtamari.github.io`.
5. Tick **Enforce HTTPS** once the certificate is issued.

## After the domain is live

Rebuild once with your domain. This adds canonical links, absolute social preview URLs and `sitemap.xml`:

```bash
SITE_URL=https://yourdomain.com python3 tools/build.py
git add -A && git commit -m "Set site URL" && git push
```

Then submit `https://yourdomain.com/sitemap.xml` in Google Search Console.

## Updating the site

1. Edit the pages in Claude Design, then export or copy the changed files into `design-source/`.
2. Run `python3 tools/build.py`.
3. Commit and push. The host redeploys on its own.

The build script:

- gives pages clean file names;
- rewrites internal links;
- swaps the Claude Design asset URLs (`/_blob/…`) for the local files in `assets/img/` and `cv/`;
- adds the viewport, description, social preview and favicon tags.

If you upload a new image in Claude Design, add its blob ID and local path to `BLOBS` in `tools/build.py`.
