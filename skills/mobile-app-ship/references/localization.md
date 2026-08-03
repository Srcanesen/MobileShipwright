# Flutter Localization

Load during Flutter foundation and again during stability/localization review.

## Foundation

- Use Flutter's built-in `flutter_localizations` and `gen-l10n`; do not pin remembered package versions.
- Create `l10n.yaml` and ARB files under `lib/l10n/`, with `app_en.arb` as the template. Configure `generate: true`, generated localization delegates, and supported locales in the app. Use the generated import path reported by the current Flutter toolchain; do not assume the deprecated synthetic package.
- Let device locale be the default. Provide a Settings override persisted with `shared_preferences` only when the product needs manual language choice.
- Let `flutter_localizations` determine the compatible `intl` constraint; do not force a newer remembered version.
- Ask which locales ship before creating the ARB set. Keep the app and store-listing locale plan aligned; use [store-submission.md](store-submission.md) for ASC mappings and limits.

## Every string change

- Add or change the key in the template and **every** shipped locale in the same change.
- Preserve placeholders, ICU syntax, and meaning. Avoid unnecessary complex ICU plurals when a simpler durable string works.
- Validate each ARB as JSON and assert that every locale's non-`@` key set equals the template before running `gen-l10n`.
- Run the current localization generator and `flutter analyze`. Do not accept fallback English as proof that localization works.

## Stability review

- Render every locale. Check `tr` and `de` for overflow; prefer `Wrap`, `Flexible`, or `FittedBox` over a bare `Row` where text grows.
- If Turkish UI uses uppercase, handle `i`/`ı` locale-aware; do not rely on a plain `.toUpperCase()`.
- If an RTL locale ships, test it in that locale and verify direction, icons, and tap order. Drop an RTL locale if it cannot be verified.
