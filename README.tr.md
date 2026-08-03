<p align="center">
  <img src=".github/assets/logo.png" alt="Mobile App Ship Playbook" width="110">
</p>

<p align="center"><b><a href="README.md">English</a> | <a href="README.tr.md">Türkçe</a></b></p>

<h1 align="center">Mobile App Ship Playbook</h1>

<p align="center">Flutter/Firebase mobil uygulamalarını App Store ve Google Play'e güvenli, denetlenebilir ve kanıta dayalı biçimde taşımak için agent odaklı bir yayınlama oyun kitabı.</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT lisansı"></a>
  <a href="VERSION"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Sürüm 0.1.0"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS arm64 üzerinde test edildi">
</p>

Bu depo yayınlanacak uygulama değil, coding agent'a verilen yayınlama oyun kitabıdır. **Repoyu kullandığınız agent ortamında klonlayın veya açın**, ardından uygulamanın ayrı klasörünü açıkça `<target-app-dir>` olarak belirtin. Hedef uygulama ayrı kalır; repodaki şablonlar yalnızca pasif örneklerdir. Otomatik olarak bulunmaz, kurulmaz, kopyalanmaz, kimlik doğrulaması yapmaz veya etkinleşmez.

Resmî giriş noktası [skills/mobile-app-ship/SKILL.md](skills/mobile-app-ship/SKILL.md) dosyasıdır. Ürün sınırı ve ölçütleri [PRODUCT.md](PRODUCT.md) içindedir. Binary'leri, OAuth durumunu, token'ları, kullanıcı ayarlarını, kimlik bilgilerini, hedef durumunu ve ham sağlayıcı yanıtlarını bu deponun ve Git'in dışında tutun.

## Oyun kitabını agent'a verin

Agent'a hedef yolu ve istenen kapsamı söyleyin. Agent şu sırayla okumalıdır:

1. [AGENTS.md](AGENTS.md)
2. [ana SKILL.md](skills/mobile-app-ship/SKILL.md)
3. [harness-onboarding.md](skills/mobile-app-ship/references/harness-onboarding.md)
4. Yalnızca skill'in yönlendirdiği ilgili faz veya sağlayıcı referansları

`https://github.com/Srcanesen/mobile-app-ship-playbook.git` adresinden klonlayıp tercih ettiğiniz harness içinde açtıktan sonra aşağıdaki hazır prompt'ları kullanın.

**Mevcut uygulama**

> `<target-app-dir>` konumundaki mevcut uygulamamı bu oyun kitabıyla incele. Önce `AGENTS.md`, sonra `skills/mobile-app-ship/SKILL.md`, ardından `skills/mobile-app-ship/references/harness-onboarding.md` dosyasını oku. Read-only preflight ile başla. Ben her işlem için ayrı ve açık onay vermeden araç kurma, kimlik doğrulama, yapılandırma, yazma veya sağlayıcı çağrısı yapma.

**Yeni uygulama**

> `<target-app-dir>` konumundaki yeni uygulama için bu oyun kitabını kullan. `AGENTS.md`, ana skill ve harness onboarding dosyalarını sırayla oku. Onboarding ile başla, şablonları pasif tut ve dry-run planını göster. İlgili işlemi açıkça onaylamadan hiçbir değişiklik uygulama veya sağlayıcı kimlik doğrulaması başlatma.

**Read-only denetim**

> `<target-app-dir>` konumundaki uygulamayı bu oyun kitabıyla denetle. Zorunlu onboarding zincirini oku ve yalnızca okuma amaçlı keşif yap. Eksik hazırlıkları, sonucu bilinmeyen işlemleri ve sonraki güvenli adımı bildir. Hedef dosyalara yazma, araç kurma, kimlik doğrulama başlatma veya sağlayıcıda değişiklik yapan araçları çağırma.

## Güvenli uçtan uca akış

### 1. Doğru başlangıcı seçin

`STATUS.json` bulunan mevcut bir hedefte `preflight` ile başlayın. Bu komut hedef dosyalara yazmadan, onay kapısı veya plan oluşturmadan ve hiçbir sağlayıcıyı çağırmadan durumu doğrular ve özetler. Yeni bir hedefte ya da `STATUS.json` bulunmayan projede `onboard` veya `onboard-web` kullanın; bunlar yalnızca hassas bilgi içermeyen, kaldığınız yerden sürdürülebilen kararları ve gelecekteki işlem niyetini kaydeder.

```bash
# Mevcut uygulama: yalnızca okuma amaçlı durum incelemesi.
scripts/mobile-app-ship preflight --target "<target-app-dir>" --platform ios --language tr

# Yeni uygulama: iki onboarding yönteminden birini seçin.
scripts/mobile-app-ship onboard --target "<target-app-dir>" --interactive --language tr
scripts/mobile-app-ship onboard-web --target "<target-app-dir>" --no-open
```

### 2. Hazırlığı ve önerilen kurulumu inceleyin

Tek bir harness seçin. Önce `doctor` komutunu çalıştırın, ardından `bootstrap` tarafından üretilen varsayılan dry-run planını inceleyin. Dry-run araç kurmaz, yapılandırma değiştirmez ve şablonları etkinleştirmez. `--apply` harici bir değişiklik uygular; planı gördükten sonra bu işlem için ayrıca açık onay vermeniz gerekir.

```bash
scripts/mobile-app-ship doctor --harness pi --target "<target-app-dir>" --platform both
scripts/mobile-app-ship bootstrap --harness pi --target "<target-app-dir>" --platform both
```

### 3. Sağlayıcıları tek tek doğrulayın

`next-auth`, sıradaki sağlayıcı bağlantısını gösterir. Kullanıcının yönettiği tarayıcı veya yerleşik OAuth akışından sonra yalnızca okuma amaçlı envanter çıkarın ve hassas bilgi içermeyen read-back kanıtını kaydedin. Kimlik doğrulama yalnızca kimliği kanıtlar; yazma yetkisi vermez.

```bash
# Sıradaki sağlayıcı bağlantısını gösterin.
scripts/mobile-app-ship next-auth --harness pi --target "<target-app-dir>"

# Read-back sonrasında güvenli bir doğrulama kaydı oluşturun. Bu işlem yine de yazma yetkisi vermez.
scripts/mobile-app-ship next-auth --harness pi --target "<target-app-dir>" --record --approve-progress --outcome verified --claim "Yalnızca okuma amaçlı envanter doğrulandı" --evidence-id "<evidence-id>" --limitation "Hiçbir değişiklik uygulanmadı"
```

### 4. Tam planı isteğe bağlı kabul edin

Kararlar ve zorunlu read-back'ler tamamlandığında bu adım SHA-256'ya bağlı bir kabul kaydı oluşturur. Yazma onayı değildir. Karar değişirse kabul geçersizleşir.

```bash
scripts/mobile-app-ship onboard --target "<target-app-dir>" --acknowledge-plan
```

### 5. Her mutasyonu ayrı onaylayın

Sağlayıcıda değişiklik yapan her işlemde aşağıdaki onay döngüsünü yeniden uygulayın. Derleme yükleme, test kullanıcılarına dağıtım, mağaza incelemesine gönderim ve herkese açık yayın birbirinden ayrı işlemlerdir; her biri ayrı onay ve kanıt gerektirir. Herkese açık yayın varsayılan olarak kapalıdır.

## Komutların yaptığı ve yapmadığı işler

| Komut | Yaptığı | **Yapmadığı** |
|---|---|---|
| `preflight --target` | Mevcut `STATUS.json` dosyasını okur ve anlamsal olarak doğrular; sonraki devam adımını seçer. | Dosya yazmaz, gate/plan oluşturmaz veya sağlayıcı çağırmaz. |
| `onboard --target` | Hassas bilgi içermeyen kararları ve gelecekte uygulanması istenen kapsamları toplar; `--show` kaldığınız yerden sürdürülebilen planı okur. | Kimlik doğrulama yapmaz, sağlayıcıda yazma işlemini onaylamaz veya seçilen kapsamları yeniden kullanılabilir bir onaya dönüştürmez. |
| `onboard-web --target` | Yalnızca localhost'a bağlanan, gizli bilgi içermeyen onboarding formunu sunar. | Sağlayıcı işlemi yapmaz veya karar durumu dışındaki hedef dosyalarını sunmaz. |
| `doctor --harness --target --platform` | Yerel araç bulunurluğunu ve sürüm sapmasını inceler. | Araç kurmaz, PATH/profile değiştirmez veya kimlik doğrulama yapmaz. |
| `bootstrap --harness --target --platform` | Varsayılan olarak eksik veya sürümü sapmış kurulum işleri için dry-run gösterir. | Planı uygulamaz, mevcut adaptörlerin üzerine yazmaz, bunları birleştirmez veya otomatik kurulum yapmaz. |
| `next-auth --harness --target` | Sıradaki sağlayıcı bağlantısına yönlendirir; açık kayıt seçenekleri kullanıldığında read-back sonrasındaki güvenli ilerlemeyi kaydeder. | Tek başına kimlik doğrulama yapmaz, secret saklamaz veya değişiklik yetkisi vermez. |
| `status-write --target --expect-sha256 --transaction` | Daha önce onaylanmış, hash'e bağlı bir `STATUS` işlemini atomik olarak kaydeder. | Sağlayıcıdaki işlemi onaylamaz, sağlayıcıya bağlanmaz veya işlemi çalıştırmaz; güvenli POSIX kilitlemesi yoksa değişiklik yapmadan durur. |
| `coverage --target --platform` | Yalnızca okuma amaçlı sorumluluk kapsamını, kapsam bağını ve sonucu bilinmeyen işlemleri raporlar. | Hazırlık puanı üretmez veya sağlayıcı çalıştırmaz. |
| `validate` | Oyun kitabını yerelde doğrular. | Uygulama yayınlamaz, sağlayıcı çağırmaz veya uygulama/sağlayıcı durumunu değiştirmez. |

İnsan tarafından okunacak `preflight` ve `onboard` çıktısında açıkça `--language tr` veya `--language en` kullanın. `--json` makine uyumludur ve hiçbir zaman yerelleştirilmez.

## Kimlik doğrulama: güvenli, sıralı, kullanıcı kontrolünde

Harness'ın kendi tarayıcı veya OAuth arayüzünü kullanın. Token, parola, yönlendirme sırrı, `.p8` içeriği, özel anahtar veya service-account JSON bilgisini sohbete, Git'e ya da hedef durumuna asla yapıştırmayın. **Bir seferde yalnızca bir harness ve bir sağlayıcı** bağlayın. Önce yalnızca okuma amaçlı envanteri çıkarın ve sağlayıcı durumunu read-back ile doğrulayın; ardından sonucu hassas bilgi içermeyen kanıt ve sınırlamalarla `verified`, `deferred` veya `not_needed` olarak kaydedin. `verified` sonucu için boş olmayan bir read-back `claim` değeri ve `evidence ID` gerekir. `deferred` tamamlanmış sayılmaz; kaldığınız yerden devam ettiğinizde sıradaki adım olarak kalır.

Gerektiğinde, komut uydurmadan şu sırayı izleyin:

1. **Apple/App Store Connect:** Kurulu `asc` komutunun desteklediği yetenekleri keşfedin; araç destekliyorsa yerleşik tarayıcıyla kimlik doğrulama akışını kullanın. Ardından yalnızca okuma amaçlı takım ve uygulama envanteri çıkarın.
2. **XcodeBuildMCP:** Apple read-back sonrasında gerektiğinde kurulum ve adaptör etkinleştirme için ayrı onay alın. OAuth kullanmaz. Yerel proje ve araç keşfinde; signing hazırlandıktan sonra da build, test, simulator, cihaz ve log işlerinde kullanılır. Sertifika, profil veya portal yapılandırmasının sahibi değildir.
3. **RevenueCat:** Seçtiğiniz harness destekliyorsa resmî MCP endpoint'ini ve yerleşik tarayıcı OAuth akışını kullanın. Önce canlı araç şemalarını keşfedin, ardından yalnızca okuma amaçlı proje ve uygulama envanteri çıkarın.
4. **Firebase:** Tarayıcıyla oturum açmayı yalnızca backend çalışması başlayacağı zaman başlatın.
5. **Google Play:** Service-account kimlik bilgileriyle ilgili işlemleri yalnızca Android çalışması başlayacağı zaman başlatın.

Zaman aşımı `outcome_unknown` anlamına gelir; tek başına başarı veya hata değildir. Yeniden denemeden ya da yeni bir onay istemeden önce sağlayıcının güncel durumunu okuyun. Bir komutun çıkış koduna bakarak sağlayıcı durumunu asla varsaymayın.

### Birincil belgelenmiş yol: Pi

Pi'nin çekirdeğinde yerleşik MCP istemcisi yoktur. RevenueCat yedek yöntemi (fallback) için **ayrı bir yerel onay** gerekir: [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) dosyasındaki kimlik bilgisi içermeyen girdiyi ve [harnesses/pi/README.md](harnesses/pi/README.md) yönergelerini kullanın. Yapılandırmayı kullanıcı genelinde, lazy lifecycle, OAuth, proxy-only ve Git dışında tutun; proje içinde MCP dosyası oluşturmayın ve `pi-mcp-adapter init` çalıştırmayın. Kimlik doğrulamayı ayrı bir Pi oturumunda yapın; her yazma onayından önce yalnızca okuma amaçlı RevenueCat keşfi yürütün.

RevenueCat, kayıtlı olmayan bir Pi OAuth istemcisini reddedebilir. Bu durum sağlayıcıya bağlıdır: körlemesine yeniden denemeyin; istemcinin RevenueCat allowlist'ine eklenmesini veya belgelenmiş kullanıcı düzeyindeki bearer-token fallback yolunu kullanın.

## Harness'lar ve pasif şablonlar

Şablonlar, kapsamı açıkça belirlenmiş bir etkinleştirme onayı verilene kadar pasif kalır. Pi birincil belgelenmiş yoldur; kullanıcı seçtiğinde diğer seçenekler de kullanılabilir.

| Harness | Şablon | Notlar |
|---|---|---|
| **Pi** (birincil) | [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) | Pi çekirdeğinde yerleşik MCP yoktur; ayrıca onaylanmış `pi-mcp-adapter` fallback yöntemi kullanılır. RevenueCat kayıtlı olmayan bir Pi OAuth istemcisini reddedebilir; körlemesine yeniden denemeyin ([Pi notları](harnesses/pi/README.md)). |
| Claude Code | [harnesses/claude-code/templates/.mcp.json](harnesses/claude-code/templates/.mcp.json) | Proje içindeki `.mcp.json` dosyasını kullanır. |
| Codex | [harnesses/codex/templates/config.toml](harnesses/codex/templates/config.toml) | Proje içindeki `.codex/config.toml` dosyasını kullanır; isteğe bağlıdır. |
| Cursor | [harnesses/cursor/templates/mcp.json](harnesses/cursor/templates/mcp.json) | Proje içindeki `.cursor/mcp.json` dosyasını kullanır. |
| Gemini CLI | [harnesses/gemini-cli/templates/settings.json](harnesses/gemini-cli/templates/settings.json) | Sahte bir yerleşik skill oluşturmaz; yalnızca onaylı manuel bağlam aktarma seçeneği sunar. |
| VS Code | [harnesses/vscode/templates/mcp.json](harnesses/vscode/templates/mcp.json) | Çalışma alanındaki `.vscode/mcp.json` dosyasını kullanır. |
| Windsurf | [harnesses/windsurf/templates/mcp_config.json](harnesses/windsurf/templates/mcp_config.json) | Yalnızca inceleme içindir; bootstrap tarafından desteklenmez. Kullanıcı genelindeki yapılandırmaya birleştirme işlemi insan onayı gerektirir. |

## Durum, devam etme ve kanıt

Çalışma durumu bu oyun kitabında değil, hedef uygulamanın klasöründe tutulur. Tek bir ana teslimat kaydı kullanın: `STATUS.json` **veya** `PROGRESS.md`.

| Hedefte tutulan dosya | Amaç | Güvenlik kuralı |
|---|---|---|
| `.mobile-app-ship-decisions.json` | Hassas bilgi içermeyen onboarding kararları ve ileride uygulanması istenen kapsamlar. | Secret saklamayın; gerekirse dosyayı hedef projenin Git ignore kurallarına kendiniz ekleyin. Karar değişikliği plan kabulünü geçersizleştirir. |
| `.mobile-app-ship-onboarding.json` | Geriye uyumlu `next-auth` bağlantı ilerlemesi. | Secret saklamayın; yalnızca sağlayıcıdan okunarak doğrulanmış bir durumdan devam edin. |
| `STATUS.json` **veya** `PROGRESS.md` | Ana teslimat durumu, eylemler, kanıtlar, engeller ve onay kapıları. | Tam olarak birini tutun. `status-write`, güncel `--expect-sha256` değerini ister ve yalnızca daha önce onaylanmış bir işlemi kaydeder. |

Hassas bilgi içermeyen durumu `onboard --show` veya `--json` ile inceleyin. Bir komutun sonraki adımı ekrana yazması ya da sıfır çıkış kodu döndürmesi, işlemin tamamlandığını kanıtlamaz. Bunun yerine sağlayıcı durumunu read-back ile doğruladıktan sonra güvenli kanıt kaydedin.

## Onay sınıfları

Planın kabul edilmesi, “Tamamlanmış kararları ve read-back sonuçlarını gözden geçirdim” anlamına gelir. “Sağlayıcıda yazma işlemi yap” anlamına gelmez. Seçilen kapsam da yalnızca bir işlemin daha sonra istenebileceğini belirtir; tek başına onay değildir.

Sağlayıcıda değişiklik yapan her işlem, o işlemin hedefi ve güncel değerleri için açık, tek kullanımlık onay gerektirir:

**Inspect → Plan → exact single-use approval → Apply once → Read back → Evidence**

Kapsam veya değer değişirse; gizli bilgi, manuel 2FA, hesap, ödeme ya da hukuki işlem gerekirse; yıkıcı kurtarma veya iptal önerilirse ya da sonuç bilinmiyorsa durun. Yeni onayı ancak güncel durumu read-back ile doğruladıktan sonra isteyin.

## Sık durumlar ve sorun giderme

- **Durumu olan mevcut uygulama:** `preflight` çalıştırın; yeniden denemeden önce `outcome_unknown` durumunu read-back ile çözün.
- **Yeni uygulama veya `STATUS.json` yok:** `onboard` ya da `onboard-web` kullanın; kabulden önce zorunlu kararları tamamlayın.
- **Araç/adaptör gerekirse:** `doctor` ve dry-run `bootstrap` çıktısını inceleyin; kurulum/etkinleştirme için ayrı onay isteyin. Hiçbir şey kendini kurmaz.
- **Sağlayıcı bağlı ama kanıt yoksa:** Sağlayıcıda yalnızca okuma amaçlı envanter çıkarın; hassas bilgi içermeyen `verified`, `deferred` veya `not_needed` ilerlemesi kaydedin.
- **RevenueCat Pi OAuth'ı reddederse:** Yeniden denemeyi bırakın ve yukarıdaki Pi fallback yolunu izleyin.
- **Kaldığınız yerden devam etmek gerekirse:** Hedef uygulamadaki üç durum kaydını okuyun; iOS ve Android geçmişlerini, engellerini ve onaylarını birbirinden ayrı tutun.

## Bu depoyu doğrulayın

```bash
PYTHONDONTWRITEBYTECODE=1 CI=true bash scripts/validate-playbook.sh
git diff --check
git status --short
```

Katkı için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun. Güvenlik açıklarını [SECURITY.md](SECURITY.md) üzerinden bildirin. Proje [MIT lisanslıdır](LICENSE); kapsam ve başarı ölçütleri için [PRODUCT.md](PRODUCT.md) dosyasına bakın.
