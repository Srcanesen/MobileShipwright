<p align="center">
  <img src=".github/assets/logo.png" alt="Mobile App Ship Playbook" width="110">
</p>

<p align="center"><b><a href="README.md">English</a> | <a href="README.tr.md">Türkçe</a></b></p>

<h1 align="center">Mobile App Ship Playbook</h1>

<p align="center">
  Flutter/Firebase uygulamalarını bağımsız iOS App Store ve Android Play yollarından yayınlamak için kanıt öncelikli (evidence-first), klonlanabilir bir araç seti; güvenlikten ödün vermeden durum, onay ve insan kapılarını (human gates) koordine eder.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT lisansı"></a>
  <a href="VERSION"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Sürüm 0.1.0"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS arm64 üzerinde test edildi">
</p>

## Bu ne

Klonlanabilir tek bir paket: mobil uygulamaları ayrı App Store ve Play yollarından yayınlamak için kanonik skill, manifestler, pasif harness bağdaştırıcıları, iş akışları ve doğrulama içerir. Tek giriş noktası [skills/mobile-app-ship/SKILL.md](skills/mobile-app-ship/SKILL.md) dosyasıdır.

Araçlar Git dışına kurulur; bu depoda hiçbir ikili dosya, belirteç (token), OAuth durumu, kullanıcı yapılandırması veya kimlik bilgisi bulunmaz. Ürün sınırı, ölçülebilir kapsam ve başarı ölçütleri için [PRODUCT.md](PRODUCT.md) dosyasına bakın.

## Özellikler

- **Tek kanonik skill** — herhangi bir hedef uygulama için preflight, onboarding, bootstrap ve kanıt kaydını yürütür.
- **Güvenli bootstrap** — varsayılan olarak kuru çalıştırmadır (dry-run); yalnızca eksik veya sapmış araçları önerir ve mevcut bağdaştırıcıların üzerine asla yazmaz.
- **Kanıt öncelikli durum** — `status-write`, hash ile bağlı, kilit korumalı STATUS işlemlerini yalnızca insan onayından sonra kaydeder.
- **Harness'tan bağımsız** — Pi, Claude Code, Codex, Cursor, Gemini CLI, VS Code ve Windsurf için pasif, kimlik bilgisi içermeyen şablonlar.
- **Çevrimdışı doğrulama** — yalnızca Python standart kütüphanesi; çalışma zamanı bağımlılığı yoktur.
- **Git'te sır yok** — kimlik bilgileri, OAuth durumu ve ham satıcı yanıtları depoya asla girmez.

## Hızlı başlangıç

```bash
git clone https://github.com/Srcanesen/mobile-app-ship-playbook.git
cd mobile-app-ship-playbook

# 1. Existing target: inspect its state read-only first.
scripts/mobile-app-ship preflight --target /path/to/app --platform ios --json

# New target, or a target without STATUS.json: fill the resumable form.
scripts/mobile-app-ship onboard-web --target /path/to/app --no-open
# Or use the terminal flow when a browser is unavailable.
scripts/mobile-app-ship onboard --target /path/to/app --interactive
# Onboarding stores .mobile-app-ship-decisions.json in the target; keep it target-local and ignored.

scripts/mobile-app-ship doctor --harness claude-code --target /path/to/app --platform both
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both
# bootstrap is dry-run by default; --apply only after inspecting the plan.
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both --apply --approve skill --approve adapter

# 2. Complete provider connections and record only vendor read-back evidence.
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app --record --approve-progress --outcome verified --claim "Sanitized read-back claim" --evidence-id evidence-001 --limitation "Sanitized limitation"
# Use --outcome not_needed --limitation "Out of scope" for providers the initial form excludes.

# 3. Optionally acknowledge the complete plan. This is not write approval.
scripts/mobile-app-ship onboard --target /path/to/app --acknowledge-plan
```

Her dış değişiklik yine kendi tek kullanımlık kesin onayına (exact single-use approval) ihtiyaç duyar. Seçtiğiniz hedefteki [kanonik skill](skills/mobile-app-ship/SKILL.md) dosyasını okuyun, [harness onboarding](skills/mobile-app-ship/references/harness-onboarding.md) sürecini izleyin ve sağlayıcıları tek tek bağlayın.

## Desteklenen harness'lar

Tüm bağdaştırıcı şablonları pasif depo malzemesidir; asla otomatik yüklenmez veya kopyalanmaz. Pi birincil belgelenmiş yoldur; diğer tüm harness'lar isteğe bağlıdır.

| Harness | Şablon | Notlar |
|---|---|---|
| **Pi** (birincil) | [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) | Pi çekirdeğinin yerel MCP istemcisi yoktur; ayrıca onaylanan `pi-mcp-adapter` uzantısını kullanır. RevenueCat kayıtlı olmayan bir Pi OAuth istemcisini reddedebilir — sağlayıcıya bağlıdır; körlemesine tekrar denemeyin ([harness notları](harnesses/pi/README.md)). |
| Claude Code | [harnesses/claude-code/templates/.mcp.json](harnesses/claude-code/templates/.mcp.json) | Proje yerel `.mcp.json`. |
| Codex | [harnesses/codex/templates/config.toml](harnesses/codex/templates/config.toml) | Proje yerel `.codex/config.toml`; isteğe bağlıdır, zorunlu değildir. |
| Cursor | [harnesses/cursor/templates/mcp.json](harnesses/cursor/templates/mcp.json) | Proje yerel `.cursor/mcp.json`. |
| Gemini CLI | [harnesses/gemini-cli/templates/settings.json](harnesses/gemini-cli/templates/settings.json) | Sahte skill yoktur; yalnızca onaylanmış manuel bağlam geri dönüşü (fallback). |
| VS Code | [harnesses/vscode/templates/mcp.json](harnesses/vscode/templates/mcp.json) | Çalışma alanı/proje `.vscode/mcp.json`. |
| Windsurf | [harnesses/windsurf/templates/mcp_config.json](harnesses/windsurf/templates/mcp_config.json) | Yalnızca inceleme; bootstrap için desteklenmez; manuel insan kapısı birleştirmesi kullanıcı geneli yapılandırmaya yapılır. |

**Pi birincil yolu.** Ayrı bir yerel onaydan sonra test edilmiş `pi-mcp-adapter` uzantısını kurun ve `harnesses/pi/templates/mcp.json` içinden yalnızca kimlik bilgisi içermeyen RevenueCat girdisini `~/.pi/agent/mcp.json` dosyasına birleştirin — tembel yaşam döngüsü, OAuth, yalnızca proxy. Asla proje `.mcp.json` dosyası oluşturmayın, bağdaştırıcının init komutunu çalıştırmayın veya kimlik bilgisi yapıştırmayın. Ayrı bir oturumda kimlik doğrulayın ve herhangi bir yazma kapısından önce yalnızca okuma amaçlı RevenueCat keşfi yapın.

## Güvenlik modeli

- Kimlik doğrulama ve plan onayı hiçbir zaman yazma yetkisi vermez; seçilen kapsamlar yalnızca gelecekteki niyettir.
- Her dış değişiklik şu zinciri izler: **Inspect → Plan → exact single-use approval → Apply once → Read back → Evidence**.
- Yükleme, test kullanıcısı dağıtımı, gönderim ve yayın, ayrı tüketilen kapılara (consumed gates) sahip ayrı işlemlerdir.
- Genel yayın (public release) varsayılan olarak hayırdır ve kendi kesin onayını gerektirir.
- Kapsam/değer sapması, sırlar, manuel 2FA/hesap/ödeme/yasal işlemler, yıkıcı kurtarma veya bilinmeyen zaman aşımlarında durun.
- Bu depo oyun kitabıdır, yayınlanan hedef uygulama değildir: her hedefi ayrı bir dizinde tutun ve hedef durumunu, kimlik bilgilerini, OAuth durumunu veya ham satıcı yanıtlarını asla buraya kopyalamayın. Başkasının işini gizlemek veya kaldırmak için `git reset`, `git clean` veya zorlamalı checkout asla kullanmayın.

## Proje yapısı

```
├── scripts/mobile-app-ship          # CLI: preflight, onboard, doctor, bootstrap, next-auth, validate
├── skills/mobile-app-ship/          # Canonical skill, references, fixtures, browser onboarding page
│   └── SKILL.md
├── harnesses/                       # Inactive per-harness MCP templates (Pi, Codex, Windsurf, ...)
├── schemas/status.schema.json       # STATUS transaction schema (byte-identical to the skill asset)
├── tests/fixtures/                  # Valid and invalid STATUS fixtures
├── .github/workflows/validate.yml   # CI: offline validation plus browser smoke
├── Brewfile                         # macOS arm64 install inventory
├── PRODUCT.md                       # Product boundary and success metrics
├── CONTRIBUTING.md                  # Contribution guidelines
├── SECURITY.md                      # Vulnerability reporting
└── LICENSE                          # MIT license
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

Doğrulama çevrimdışı ve yalnızca okumadır. CI, kök betiği (root wrapper) çalıştırır; `CI=true` olduğunda onboarding tarayıcı duman testini (browser smoke) de çalıştırır.

## Katkıda bulunma

Katkılar memnuniyetle karşılanır — önce [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun. Güvenlik açıklarını [SECURITY.md](SECURITY.md) içindeki süreç üzerinden bildirin. Bu proje [MIT lisansı](LICENSE) ile lisanslıdır. Ürün sınırı ve başarı ölçütleri için [PRODUCT.md](PRODUCT.md) dosyasına bakın.
