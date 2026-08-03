# App Store Optimization (ASO) — Planning and Review Reference

Load when planning or reviewing store metadata, keywords, copy, visual assets, localization, experiments, or metrics for either store. This reference only **prepares and validates** artifacts and **records evidence**; it never uploads or mutates a vendor. Upload, listing, experiment, and custom-page mutations stay in [store-submission.md](store-submission.md), [ios-app-store.md](ios-app-store.md), and [android-play.md](android-play.md), with their existing exact single-use gates and read-backs.

Official-source claims below were verified **2026-08-02** (`verifiedAt`). Store documentation is volatile: revalidate every cited claim against the live source before each submission cycle. Do not present ranking factors, character limits, or asset rules as eternal guarantees.

Complements: [design-rules.md](design-rules.md) § store naming and screenshots, [localization.md](localization.md), [pre-submission-review.md](pre-submission-review.md), and [state-evidence.md](state-evidence.md) for evidence recording.

## Labels used in this reference

- **Platform fact** — stated by an official source cited inline; true as of `verifiedAt`.
- **Heuristic** — a pattern derived from store behavior or review practice; not a guaranteed ranking factor. Treat as judgment, not law.
- **Revalidate** — the official source or the value can change; confirm live before acting on it.

## Scope and boundaries

- Do not add new phases, gates, onboarding decisions, or schema fields. Existing listing/locales/screenshots decisions are sufficient.
- Prepare copy, keywords, assets, and checks; validate against official sources; record sanitized evidence through the existing [state-evidence.md](state-evidence.md) model.
- Every vendor mutation (metadata import, screenshot upload, experiment start, custom page publish) remains a separate external mutation with its own exact single-use approval, applied once and read back, per [human-gates.md](human-gates.md).
- When official guidance and the playbook baseline disagree, the live official source wins; record the discrepancy in evidence.

## Competitor intelligence workflow (read-only, target-specific)

Run this workflow **before** writing ASO copy or choosing experiments. It discovers comparable apps, compares only public evidence, finds honest positioning gaps, and produces differentiated recommendations for the target app. It does not promise rank, installs, conversion, or revenue.

Competitor research is target-specific. Do not put a competitor list, raw store response, reviewer personal data, or target metadata into this toolkit. Keep approved decisions and sanitized evidence in the target's existing `DECISIONS.md`/STATUS evidence flow; do not add onboarding or schema fields.

### 1. Define the target scope

Read the target's approved `SPEC.md` and `DECISIONS.md` before searching. Record:

- core job-to-be-done and the problem the app solves;
- primary audience, supported platforms, storefronts, languages, and territories;
- supported features, pricing model, trust/safety claims, and known differentiators;
- excluded features and claims the app cannot truthfully make.

If the scope is missing or contradictory, stop and ask for clarification. Do not choose competitors from the app name alone.

### 2. Build a defensible competitor set

Use three tiers. The tier is an analysis label, not a store ranking claim:

- **Direct:** same job, audience, platform, and market intent.
- **Adjacent:** a different product that solves the same user problem or substitutes for the same decision.
- **Benchmark:** a visible category leader whose presentation is useful to study, even when it is not a direct substitute.

A practical starting sample is 3–5 direct and 2–3 adjacent/benchmark apps per platform or primary storefront. This is a **heuristic**, not a completeness guarantee. Keep a selection reason for every app and remove an app when its scope, platform, or market no longer matches.

For each competitor, record its public store URL, platform, storefront/country, language, device context, captured-at timestamp, tier, and selection reason. Use public App Store pages or Apple's public search/API surfaces where available. Use a manual public Google Play listing capture; do not invent a private API, use credentials, or bulk-scrape Play pages. Third-party ASO estimates for installs, revenue, or keywords are heuristics and must never be recorded as platform facts.

### 3. Capture public evidence only

Capture the smallest evidence set that supports a comparison:

| Area | Observable public evidence | Do not claim |
|---|---|---|
| Listing copy | Name/title, subtitle or short description, visible full description, promotional text when shown, category, visible pricing/ads/IAP badges | Apple's hidden keyword field or Google's hidden keyword-level data |
| Visuals | Icon, first three visible screenshots, screenshot order, overlays, preview/feature graphic, visible UI language | Conversion caused by one asset without an experiment |
| Market signals | Public rating, review count, visible review themes, update/version date, Apple territory rating, Google install range when displayed | Exact installs, revenue, impressions, ad spend, or ranking formula |
| Localization | Visible locale/storefront, translated copy/assets, fallback or missing-language observations | Global coverage from one storefront snapshot |
| Trust and claims | Privacy/data-safety summaries, subscriptions/IAP/ads labels, developer identity, support links, claims visible in copy/assets | Compliance or product capability that the public page does not prove |

Public evidence is a snapshot. Ratings, reviews, search results, prices, availability, experiments, and page content vary by storefront, language, device, account, and date. Save sanitized themes and source URLs, not reviewer names, contact details, cookies, or raw credential-bearing responses.

### 4. Produce the comparison matrix

Use one row per competitor and separate **observation**, **interpretation**, and **recommendation**. The minimum matrix is:

```text
competitor | tier | platform/storefront/locale | public URL | capturedAt
job/promise | title/subtitle/short-description pattern | visible keyword themes
first-three-screenshot messages | asset/localization notes
rating/review-count/update snapshot | repeated review themes
observed strengths | observed gaps | confidence | source limitations
```

Do not call a visible word a competitor's hidden keyword. Use `observed theme` or `visible phrase` instead. Do not infer that a high rating proves better retention or that an install range proves market share.

### 5. Turn comparison into differentiated ASO

For every recommendation, require this chain:

```text
public observation → user intent or unmet need → target-app capability → proposed metadata/asset change → validation evidence
```

Prioritize gaps that the target app can actually support. Good outputs include a clearer job-to-be-done, a missing locale, an under-explained feature, a confusing first screenshot, or a trust concern repeated in public reviews. Do not copy competitor wording, screenshot composition, icons, names, trademarks, testimonials, or claims. Competitor names and trademarks are **internal analysis data only**; never put them in the target's title, subtitle, keywords, description, screenshots, or promotional text. Keep Apple § 2.3 and Google metadata/IP rules in force.

Return recommendations in three buckets:

- **Launch:** truthful listing changes needed before first submission.
- **Next iteration:** changes that need product, design, localization, or support work.
- **Experiment:** one hypothesis, one primary asset/copy change, one metric, and a read-back window; never treat the result as guaranteed rank.

### 6. Evidence contract for agents

Record one sanitized read-only evidence item for each completed competitor review. It should include:

- target scope reference and the observation window;
- competitor tier, platform, storefront, locale, URL, and capture date;
- visible observations and source type (`app-store-page`, `itunes-search-api`, `play-page`, or `play-help`);
- comparison gaps, recommended changes, confidence, and explicit limitations;
- `verifiedAt` for platform facts and a statement that hidden keywords, exact installs, revenue, ranking, experiments, and custom-page analytics were not observed.

Use the existing evidence model in [state-evidence.md](state-evidence.md). ASO research itself is read-only: it does not create an action, consume a gate, or change vendor state. A metadata import, screenshot upload, experiment start, or custom-page publication is a later external mutation and still needs its own exact single-use approval and read-back.

### Public-source boundaries (verifiedAt 2026-08-03)

- **Apple:** public search/API surfaces expose listing fields such as name, subtitle, description, screenshots/previews, category, seller, rating, and version information. The public response does not expose the App Store keyword field, installs, revenue, impressions, conversion, ad spend, or competitor PPO/custom-page analytics. Treat this as a public-observation boundary, not proof that the values do not exist internally. Source: [iTunes Search API documentation](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html) and [App Store search](https://developer.apple.com/app-store/search/).
- **Google Play:** public listings may show title, descriptions, screenshots/video, feature graphic, rating/reviews, update information, developer details, policy badges, and an install range. Exact installs, revenue, search impressions, keyword data, experiment results, and custom-listing analytics are not public competitor evidence. Use manual page capture; do not bulk-scrape or use unofficial competitor APIs.
- **Both stores:** search results and charts are regional, language-specific, device-specific, and partly personalized. A captured position is a timestamped observation, not a reproducible rank or a ranking formula.
- **Ratings and reviews:** use them as directional themes. Apple ratings are territory-specific and can be reset on a new version; Google states that public ratings are weighted toward recent ratings. A single snapshot does not prove a quality trend.
- **Custom pages and experiments:** Apple custom product pages and PPO, and Google custom store listings and experiments, expose analytics only to the owning developer. Do not infer a competitor's page variants, targeting, experiment result, or keyword list from a public default listing.

### Competitor-review checklist

Emit one PASS/FAIL line per item:

- Target scope, storefront, locale, device, and observation date are recorded.
- Every selected competitor has a tier and a defensible selection reason.
- Every observation has a public source URL; hidden fields are marked `not_observable`.
- At least one direct and one adjacent comparison is present when the market supports them.
- Visible phrases are separated from keyword assumptions, estimates, and heuristics.
- Review/rating signals include territory/locale/date limitations.
- Each recommendation maps to a real target capability and a stated user intent.
- No competitor name, trademark, copied wording, copied asset, fake testimonial, ranking promise, or unsupported claim enters the target listing.
- Launch, next-iteration, and experiment recommendations are separated.
- Sanitized evidence records source URLs, `verifiedAt`, confidence, limitations, and the next revalidation point.

## Official sources (verifiedAt 2026-08-02; competitor public-source boundaries verifiedAt 2026-08-03)

| Vendor | Topic | Source |
|---|---|---|
| Apple | Search, keyword field, promotional text, App Analytics | https://developer.apple.com/app-store/search/ |
| Apple | Review Guidelines § 2.3 (accurate metadata, screenshots) | https://developer.apple.com/app-store/review/guidelines/ |
| Apple | Field limits: name/subtitle/keywords/promo/description/What's New, URLs | https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information |
| Apple | Screenshot count and current device specifications | https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications |
| Apple | App preview count and specifications | https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications |
| Apple | Localization and fallback behavior | https://developer.apple.com/help/app-store-connect/manage-app-information/localize-app-information and https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations |
| Apple | Product Page Optimization (up to 3 treatments) | https://developer.apple.com/help/app-store-connect/create-product-page-optimization-tests/overview-of-product-page-optimization |
| Apple | Custom product pages (up to 70) | https://developer.apple.com/help/app-store-connect/create-custom-product-pages/configure-multiple-product-page-versions |
| Apple | Public competitor listing/search fields | https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html and https://developer.apple.com/app-store/search/ |
| Google | Field limits: title/short/full, localized listings | https://support.google.com/googleplay/android-developer/answer/9859152 |
| Google | Metadata policy (honest, relevant, no spammy keywords) | https://support.google.com/googleplay/android-developer/answer/9898842 |
| Google | Preview assets (screenshots, feature graphic, claims, alt text) | https://support.google.com/googleplay/android-developer/answer/9866151 |
| Google | Translation/localization and RTL testing | https://support.google.com/googleplay/android-developer/answer/9844778 |
| Google | Listing experiments (default + localized variants) | https://support.google.com/googleplay/android-developer/answer/9859351 |
| Google | Custom store listings (country/search keyword targeting) | https://support.google.com/googleplay/android-developer/answer/9867158 |
| Google | Store listing performance and CTR terminology | https://support.google.com/googleplay/android-developer/answer/9859173 |
| Google | Listing experiment best practices (test ≥ 1 week) | https://developer.android.com/distribute/best-practices/grow/store-listing-experiments.html |

## Apple App Store — metadata plan

Field limits below are **platform facts at `verifiedAt`**; revalidate against the platform-version-information help page before export. Import mechanics, locale mappings, and read-back live in [store-submission.md](store-submission.md) § Locale mappings.

| Field | Limit (verifiedAt 2026-08-02) | Notes |
|---|---|---|
| Name (title) | 30 characters | Keep the `Brand: translated tagline` shape; see [design-rules.md](design-rules.md) § Store naming. |
| Subtitle | 30 characters | Second keyword phrase; separate from name. |
| Promotional text | 170 characters | **Platform fact: does not affect ranking.** It is promotional, not searchable. |
| Keywords | 100 (see byte/character conflict below) | Comma-separated, no spaces after commas. |
| Description | 4000 characters | Lead with the strongest human-written benefit; see copy guardrails. |
| What's New | 4000 characters | Omit on the first release; see [store-submission.md](store-submission.md). |
| Support/Marketing URL | URL per locale | Set and verify HTTP 200 per locale; see [store-submission.md](store-submission.md). |

### Keyword field: the byte/character conflict

**Platform fact (conflict):** Apple's official documentation conflicts between **100 characters** and **100 bytes** for the keyword field. **Revalidate** the live wording. Until resolved, treat the budget as **100 characters or fewer of ASCII-compatible text** (worst case: 100 bytes), count per locale, and record the observed live limit in evidence.

### Keyword and copy guardrails (Apple)

- **Platform fact:** App Store search uses text relevance for the **title, subtitle, keywords, and category**, plus user behavior (installs, engagement). It is not a fixed keyword-weight algorithm; do not present any specific weighting as guaranteed.
- **Platform fact:** Promotional text does not affect ranking; it exists to inform returning users.
- **Platform fact:** Do not include keyword stuffing, third-party trademarks, or competitor app names in metadata (search page guidance; § 2.3 accurate metadata).
- **Heuristic:** Put the primary keyword phrase in the title/subtitle (the brand stays constant; see [design-rules.md](design-rules.md) § Store naming), secondary phrases in keywords, and natural-language keyword use in the description.
- **Heuristic:** Lead the description with the strongest benefit in the first two lines — reviewers and users see it first; keep claims truthful (§ 2.3) and consistent with [ios-app-store.md](ios-app-store.md) § Description and claims.

## Google Play — metadata plan

Field limits are **platform facts at `verifiedAt`** (https://support.google.com/googleplay/android-developer/answer/9859152); **revalidate** before each release. Play store listing mechanics live in [android-play.md](android-play.md) § Store listing.

| Field | Limit (verifiedAt 2026-08-02) | Notes |
|---|---|---|
| App name (title) | 30 characters | Same `Brand: tagline` rule; brand constant across locales. |
| Short description | 80 characters | First impression; put the core promise here. |
| Full description | 4000 characters | Natural keyword use; honest feature claims. |
| Localized listings | One per supported locale | See localization section. |

### Keyword and copy guardrails (Google)

- **Platform fact:** Play metadata policy (https://support.google.com/googleplay/android-developer/answer/9898842) requires metadata that is **honest and relevant**; do not use **repetitive or spammy keywords**, irrelevant **emojis or ALL-CAPS**, or **ranking and price claims** ("#1", "best app", "free" when it is not).
- **Platform fact:** Violations are a policy issue, not a ranking tweak — they can block the listing or the release.
- **Heuristic:** Write the title for the primary keyword phrase and the short description for the second; use the full description for supporting phrases in natural sentences, never stacked keyword lists.

## Visual assets

Shared source rules: real shipping UI, locale-matched UI language, no price/currency text, truthful status bar; see [design-rules.md](design-rules.md) § Store screenshots rules, [ios-app-store.md](ios-app-store.md) § Phase 11.5, and [android-play.md](android-play.md) § Store listing for capture and upload detail.

### Apple (screenshot-specifications; § 2.3)

- **Platform fact:** Supply **1–10 screenshots** per required device size and locale. Current device specifications and slot names are set by Apple; **revalidate** them before export.
- **Platform fact (§ 2.3):** Screenshots must show the **app in use** — real current UI, not mockups, old UI, or unrelated imagery.
- **Platform fact (§ 2.3):** No imagery that is irrelevant to the app or that shows **other platforms**; claims must be truthful.
- **Platform fact:** Up to three app previews can be provided per localization and device size; preview format and duration limits are defined by Apple's current specification page and must be revalidated before export.
- **Heuristic:** First screenshot carries the benefit headline; order sets zero-padded for display order.

### Google (https://support.google.com/googleplay/android-developer/answer/9866151)

- **Platform fact:** Maximum **8 screenshots per device type**; screenshots must show the **actual app UI**. A feature graphic is a separate marketing asset and must meet the current Play specification.
- **Platform fact:** The current Play baseline lists a **1024×500 feature graphic**; revalidate the dimension before export.
- **Platform fact:** Play accepts one listing preview video through a YouTube URL; autoplay and length behavior vary by surface, so verify the current help page before production.
- **Platform fact:** A tagline may be overlaid, but keep it within roughly **20%** of the graphic; do not let it dominate or obscure the UI.
- **Platform fact:** No promotional claims in the graphic text: no **"#1", "Best", "Sale", or call-to-action** phrases.
- **Platform fact:** Provide **alt text** for screenshots so the listing is accessible and understood without images.
- **Revalidate:** Current feature graphic dimensions and accepted device types in Play Console before export; the playbook baseline (1024×500 feature graphic) is a planning baseline only, per [android-play.md](android-play.md).

## Localization

- **Apple:** Localization and fallback behavior are documented in the localize-app-information and app-store-localizations pages. **Platform fact:** a locale without content falls back to the default-language listing; mismatched UI/caption languages fail the "show the app in use" rule. Map locales deliberately via [store-submission.md](store-submission.md) § Locale mappings; keep ARB and store locale sets aligned per [localization.md](localization.md).
- **Google:** Localized listings per locale are supported (https://support.google.com/googleplay/android-developer/answer/9859152); translation quality and **RTL testing** are covered by https://support.google.com/googleplay/android-developer/answer/9844778. Follow [localization.md](localization.md) § Stability review for RTL and longest-string rendering before asset capture.
- **Heuristic:** Translate meaning, never the brand; the brand token is constant in every locale ([design-rules.md](design-rules.md) § Store naming).

## Experiments and analytics

Experiments change only which listing variant users see; they do **not** change the submitted binary or metadata for review. Starting an experiment or publishing a custom page is an external mutation with its own exact single-use gate and read-back.

### Apple — Product Page Optimization (PPO)

- **Platform fact:** PPO supports up to **3 treatments** at a time (icon, screenshot, or preview variations) against a default. The overview page documents conversion-lift and confidence reporting.
- **Platform fact:** Custom product pages allow up to **70 versions**, each with unique keywords, assets, and URLs; analytics on a custom page begin after **5 first-time downloads**.
- **Heuristic:** Run one hypothesis at a time; give each test enough impressions before reading results (see Google best practice below for duration guidance).

### Google — listing experiments and custom store listings

- **Platform fact:** Listing experiments run a **default against one or more localized variants**; the experiments page documents variants and metrics (https://support.google.com/googleplay/android-developer/answer/9859351).
- **Platform fact:** Custom store listings support **country and search-keyword targeting** and up to **50 listing pages** (https://support.google.com/googleplay/android-developer/answer/9867158).
- **Platform fact/best practice:** Google's grow guide recommends testing for **at least a week** and interpreting metrics against the stated goal before concluding (https://developer.android.com/distribute/best-practices/grow/store-listing-experiments.html). This duration is guidance, not a guarantee of significance.
- **Heuristic:** Prefer testing title/short-description or first-screenshot changes — the highest-visibility fields — and treat icon changes separately.

## Metrics

- **Apple:** App Analytics documents **impressions, conversion, and source** of store traffic (https://developer.apple.com/app-store/search/). **Heuristic:** use impressions-to-download conversion and source breakdown, not raw impressions, to judge a listing change.
- **Google:** The store listing performance page documents **CTR and related terminology** (https://support.google.com/googleplay/android-developer/answer/9859173). **Revalidate** this page before quoting its terms — Google warns the page changes.
- **Heuristic:** A listing change is "working" only when the primary metric moves in the expected direction over the full test window with enough traffic; never conclude from a single day.

## Pre-submission ASO checks

Run these alongside [pre-submission-review.md](pre-submission-review.md) before the final submit pass. Emit one PASS/FAIL line per item against the actual prepared artifacts; fix every FAIL. This is a review checklist, not a new gate.

- Title/name ≤ current limit per locale, `Brand: tagline` shape, brand constant (Apple 30 / Google 30).
- Subtitle (Apple) and short description (Google) ≤ limits and contain the intended keyword phrase.
- Keywords: ≤ budget, comma-separated, no stuffed repeats, no trademarks/competitor names (Apple); Play metadata free of repetitive keywords, emojis/CAPS, and ranking/price claims.
- Description/full description within limits; strongest benefit in the first lines; claims truthful and match actual features (both stores, § 2.3 / metadata policy).
- Promotional text within limit and treated as non-ranking (Apple).
- Screenshots: count within 1–10 (Apple) and ≤ 8 per device (Play); real current UI; UI language matches locale; no other-platform or irrelevant imagery; no price/currency text (OCR check per [pre-submission-review.md](pre-submission-review.md)); Play graphics within ~20% tagline guidance, no "#1/Best/Sale/CTA" text, alt text present.
- Localization: every shipped locale has complete metadata and matched UI; fallback correct where full localization is infeasible; RTL verified.
- URLs: support/privacy/marketing URLs per locale return HTTP 200.
- Competitor review: scope, tiers, storefront/locale/device, public URLs, observation date, visible-vs-hidden fields, gaps, and confidence are recorded; recommendations trace to real target capabilities.
- Differentiation: no competitor names/trademarks, copied wording/assets, fake testimonials, ranking promises, or unsupported claims enter the target listing.
- Evidence: record the observed limits, source URLs, `verifiedAt`, and any official-vs-baseline discrepancy via [state-evidence.md](state-evidence.md).

## Evidence and gate handling

- ASO planning and validation are read-only: record sanitized evidence (limits observed, source URLs, `verifiedAt`, PASS/FAIL lines) through the existing evidence model; never fabricate vendor state.
- Metadata imports, screenshot uploads, experiment starts, and custom-page publishes are external mutations: exact single-use approval, apply once, read back — per [human-gates.md](human-gates.md) and the owning reference ([store-submission.md](store-submission.md), [ios-app-store.md](ios-app-store.md), [android-play.md](android-play.md)).
- This reference adds **no** new phase, gate, onboarding decision, or schema field.

## Fact vs heuristic and revalidation summary

| Claim | Type | Source (verifiedAt 2026-08-02) | Revalidate before |
|---|---|---|---|
| Apple search uses text relevance (title/subtitle/keywords/category) + user behavior | Platform fact | developer.apple.com/app-store/search/ | Each submission cycle |
| Apple keyword field 100 characters vs 100 bytes (docs conflict) | Platform fact (conflict) | developer.apple.com/app-store/search/ and platform-version-information | Each submission cycle |
| Apple promotional text does not affect ranking | Platform fact | developer.apple.com/app-store/search/ | Each submission cycle |
| Apple name/subtitle 30, promo 170, description/What's New 4000 | Platform fact | platform-version-information | Before export |
| Apple 1–10 screenshots, current device specs | Platform fact | screenshot-specifications | Before export |
| Apple up to 3 app previews per localization/device size | Platform fact | app-preview-specifications | Before export |
| Apple § 2.3: real-UI screenshots, no irrelevant/other-platform imagery, truthful claims | Platform fact | app-store/review/guidelines/ | Each submission |
| Apple PPO ≤ 3 treatments; custom pages ≤ 70; analytics after 5 first-time downloads | Platform fact | PPO overview; custom product pages | Before starting tests |
| Google title 30 / short 80 / full 4000 | Platform fact | support.google.com .../9859152 | Before each release |
| Google metadata policy: no spammy keywords, emojis/CAPS, ranking/price claims | Platform fact | support.google.com .../9898842 | Each release |
| Google ≤ 8 screenshots/device, actual UI, ~20% tagline, no "#1/Best/Sale/CTA", alt text | Platform fact | support.google.com .../9866151 | Before export |
| Google feature graphic baseline 1024×500 and one YouTube preview URL | Platform fact | support.google.com .../9866151 | Before export |
| Google listing experiments (default + localized) | Platform fact | support.google.com .../9859351 | Before starting tests |
| Google custom store listings (country/keyword targeting, up to 50 pages) | Platform fact | support.google.com .../9867158 | Before creating one |
| Google listing performance/CTR terminology | Platform fact; page changes | support.google.com .../9859173 | Before quoting |
| Test experiments ≥ 1 week, interpret against goal | Platform fact (guidance) | developer.android.com grow/store-listing-experiments.html | Before concluding |
| Public competitor keywords, exact installs, revenue, impressions, experiments, and custom-page analytics are not observable | Operational boundary; revalidate | iTunes Search API; public App Store/Play listing surfaces | Before each research cycle |
| Public store position is regional, localized, personalized, and time-bound | Heuristic | App Store search; Play search guidance | Never treated as a ranking formula |
| Ratings/reviews are directional; Apple is territory/version-sensitive and Google weights recent ratings | Platform fact + interpretation rule | Apple ratings/search guidance; Google ratings guidance | Before market conclusions |
| Competitor names/trademarks are internal analysis data only | Policy guardrail | App Review Guidelines §2.3.7/4.1/5.2.1; Google Metadata/IP policy | Every listing review |
| Keyword placement, description lead, one-hypothesis-at-a-time, conversion-first metrics | Heuristic | — (judgment) | Never treated as guaranteed |
