<p align="center">
  <img src=".github/assets/logo.png" alt="Mobile App Ship Playbook" width="110">
</p>

<p align="center"><b><a href="README.md">English</a> | <a href="README.tr.md">Türkçe</a></b></p>

<h1 align="center">Mobile App Ship Playbook</h1>

<p align="center">
  Flutter/Firebase tabanlı mobil uygulamaları App Store ve Google Play'e güvenli, denetlenebilir ve tekrarlanabilir biçimde taşımak için kanıta dayalı bir araç seti. Durumu, onayları ve insan kontrol noktalarını güvenlikten ödün vermeden koordine eder.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT lisansı"></a>
  <a href="VERSION"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Sürüm 0.1.0"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS arm64 üzerinde test edildi">
</p>

## Bu proje ne sağlar?

Tek bir klonlanabilir paket içinde mobil uygulama yayınlama skill'ini, manifestleri, pasif harness adaptörlerini, iş akışlarını ve doğrulama araçlarını sunar. Projenin tek resmi giriş noktası [skills/mobile-app-ship/SKILL.md](skills/mobile-app-ship/SKILL.md) dosyasıdır.

Gerekli araçlar Git deposunun dışına kurulur. Binary dosyalar, token'lar, OAuth durumu, kullanıcı yapılandırması ve kimlik bilgileri bu repoda tutulmaz. Ürünün kapsamı, ölçülebilir hedefleri ve başarı ölçütleri için [PRODUCT.md](PRODUCT.md) dosyasına bakın.

## Öne çıkan özellikler

- **Tek doğruluk kaynağı** — canonical skill; preflight, onboarding, bootstrap ve kanıt kaydı adımlarını her hedef uygulama için aynı kurallarla yürütür.
- **Güvenli kurulum** — `bootstrap` varsayılan olarak dry-run çalışır; yalnızca eksik veya sürümü sapmış araçları önerir, mevcut adaptörlerin üzerine yazmaz.
- **Kanıta dayalı durum yönetimi** — `status-write`, hash'e bağlı ve kilitle korunan STATUS işlemlerini ancak gerekli insan onayı verildikten sonra kaydeder.
- **Agent ortamlarından bağımsız** — Pi, Claude Code, Codex, Cursor, Gemini CLI, VS Code ve Windsurf için pasif, kimlik bilgisi içermeyen şablonlar sağlar.
- **Çevrimdışı doğrulama** — yalnızca Python standart kütüphanesini kullanır; çalışma zamanı bağımlılığı yoktur.
- **Git'e sır girmez** — kimlik bilgileri, OAuth durumu ve sağlayıcılardan alınan ham yanıtlar repoya kaydedilmez.

## Hızlı başlangıç

```bash
git clone https://github.com/Srcanesen/mobile-app-ship-playbook.git
cd mobile-app-ship-playbook

# 1. Mevcut bir hedefte önce durumu yalnızca okuyarak inceleyin.
scripts/mobile-app-ship preflight --target /path/to/app --platform ios --json

# Yeni bir hedefte veya STATUS.json bulunmayan bir projede devam ettirilebilir formu açın.
scripts/mobile-app-ship onboard-web --target /path/to/app --no-open
# Tarayıcı kullanılamıyorsa terminal akışını kullanın.
scripts/mobile-app-ship onboard --target /path/to/app --interactive
# Onboarding, .mobile-app-ship-decisions.json dosyasını hedefe kaydeder; dosyayı hedefe özel ve Git dışında tutun.

scripts/mobile-app-ship doctor --harness claude-code --target /path/to/app --platform both
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both
# bootstrap varsayılan olarak dry-run çalışır; planı incelemeden --apply kullanmayın.
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both --apply --approve skill --approve adapter

# 2. Sağlayıcı bağlantılarını tamamlayın ve yalnızca doğrulanmış, temizlenmiş read-back kanıtlarını kaydedin.
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app --record --approve-progress --outcome verified --claim "Sanitized read-back claim" --evidence-id evidence-001 --limitation "Sanitized limitation"
# Başlangıç formunda kapsam dışı bırakılan sağlayıcılar için --outcome not_needed --limitation "Out of scope" kullanın.

# 3. İsterseniz tamamlanan planı kabul edin. Bu işlem yazma yetkisi vermez.
scripts/mobile-app-ship onboard --target /path/to/app --acknowledge-plan
```

Her harici değişiklik için ayrıca açık ve tek kullanımlık onay gerekir. Seçtiğiniz hedefteki [canonical skill](skills/mobile-app-ship/SKILL.md) dosyasını okuyun, [harness onboarding](skills/mobile-app-ship/references/harness-onboarding.md) adımlarını izleyin ve sağlayıcıları sırayla, birer birer bağlayın.

## Desteklenen agent ortamları

Tüm adaptör şablonları repoda pasif olarak bulunur; otomatik olarak yüklenmez veya kullanıcı yapılandırmasına kopyalanmaz. Birincil belgelenmiş yol Pi'dir. Diğer harness'lar isteğe bağlı alternatiflerdir.

| Ortam | Şablon | Notlar |
|---|---|---|
| **Pi** (birincil) | [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) | Pi'nin çekirdeğinde yerleşik MCP istemcisi yoktur; ayrıca onaylanmış `pi-mcp-adapter` uzantısı kullanılır. RevenueCat, kayıtlı olmayan bir Pi OAuth istemcisini reddedebilir. Bu durum sağlayıcıya bağlıdır; körlemesine yeniden denemeyin ([Pi notları](harnesses/pi/README.md)). |
| Claude Code | [harnesses/claude-code/templates/.mcp.json](harnesses/claude-code/templates/.mcp.json) | Projeye özel `.mcp.json` kullanır. |
| Codex | [harnesses/codex/templates/config.toml](harnesses/codex/templates/config.toml) | Projeye özel `.codex/config.toml` kullanır; isteğe bağlıdır. |
| Cursor | [harnesses/cursor/templates/mcp.json](harnesses/cursor/templates/mcp.json) | Projeye özel `.cursor/mcp.json` kullanır. |
| Gemini CLI | [harnesses/gemini-cli/templates/settings.json](harnesses/gemini-cli/templates/settings.json) | Sahte bir skill üretmez; yalnızca onaylı manuel bağlam aktarımı seçeneği sunar. |
| VS Code | [harnesses/vscode/templates/mcp.json](harnesses/vscode/templates/mcp.json) | Çalışma alanına özel `.vscode/mcp.json` kullanır. |
| Windsurf | [harnesses/windsurf/templates/mcp_config.json](harnesses/windsurf/templates/mcp_config.json) | Yalnızca inceleme amaçlıdır; bootstrap tarafından desteklenmez. Kullanıcı genelindeki yapılandırmaya yapılacak birleştirme, insan onayı gerektirir. |

**Pi için önerilen yol:** Ayrı bir yerel onay aldıktan sonra test edilmiş `pi-mcp-adapter` sürümünü kurun. `harnesses/pi/templates/mcp.json` içinden yalnızca kimlik bilgisi içermeyen RevenueCat girdisini `~/.pi/agent/mcp.json` dosyasına ekleyin; yapılandırmayı lazy lifecycle, OAuth ve proxy-only olarak koruyun. Proje içinde `.mcp.json` oluşturmayın, adaptörün init komutunu çalıştırmayın ve kimlik bilgilerini yapıştırmayın. Kimlik doğrulamayı ayrı bir oturumda tamamlayın. Herhangi bir yazma onayından önce RevenueCat tarafında yalnızca read-only keşif yapın.

## Güvenlik modeli

- Kimlik doğrulama ve planın kabul edilmesi yazma yetkisi vermez. Seçilen kapsamlar yalnızca gelecekte yapılması düşünülen işlemleri belirtir.
- Her harici değişiklik şu sırayı izler: **Inspect → Plan → exact single-use approval → Apply once → Read back → Evidence**.
- Build yükleme, test kullanıcısı dağıtımı, mağaza incelemesine gönderim ve genel yayına alma birbirinden ayrı işlemlerdir; her biri ayrı onay gerektirir.
- Public release varsayılan olarak kapalıdır ve kendine ait açık bir onay olmadan uygulanmaz.
- Kapsam veya değer değişirse, secret tespit edilirse, manuel 2FA/hesap/ödeme/yasal işlem gerekirse, yıkıcı kurtarma söz konusuysa ya da zaman aşımının sonucu bilinmiyorsa işlem durdurulur.
- Bu repo yayınlama oyun kitabını barındırır; hedef uygulamanın kendisi değildir. Hedef uygulamaları ayrı dizinlerde tutun. Hedef durumu, kimlik bilgileri, OAuth verileri veya sağlayıcılardan alınan ham yanıtları bu repoya kopyalamayın. Başkasına ait çalışmaları gizlemek veya silmek için `git reset`, `git clean` ya da zorlamalı checkout kullanmayın.

## Proje yapısı

```
├── scripts/mobile-app-ship          # CLI: preflight, onboard, doctor, bootstrap, next-auth, validate
├── skills/mobile-app-ship/          # Canonical skill, referanslar, fixture'lar ve tarayıcı onboarding sayfası
│   └── SKILL.md
├── harnesses/                       # Harness bazlı pasif MCP şablonları (Pi, Codex, Windsurf, ...)
├── schemas/status.schema.json       # Skill asset'iyle byte düzeyinde aynı STATUS işlem şeması
├── tests/fixtures/                  # Geçerli ve geçersiz STATUS fixture'ları
├── .github/workflows/validate.yml   # CI: çevrimdışı doğrulama ve tarayıcı smoke testi
├── Brewfile                         # macOS arm64 kurulum envanteri
├── PRODUCT.md                       # Ürün sınırı ve başarı ölçütleri
├── CONTRIBUTING.md                  # Katkı rehberi
├── SECURITY.md                      # Güvenlik açığı bildirim süreci
└── LICENSE                          # MIT lisansı
```

## Doğrulama

```bash
python3 scripts/test_toolkit.py
python3 scripts/test_onboarding_browser.py
scripts/mobile-app-ship validate
bash scripts/validate-playbook.sh
python3 skills/mobile-app-ship/scripts/validate_playbook.py
git diff --check
```

Doğrulama tamamen çevrimdışı ve read-only çalışır. CI, kök doğrulama betiğini çalıştırır; `CI=true` olduğunda tarayıcı onboarding smoke testi de devreye girer.

## Katkıda bulunma

Katkılarınızı bekliyoruz. Başlamadan önce [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun. Güvenlik açıklarını [SECURITY.md](SECURITY.md) içinde açıklanan yöntemle bildirin. Proje [MIT lisansı](LICENSE) ile yayımlanır. Ürün sınırı ve başarı ölçütleri için [PRODUCT.md](PRODUCT.md) dosyasına bakın.
