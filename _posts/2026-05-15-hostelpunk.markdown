---
layout: post
title: "HostelPunk — ranking hostels by atmosphere instead of by 8.9"
date: 2026-05-15 12:00:00 +0000
categories: project
excerpt: "Ranking hostels by atmosphere hit-rate, confidence, bed bug evidence, and suspicious-review signals instead of generic 8.9 scores."
---

# HostelPunk — ranking hostels by atmosphere instead of by 8.9

I made a hostel search site: <https://hostelpunk.com/>.

The short version is that I kept ending up in clean, central, 9.1-star hostels where nobody talked to each other. That is fine if you came to sleep. It is not fine if you came to meet people. A generic 8.9 cannot tell those two places apart, because everything good on a hostel platform compresses into a tight band between roughly 8.5 and 9.6, and the thing I actually want to know about — whether the common room is alive — is buried in subscores and review text.

So the main HostelPunk score is not a rating in the normal sense. It is one specific question:

```text
PerfAtmPct = perfect-atmosphere reviews / atmosphere reviews
```

If a hostel has `PerfAtmPct 93`, that means 93% of reviewers gave the atmosphere the top-of-scale rating in the source review data. It is not cleanliness, not luxury, not a weighted soup of staff and breakfast and WiFi. It is a deliberately narrow social-vibe statistic, and it is cruel to places that are pleasant but not socially exceptional. That is the point.

A top-box rate behaves differently from an average. An average is forgiving; everyone giving 8/10 looks healthy. A top-box rate asks "did this place actually work for people, or was it just fine?" For solo-traveler hostels, "fine" is the failure mode I'm trying to detect.

## Sample size, or: 100 from 7 reviews is not 100

The obvious bug: a 100% score from 7 reviewers should not casually outrank a 93% from 900. HostelPunk handles this in two places. The displayed score is the raw `PerfAtmPct`, because that's the number a human can interpret. A confidence tier sits next to it. Ranking uses a Wilson-style lower-bound adjustment so small-n hostels can appear without pretending to be deep signal.

Current confidence tiers:

- `certain`: 300+ reviews
- `confident`: 100+
- `mid`: 50+
- `low`: 20+
- `blind`: below 20

Absence-of-warning claims (e.g. "no bed bug reports") require at least 100 analyzed reviews. Below that, "we don't know" is the honest read, not "clean."

## Bed bugs are a different axis

The most useful thing the site does is refuse to compress everything into one score.

A hostel can be social and have recent bed bug reports. Averaging those two facts into a 7.9 is worse than useless — they drive different decisions. Some people will never book a place with any positive bed bug evidence. Others will tolerate one historical report against hundreds of clean recent reviews. The job is to show both, with dates and severity, and let the user pick.

As of today the bed bug detector has positive evidence for 1,075 properties: 4,839 total reports, 658 in the last twelve months, 81 in the last thirty days. The product copy says "reports" and "evidence," not infestation. Bites can be misidentified, reviews lag conditions, hostels remediate. UI tiers care about recency and repetition — one old report is not the same object as multiple reports this month.

Two concrete Amsterdam examples:

- **Onefam Amstel** — `PerfAtmPct 93/100`, 916 reviews, `certain` confidence, #1 in Amsterdam, #1 in the Netherlands. Dorms from $79, privates from $253. Top languages English 59%, Spanish 8%, Turkish 7%. Clean example, no warnings.
- **Princess Hostel Leidse Square** — `PerfAtmPct 2/100` from 499 reviews, 59 bed bug reports, 18 in the last twelve months, latest 2026-05-02. High tier. The extreme version of the page doing its job.

## Suspicious reviews as a distribution problem

The other detector is weirder, and it's where the project drifts from travel site into applied statistics hobby.

Explicit paid-review complaints are rare. Sometimes a reviewer writes that staff offered a free drink for a positive review; that's easy to catch but doesn't move the ranking much. The interesting signal is aggregate: too many short top-rated reviews compared with what peer properties produce. The detector estimates excess short top-atmosphere reviews against a leave-one-out baseline. That estimate is not a per-review verdict. It's a property-level shape anomaly large enough that I don't want the raw atmosphere score to be the only score.

When the warning threshold is met, HostelPunk also computes an *adjusted* atmosphere score with the likely distorted reviews excluded, and shows both. Today, 53 current properties cross that line with an adjusted score below the raw score. Average drop: 3.9 points. Largest drop: 16.4 points.

Examples:

- Mama Hostel & Rooftop Pool, Hanoi — raw 70.4, adjusted 54.0, estimated 90 incentivized.
- ClinkNOORD, Amsterdam — 3,015 reviews, `PerfAtmPct 53/100`, also 7 bed bug reports and a suspicious-5-star warning with about 104 possibly bought. The mixed-signal case: well-known place, large sample, weak vibe, two separate warning kinds — the page can show all of that at once instead of melting it into a single number that picks a side.

The wording in this section of the UI is intentionally less fun than the rest of the brand. An aggregate anomaly is not a claim that review #12345 is fake, and the copy has to keep that clear.

## The unglamorous half: source data is weird

The funniest bugs are not in the ranking code. They're in source data.

Two real Hostelworld quirks the scraper has to handle:

- Review notes from the legacy review endpoint sometimes come back exactly 512 characters long, cut mid-word. The public Hostelworld site shows the same cutoff, so the truncation is at the source, not in our parser.
- The city availability endpoint can return room prices like `999999.99`. If you request a different currency, the sentinel is numerically *converted* and comes back as something like `1170756.99 USD` — still bogus, now wearing a currency label.

So a lot of the engineering is not "fetch JSON, insert rows." It's deciding which fields are trustworthy enough to display, what counts as sentinel garbage, and which narrower endpoint should override a broader one. None of that ends up in product copy, but it's why prices on the page don't lie.

## Stack

The boring-in-a-good-way part:

- Go for the user-facing app (`hostelpunk`)
- PostgreSQL + PostGIS
- Server-rendered HTML, a little HTMX
- No npm
- Python scrapers with `uv`
- Review analysis runs as a separate worker pool against models served locally and via OpenRouter

HostelPunk is the public surface of a bigger pile called SocialSpots, which has Hostelworld, Booking.com, Google Maps, iOverlander, OSM, and Workaway data behind it. The order-of-magnitude shape: roughly a million-ish Hostelworld reviews, tens of millions of Booking reviews, and tens of millions of review-analysis rows feeding the detectors. A traveler does not need to see any of that. They need to see that a hostel's 93 came from 916 reviews, that there are no current warnings, and that the language mix probably fits them.

## Still rough

The UI isn't done. Some detectors are conservative, some are still mining signals. Rare-class precision is hard. Source platforms change APIs. A property can improve or decay faster than the crawler notices. The right posture is not "the model knows the truth" — it's "this is a much better prior than reading 300 random reviews at 1am the night before a flight."

It already works well enough for me. If I'm choosing between two hostels in Amsterdam or Hanoi or Hoi An, I'd rather start from atmosphere hit-rate, confidence, warning evidence, suspicious-review adjustment, language mix, and source links than from a generic 8.9.

<https://hostelpunk.com/>
