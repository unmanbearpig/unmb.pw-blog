# unmb.pw local review QA

Date: 2026-07-28  
Branch: `redesign/employer-site-review-2026-07-28`  
Worktree: `/home/unmbp/projects/unmb.pw/worktrees/employer-site-review`

## Why?

This review is critical before any production decision because the redesign changes the site's audience from a mostly personal blog presentation to an employer-facing portfolio while preserving the writing archive and the unmanbearpig identity. The checks below establish that the proposed local build is usable, internally coherent and safely isolated. They do not authorize a deployment.

## Safety result

- No production deployment was run.
- No DNS, domain-registration, analytics or external-profile change was made.
- Review pages contain `noindex,nofollow,noarchive`.
- `robots.txt` disallows all crawling in review mode.
- The build remains local and links to the service prototype through a localhost URL.

## Build result

Command:

```sh
chruby-run bundle exec jekyll build \
  --destination /tmp/unmb-site-build \
  --disable-disk-cache \
  --trace
```

Result: PASS. Jekyll completed without build or Sass errors.

## Concept review

| Direction | Route | Desktop | Mobile | Finding |
| --- | --- | --- | --- | --- |
| Editorial Evidence, recommended | `/` | `screenshots/editorial-desktop.png` | `screenshots/editorial-mobile.png` | Best balance of technical proof, product judgment and a recognizable personal voice. |
| Technical Monochrome | `/review/concepts/technical/` | `screenshots/technical-desktop.png` | `screenshots/technical-mobile.png` | Strongest technical signal, but makes visual-identity and product work feel secondary. |
| Minimal Document | `/review/concepts/document/` | `screenshots/document-desktop.png` | `screenshots/document-mobile.png` | Fastest to scan and closest to a CV, but least distinctive. |

Additional captures cover the comparison page, recommended About draft and full Work page.

## Responsive and interaction checks

- Viewports tested: 320, 390, 768, 1024 and 1440 CSS pixels.
- Horizontal overflow: none at every tested width.
- Native mobile disclosure menu: PASS.
- Mobile navigation appears in the accessibility tree with a useful name: PASS.
- Keyboard navigation from the menu to the first link: PASS.
- Visible focus outline: 3px solid cobalt with 4px offset.
- Skip link and semantic main, banner, navigation and content-info landmarks: present.

## Automated audits

Lighthouse navigation audits on the recommended homepage:

| Device | Accessibility | Best Practices | Agentic Browsing | SEO |
| --- | ---: | ---: | ---: | ---: |
| Desktop | 100 | 100 | 100 | 69 |
| Mobile | 100 | 100 | 100 | 69 |

The sole final failure is the intentional crawler block in local review mode. A desktop accessible-name warning found during the first pass was fixed by letting the visible site identity provide the link name.

Local performance trace, 390 x 844 viewport, unthrottled localhost:

- LCP: 112 ms
- CLS: 0.00
- TTFB: 2 ms

These numbers verify that the static build has no obvious rendering regression. They are not production-network estimates.

## Routes, links and metadata

- Core routes, all three concepts, all About variants, Work, Writing, legacy About redirect, robots, sitemap and CV: HTTP 200 from the local server.
- Static crawl: 40 generated HTML files checked, zero missing internal `href` or `src` targets.
- Console after homepage navigation: zero messages.
- Homepage network log: ten same-origin local requests and no unexpected external requests.
- `sitemap.xml`: valid XML.
- Canonical, Open Graph metadata and Person JSON-LD: present.
- Blog posts remain below `/blog/misc/` and `/blog/project/`.
- Travel and Ticks and Trips collections now remain below `/blog/travel/` and `/blog/ticks_and_trips/`; duplicate root collection paths are absent.
- `/blog/about/` remains as a local redirect to `/about/`.

## CV check

- Stable route: `/assets/cv/Ivan_Fedyunin_CV.pdf`
- One A4 page, 53,993 bytes.
- Tagged PDF with a searchable text layer.
- No embedded JavaScript.
- Headline and current Vestuario Antiguo product, identity, logo and Rails ownership are represented in the source and PDF.

## Known review constraints

- Workshaped is a provisional service name based on a preliminary exact-name web, DNS and RDAP screen. It is not a legal clearance or domain purchase.
- No approved portrait was available, so the employer site relies on real project imagery.
- The Vestuario Antiguo case-study wording remains subject to client approval before public deployment.
- The local service link will work only while its separate review server is running.
- Production caching, compression and real-user performance still need verification if a deployment is later approved.

## Recommendation

Keep Editorial Evidence as the lead candidate. Use Minimal Document as the structural fallback if a more conservative hiring presentation is preferred, and retain Technical Monochrome as a useful art-direction reference rather than the default employer homepage.
