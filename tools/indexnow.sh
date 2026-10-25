#!/usr/bin/env bash
# Tell Bing, Yandex, Seznam, Naver and other IndexNow engines that pages changed.
# Run after a deploy: bash tools/indexnow.sh   (sends every URL in public/sitemap.xml)
set -euo pipefail
KEY="e0c925c720d1e1b8e8e2a04b6aa192fd"
URLS=$(grep -o '<loc>[^<]*</loc>' "$(dirname "$0")/../public/sitemap.xml" | sed 's#</\?loc>##g' | grep -v '/assets/' | sed 's/.*/"&"/' | paste -sd, -)
curl -sS -X POST https://api.indexnow.org/indexnow -H 'Content-Type: application/json; charset=utf-8' \
  -d "{\"host\":\"saadaltamari.com\",\"key\":\"$KEY\",\"keyLocation\":\"https://saadaltamari.com/$KEY.txt\",\"urlList\":[$URLS]}" \
  -w '\nIndexNow HTTP %{http_code}\n'
