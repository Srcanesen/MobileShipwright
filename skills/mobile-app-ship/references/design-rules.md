# Design Quality Rules

Apply during the design phase (understanding the app, writing the prompt, building the paywall) and before store listing setup.

## Anti-slop: forbidden defaults

Do not start from these. They are the universal tells of AI-generated design:

- ❌ Claude orange as the primary colour.
- ❌ "AI slop" purple + purple-blue neon gradients.
- ❌ Glassmorphism (frosted glass, backdrop blur everywhere).
- ❌ The beige default: warm cream paper + muted brown + a lone serif. Every app that ships this looks the same and looks AI-made.
- ❌ Generic "artificial intelligence" aesthetics (circuit-board patterns, robot icons, neural network diagrams).

## Palette tied to app meaning

The colour palette must come from the app's subject matter, not from a safe fallback:

- Finance → trustworthy deep tones (navy, forest, burgundy).
- Health/wellness → calm naturals (sage, clay, sky).
- Creativity → warm contrast (coral, ochre, ink).
- Utility → clear, high-information (steel, white, accent).

Suggest concrete colours/hex. Make it original. If the user likes warm and papery — fine, but it is a choice for this app, never an autopilot.

## User discovery and approval

Before drafting a design, state the app's purpose, audience, age/tone, and core action in 2–3 sentences; ask if any is unclear. Ask the user for mood, light/dark preference, admired references, and colours/styles to avoid. Produce an app-specific design brief with palette/hex, typography, shape/depth language, and required screens. Obtain approval before implementation.

Content needs pictures, not paragraphs. Repeating items (exercises, recipes, lessons, categories) each need a visual:
- Prefer one consistent professional, permissively licensed set (for example Lucide, Phosphor, Feather, Font Awesome Free, Tabler, unDraw, Lottie/Rive) before custom drawing/generation.
- Verify the exact asset license before shipping. Use only licensed assets; add attribution when the license requires it (for example CC-BY), not for licenses that do not.
- Never scrape random web/GitHub images. Use custom/generated art only when a generic set cannot represent the subject.
- Empty states get an illustration, not bare text.
- Every screen needs a visual anchor. A wall of text with buttons looks like a prototype.

## Visual/animated onboarding

**Required** — animated and visual, not text slides. Multi-page onboarding through key features (3-5 pages, progress indicator, "skip/continue"). The paywall opens after the last page. Shown once (`shared_preferences`).

Each page carries motion or an illustration: a Lottie/Rive animation, an animated hero, a subject-matter illustration. Animate element entry and meaningful page changes. A static text-slide onboarding is the #1 tell of a template app; users skip it and never see the value.

## Haptics

Use platform-appropriate haptics for meaningful button/tab taps, onboarding page changes, selections, and success/error moments. Centralize them in shared controls. Do not vibrate for passive scrolling or every decorative animation.

## Paywall design standards

The paywall earns the entire revenue. A stock list of radio buttons with a "Premium" title looks like raw HTML and converts like it.

- **Hero at the top**: illustration, gradient, or strong product image in the app's palette. Bare heading is not enough.
- **Text-light, visual-first**: sell with a hero visual, a benefit headline, and 3-4 icon rows — not paragraphs. Whitespace and one strong image beat five lines.
- **Sell the outcome, not the feature**: headline is a benefit ("Boyunun potansiyeline ulaş"), not the word "Premium".
- **Plan card hierarchy**: the recommended plan is visually dominant with a badge ("En popüler"). Annual shows savings + per-week price.
- **One prominent CTA**: full-width, accent colour. Label reflects the trial ("Ücretsiz Dene", not "Satın Al") when one exists.
- **Trust elements (required, not optional)**: "Restore" action, small tappable **Terms** and **Privacy** links, auto-renew disclosure sentence. A paywall without working legal links is both a conversion failure and a guaranteed rejection (3.1.2).
- **Data-driven off the RevenueCat offering**: plan changes need zero code.
- **Smell test**: if the paywall looks like it could belong to any app, or like a settings page with prices, it is not done.

## Store naming: Brand: Tagline

The **name** field in the App Store is your title. Write it as **`<Brand>: <what it does>`**.

**Three rules:**
1. **The brand is a constant** — identical in all locales. Never translate, never transliterate, never decline it.
2. **The tagline is what people SEARCH** — not a polite description. Find the two or three words a real user types to find this app. Translate the meaning, never transliterate. If unsure, check competitor titles and App Store search autocomplete.
3. **Keep it short** — Apple truncates around 30 characters on the store shelf. `Brand: two or three words` fits. The **subtitle** field is a separate 30 characters — put the second keyword phrase there.

```
Locale  | name
en-US   | Auria: Migraine Tracker
tr      | Auria: Migren Takibi
de-DE   | Auria: Migräne Tagebuch
```

Feed this into `appinfo.json` per locale. Assemble `brand + ": " + translated_tagline` yourself rather than trusting a translator to echo the brand. The brand token is fixed; translate only what follows the colon.

## Store screenshots rules

1. The UI inside the screenshot must be in the **same language** as the store locale.
2. Show the app in use (Guideline 2.3.3). Not title art, login page, or splash screen.
3. Status bar must not lie: 9:41, full battery, full signal, no invented carrier name.

Capture raw screens from the shipping build. Turn them into premium listing assets with any user-approved tool; keep generated decoration outside the real UI. Revalidate current device-family dimensions in store documentation before export. For durable examples and upload checks, load [ios-app-store.md](ios-app-store.md) § Phase 11.5 and [android-play.md](android-play.md) § Store listing.

## Final anti-slop review

Screenshot the implemented screens before showing them. Check type hierarchy, visual identity, content density, loading/empty/error states, and accessibility. Cover the logo: if the result could belong to any app, revise it. Do not make the user be the first person to identify generic output.
