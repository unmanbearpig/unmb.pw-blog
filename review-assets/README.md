# Local review guide

This directory contains the review evidence for the employer-facing `unmb.pw` redesign. The implementation lives on branch `redesign/employer-site-review-2026-07-28` in the isolated worktree at `/home/unmbp/projects/unmb.pw/worktrees/employer-site-review`.

No production deployment, DNS change, analytics change or domain action is part of this branch. Do not run `deploy.sh` while reviewing it.

## Why?

The redesign changes how Ivan's experience, flagship work and use of coding agents are presented to employers. A local review gate is critical because the current public site remains the stable production version until Ivan chooses a direction and approves the copy.

## Build and serve locally

From the review worktree:

```sh
chruby-run bundle exec jekyll build \
  --destination /tmp/unmb-site-build \
  --disable-disk-cache \
  --trace
python3 -m http.server 4000 --directory /tmp/unmb-site-build
```

Open `http://127.0.0.1:4000/`.

## Recommended review order

1. `/review/concepts/` for the comparison and tradeoffs.
2. `/` for the recommended Editorial Evidence direction.
3. `/review/concepts/technical/` for Technical Monochrome.
4. `/review/concepts/document/` for Minimal Document.
5. `/work/`, `/about/` and the linked one-page CV.
6. `/about/cv-companion/` and `/about/personal-essay/` for the alternate About drafts.

The companion service prototype is on branch `site/service-brand-review-2026-07-28` in `/home/unmbp/projects/worktrees/service-site-review`. Its local review server is expected at `http://127.0.0.1:4322/` when running.

See `qa/2026-07-28_unmb-site-qa.md` for the verification record and `screenshots/` for matched desktop and mobile captures.
