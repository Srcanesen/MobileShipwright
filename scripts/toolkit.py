#!/usr/bin/env python3
"""Offline, secret-safe entry point for the mobile-app-ship toolkit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import ipaddress
import json
import os
import platform
import re
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import webbrowser
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl
    fcntl = None
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/mobile-app-ship"
MANIFEST = SKILL / "assets/tool-manifest.json"
ONBOARDING_SCHEMA = SKILL / "assets/onboarding.schema.json"
ONBOARDING_HTML = SKILL / "assets/onboarding.html"
HARNESSES = {
    "claude-code": {"skill": ".claude/skills/mobile-app-ship", "adapter": ".mcp.json", "template": "harnesses/claude-code/templates/.mcp.json"},
    "codex": {"skill": ".agents/skills/mobile-app-ship", "adapter": ".codex/config.toml", "template": "harnesses/codex/templates/config.toml"},
    "cursor": {"skill": ".cursor/skills/mobile-app-ship", "adapter": ".cursor/mcp.json", "template": "harnesses/cursor/templates/mcp.json"},
    "vscode": {"skill": ".github/skills/mobile-app-ship", "adapter": ".vscode/mcp.json", "template": "harnesses/vscode/templates/mcp.json"},
    "windsurf": {"skill": ".windsurf/skills/mobile-app-ship", "adapter": None, "template": "harnesses/windsurf/templates/mcp_config.json", "manualAdapter": "~/.codeium/windsurf/mcp_config.json"},
    "gemini-cli": {"skill": None, "adapter": ".gemini/settings.json", "template": "harnesses/gemini-cli/templates/settings.json"},
    "pi": {"skill": ".agents/skills/mobile-app-ship", "adapter": None, "template": None},
}
PROGRESS = ".mobile-app-ship-onboarding.json"
AUTH_SEQUENCE = [
    ("apple", "Run asc auth status. If empty, use asc auth login help and the system-keychain flow with a user-selected .p8 path; then verify with asc apps list --output table. Never copy key material into chat."),
    ("xcodebuildmcp", "Activate the approved adapter, discover its schema, then run local read-only discovery. No OAuth."),
    ("revenuecat", "Use native harness OAuth if officially supported, then read-only projects/apps discovery; otherwise Human gate."),
    ("firebase", "Begin browser login only when backend work begins."),
    ("gcloud-play", "Begin gcloud/Play credentials only when Android work begins."),
]
AUTH_CONNECTIONS = {
    "connection.asc": "apple",
    "connection.xcodebuildmcp": "xcodebuildmcp",
    "connection.revenuecat": "revenuecat",
    "connection.firebase": "firebase",
    "connection.gcloud_play": "gcloud-play",
}
ONBOARDING_SCHEMA_VERSION = "3.0.0"
LEGACY_ONBOARDING_SCHEMA_VERSION = "2.0.0"
AUTHORIZATION_SCOPES = {
    "authorization.firebase_create_deploy": "firebase.create_deploy",
    "authorization.app_store_records_metadata": "app_store.records_metadata",
    "authorization.iap_catalog": "iap.catalog",
    "authorization.pricing_availability": "pricing.availability",
    "authorization.revenuecat_config": "revenuecat.config",
    "authorization.signing_assets": "signing.assets",
    "authorization.screenshot_upload_replace": "screenshots.upload_replace",
    "authorization.build_upload": "build.upload",
    "authorization.testflight_distribution": "testflight.distribution",
    "authorization.review_submission": "review.submission",
    "authorization.public_release": "public_release",
}
FIELD_DESCRIPTORS = {
    "tooling.harness": ("AI harness", "Yapay zeka araç ortamı", "Select the local coding harness that will receive this plan and its inactive adapter instructions.", "Bu planı ve etkin olmayan adaptör talimatlarını alacak yerel kodlama araç ortamını seçer."),
    "project.platforms": ("Shipping platforms", "Yayın platformları", "Sets whether later checks and store work cover iOS, Android, or two independent paths.", "Sonraki denetimlerin ve mağaza işlerinin iOS, Android ya da iki bağımsız yolu kapsamasını belirler."),
    "connection.asc": ("App Store Connect readiness", "App Store Connect hazırlığı", "Records whether App Store Connect read-only access can be verified later; it never authenticates here.", "App Store Connect salt okunur erişiminin daha sonra doğrulanıp doğrulanamayacağını kaydeder; burada kimlik doğrulamaz."),
    "connection.firebase": ("Firebase readiness", "Firebase hazırlığı", "Records whether Firebase and gcloud discovery can proceed when backend work starts.", "Arka uç işi başladığında Firebase ve gcloud keşfinin ilerleyip ilerleyemeyeceğini kaydeder."),
    "connection.revenuecat": ("RevenueCat readiness", "RevenueCat hazırlığı", "Records whether RevenueCat transport and read-only project discovery are available for purchase setup.", "Satın alma kurulumu için RevenueCat bağlantısının ve salt okunur proje keşfinin kullanılabilirliğini kaydeder."),
    "connection.flutter": ("Flutter readiness", "Flutter hazırlığı", "Records whether the tested Flutter toolchain is available before app builds are planned.", "Uygulama derlemeleri planlanmadan önce test edilen Flutter araç zincirinin kullanılabilirliğini kaydeder."),
    "connection.xcode": ("Xcode readiness", "Xcode hazırlığı", "Records whether local Apple builds and signing inspection can run on this machine.", "Yerel Apple derlemelerinin ve imzalama incelemesinin bu makinede çalışıp çalışamayacağını kaydeder."),
    "connection.xcodebuildmcp": ("XcodeBuildMCP readiness", "XcodeBuildMCP hazırlığı", "Records whether local Xcode tool discovery is available without granting store access.", "Mağaza erişimi vermeden yerel Xcode araç keşfinin kullanılabilirliğini kaydeder."),
    "connection.gcloud_play": ("Google Cloud and Play readiness", "Google Cloud ve Play hazırlığı", "Records whether Google Cloud and Play read-only discovery can proceed for Android work.", "Android işi için Google Cloud ve Play salt okunur keşfinin ilerleyip ilerleyemeyeceğini kaydeder."),
    "app.name": ("App name", "Uygulama adı", "Names the app in the saved plan so later store records and evidence refer to the correct product.", "Sonraki mağaza kayıtlarının ve kanıtların doğru ürüne bağlanması için kayıtlı planda uygulamayı adlandırır."),
    "app.bundle_id": ("iOS bundle ID", "iOS bundle kimliği", "Identifies the exact iOS app record and prevents work against a different App Store target.", "Kesin iOS uygulama kaydını tanımlar ve farklı bir App Store hedefinde işlem yapılmasını önler."),
    "app.package_name": ("Android package name", "Android paket adı", "Identifies the exact Android application ID used by builds, Firebase, and Google Play.", "Derlemeler, Firebase ve Google Play tarafından kullanılan kesin Android uygulama kimliğini tanımlar."),
    "support.email": ("Public support email", "Genel destek e-postası", "Sets the customer-visible support address that store listings may publish.", "Mağaza listelerinde yayınlanabilecek, müşterilerin göreceği destek adresini belirler."),
    "review.first_name": ("Review contact first name", "İnceleme kişisi adı", "Provides the first name of the person stores may contact when review is blocked.", "İnceleme engellendiğinde mağazaların iletişim kurabileceği kişinin adını sağlar."),
    "review.last_name": ("Review contact last name", "İnceleme kişisi soyadı", "Provides the last name of the accountable review contact.", "Sorumlu inceleme kişisinin mağaza iletişiminde kullanılacak soyadını sağlar."),
    "review.email": ("Review contact email", "İnceleme kişisi e-postası", "Provides a monitored private contact address for store review questions.", "Mağaza inceleme soruları için takip edilen özel iletişim adresini sağlar."),
    "review.phone": ("Review contact phone", "İnceleme kişisi telefonu", "Provides an international-format phone number for urgent store review contact.", "Acil mağaza inceleme iletişimi için uluslararası biçimde telefon numarası sağlar."),
    "review.demo_access_required": ("Demo access", "Demo erişimi", "Determines whether reviewers need a later credential handoff or a manual access gate; credentials never belong here.", "İnceleyicilerin daha sonra kimlik bilgisi aktarımına mı yoksa manuel erişim kapısına mı ihtiyaç duyduğunu belirler; kimlik bilgileri buraya girilmez."),
    "listing.primary_locale": ("Primary store locale", "Birincil mağaza listeleme dili", "Sets the canonical App Store Connect source locale used when localized metadata falls back.", "Yerelleştirilmiş meta veri olmadığında kullanılacak kanonik App Store Connect kaynak dilini belirler; tek bir kod girin, örneğin tr veya en-US."),
    "listing.locales": ("Shipping locales", "Mağaza listeleme dilleri", "Lists every store locale that needs complete, reviewed metadata before submission.", "Mağaza listesinde yayınlanacak kanonik dilleri virgülle ayırarak listeler; örneğin tr,en-US. Her dil için gönderimden önce eksiksiz ve incelenmiş meta veri gerekir; tr kullanın, tr-TR kullanmayın."),
    "listing.territories": ("Sales territories", "Satış bölgeleri", "Limits the countries or regions where pricing and availability will be planned.", "Fiyatlandırma ve kullanılabilirliğin planlanacağı ülke veya bölgeleri büyük harfli ISO kodlarıyla sınırlar; örneğin TR,US."),
    "pricing.app": ("App price", "Uygulama fiyatı", "Records free status or the intended base price context; changing it later requires a new scoped plan.", "Ücretsiz durumu veya amaçlanan temel fiyat bağlamını kaydeder; daha sonra değiştirmek yeni kapsamlı plan gerektirir."),
    "pricing.iaps": ("In-app purchases", "Uygulama içi satın almalar", "Defines the intended product catalog and base prices so store and RevenueCat records can be reconciled.", "Mağaza ve RevenueCat kayıtlarının karşılaştırılabilmesi için amaçlanan ürün kataloğunu ve temel fiyatları tanımlar."),
    "distribution.release_mode": ("Release mode", "Yayın modu", "Controls how an approved version becomes available after store approval.", "Onaylanan sürümün mağaza onayından sonra nasıl kullanıma açılacağını belirler."),
    "screenshots.device_families": ("Screenshot device families", "Ekran görüntüsü cihaz aileleri", "Sets which Apple device families need compliant screenshot sets before submission.", "Gönderimden önce hangi Apple cihaz aileleri için uyumlu ekran görüntüsü setleri gerektiğini belirler."),
    "privacy.readiness": ("Privacy readiness", "Gizlilik hazırlığı", "Records whether data-use declarations are reviewable now or remain a submission blocker.", "Veri kullanımı beyanlarının şimdi incelenebilir olup olmadığını ya da gönderim engeli olarak kalacağını kaydeder."),
    "distribution.build_policy": ("Build selection policy", "Derleme seçim politikası", "Defines which inspected build may be proposed for TestFlight or submission and avoids accidental latest-build selection.", "TestFlight veya gönderim için hangi incelenmiş derlemenin önerilebileceğini belirler ve yanlışlıkla en son derlemenin seçilmesini önler."),
    "authorization.firebase_create_deploy": ("Firebase create and deploy intent", "Firebase oluşturma ve dağıtım niyeti", "Records whether a future plan may propose Firebase resource creation or deployment.", "Gelecekteki bir planın Firebase kaynağı oluşturmayı veya dağıtmayı önerebilip öneremeyeceğini kaydeder."),
    "authorization.app_store_records_metadata": ("App Store records and metadata intent", "App Store kayıtları ve meta veri niyeti", "Records whether a future plan may propose creating or changing App Store records and metadata.", "Gelecekteki bir planın App Store kayıtları ve meta verilerini oluşturmayı veya değiştirmeyi önerebilip öneremeyeceğini kaydeder."),
    "authorization.iap_catalog": ("IAP catalog intent", "Uygulama içi satın alma kataloğu niyeti", "Records whether a future plan may propose creating or changing in-app purchase products.", "Gelecekteki bir planın uygulama içi satın alma ürünleri oluşturmayı veya değiştirmeyi önerebilip öneremeyeceğini kaydeder."),
    "authorization.pricing_availability": ("Pricing and availability intent", "Fiyat ve kullanılabilirlik niyeti", "Records whether a future plan may propose store price or territory availability changes.", "Gelecekteki bir planın mağaza fiyatı veya bölgesel kullanılabilirlik değişikliği önerebilip öneremeyeceğini kaydeder."),
    "authorization.revenuecat_config": ("RevenueCat configuration intent", "RevenueCat yapılandırma niyeti", "Records whether a future plan may propose RevenueCat product, entitlement, or offering changes.", "Gelecekteki bir planın RevenueCat ürün, yetki veya teklif değişikliği önerebilip öneremeyeceğini kaydeder."),
    "authorization.signing_assets": ("Signing assets intent", "İmzalama varlıkları niyeti", "Records whether a future plan may propose certificate, profile, or signing configuration changes.", "Gelecekteki bir planın sertifika, profil veya imzalama yapılandırması değişikliği önerebilip öneremeyeceğini kaydeder."),
    "authorization.screenshot_upload_replace": ("Screenshot upload or replace intent", "Ekran görüntüsü yükleme veya değiştirme niyeti", "Records whether a future plan may propose uploading or replacing store screenshots.", "Gelecekteki bir planın mağaza ekran görüntülerini yüklemeyi veya değiştirmeyi önerebilip öneremeyeceğini kaydeder."),
    "authorization.build_upload": ("Build upload intent", "Derleme yükleme niyeti", "Records whether a future plan may propose uploading an inspected binary to a store.", "Gelecekteki bir planın incelenmiş bir uygulama dosyasını mağazaya yüklemeyi önerebilip öneremeyeceğini kaydeder."),
    "authorization.testflight_distribution": ("TestFlight distribution intent", "TestFlight dağıtım niyeti", "Records whether a future plan may propose assigning a build to TestFlight testers.", "Gelecekteki bir planın bir derlemeyi TestFlight test kullanıcılarına atamayı önerebilip öneremeyeceğini kaydeder."),
    "authorization.review_submission": ("Review submission intent", "İncelemeye gönderme niyeti", "Records whether a future plan may propose submitting a prepared version for store review.", "Gelecekteki bir planın hazırlanmış sürümü mağaza incelemesine göndermeyi önerebilip öneremeyeceğini kaydeder."),
    "authorization.public_release": ("Public release intent", "Genel yayın niyeti", "Records future intent for the highest-risk action: making an approved version public. It defaults to no.", "En yüksek riskli işlem olan onaylı sürümü herkese açma niyetini kaydeder. Varsayılanı hayırdır."),
}
# Presentation-only guidance served to the browser. It is never validated; the canonical server validator in
# onboarding_value() remains the single source of truth for every field value.
FIELD_GUIDANCE = {
    "tooling.harness": {
        "en": {"format": "Choose one of the listed harnesses.", "example": "pi", "why": "The saved plan and its inactive adapter instructions target this local coding harness."},
        "tr": {"format": "Listedeki araç ortamlarından birini seçin.", "example": "pi", "why": "Kaydedilen plan ve etkin olmayan adaptör talimatları bu yerel kodlama araç ortamını hedefler."},
    },
    "project.platforms": {
        "en": {"format": "Choose one option: ios, android, or both.", "example": "ios", "why": "Sets which store path later checks, evidence, and release gates cover."},
        "tr": {"format": "Bir seçenek seçin: ios, android veya both.", "example": "ios", "why": "Sonraki denetimlerin, kanıtların ve yayın kapılarının hangi mağaza yolunu kapsadığını belirler."},
    },
    "connection.asc": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether App Store Connect read-only verification can run later; it never authenticates or grants access here."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "App Store Connect salt okunur doğrulamasının daha sonra çalışıp çalışamayacağını kaydeder; burada kimlik doğrulamaz veya erişim vermez."},
    },
    "connection.firebase": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether Firebase and gcloud discovery can run when backend work starts."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Arka uç işi başladığında Firebase ve gcloud keşfinin çalışıp çalışamayacağını kaydeder."},
    },
    "connection.revenuecat": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether RevenueCat read-only project discovery is available for purchase setup."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Satın alma kurulumu için RevenueCat salt okunur proje keşfinin kullanılabilirliğini kaydeder."},
    },
    "connection.flutter": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether the tested Flutter toolchain is available before builds are planned."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Derlemeler planlanmadan önce test edilen Flutter araç zincirinin kullanılabilirliğini kaydeder."},
    },
    "connection.xcode": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether local Apple builds and signing inspection can run on this machine."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Yerel Apple derlemelerinin ve imzalama incelemesinin bu makinede çalışıp çalışamayacağını kaydeder."},
    },
    "connection.xcodebuildmcp": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether local Xcode tool discovery is available without granting store access."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Mağaza erişimi vermeden yerel Xcode araç keşfinin kullanılabilirliğini kaydeder."},
    },
    "connection.gcloud_play": {
        "en": {"format": "Choose one option: ready, deferred, or not_needed.", "example": "ready", "why": "Records whether Google Cloud and Play read-only discovery can run for Android work."},
        "tr": {"format": "Bir seçenek seçin: ready, deferred veya not_needed.", "example": "ready", "why": "Android işi için Google Cloud ve Play salt okunur keşfinin çalışıp çalışamayacağını kaydeder."},
    },
    "app.name": {
        "en": {"format": "Short display name: letters, digits, and spaces.", "example": "Example App", "why": "The saved plan uses this name so later store records and evidence name the correct product."},
        "tr": {"format": "Kısa görünen ad: harf, rakam ve boşluk.", "example": "Example App", "why": "Kaydedilen plan bu adı kullanır; böylece sonraki mağaza kayıtları ve kanıtlar doğru ürünü adlandırır."},
    },
    "app.bundle_id": {
        "en": {"format": "Reverse-domain identifier: com.company.product, lowercase.", "example": "com.example.app", "why": "Reverse domain makes the iOS app record unique; keep the same prefix as your developer account domain and never change it later."},
        "tr": {"format": "Ters alan adı biçiminde kimlik: com.sirket.urun, küçük harf.", "example": "com.example.app", "why": "Ters alan adı iOS uygulama kaydını benzersiz yapar; geliştirici hesabı alan adınızla aynı öneki kullanın ve sonradan değiştirmeyin."},
    },
    "app.package_name": {
        "en": {"format": "Reverse-domain identifier: com.company.product, lowercase.", "example": "com.example.app", "why": "Must match the Android application ID used by builds, Firebase, and Google Play; changing it later breaks references."},
        "tr": {"format": "Ters alan adı biçiminde kimlik: com.sirket.urun, küçük harf.", "example": "com.example.app", "why": "Derlemelerin, Firebase'in ve Google Play'in kullandığı Android uygulama kimliğiyle aynı olmalıdır; sonradan değiştirmek bağlantıları bozar."},
    },
    "support.email": {
        "en": {"format": "A monitored public email address.", "example": "support@example.com", "why": "Stores may publish this address as the customer support contact in the listing."},
        "tr": {"format": "Takip edilen, herkese açık bir e-posta adresi.", "example": "support@example.com", "why": "Mağazalar bu adresi listede müşteri desteği iletişimi olarak yayınlayabilir."},
    },
    "review.first_name": {
        "en": {"format": "Given name only, one word.", "example": "Ada", "why": "Stores contact this person when review is blocked; enter a plain name, never a password or key."},
        "tr": {"format": "Yalnızca ad, tek kelime.", "example": "Ada", "why": "İnceleme engellendiğinde mağazalar bu kişiyle iletişim kurar; düz bir ad girin, şifre veya anahtar girmeyin."},
    },
    "review.last_name": {
        "en": {"format": "Family name only, one word.", "example": "Lovelace", "why": "Completes the accountable review contact identity for store records."},
        "tr": {"format": "Yalnızca soyad, tek kelime.", "example": "Lovelace", "why": "Mağaza kayıtları için sorumlu inceleme kişisinin kimliğini tamamlar."},
    },
    "review.email": {
        "en": {"format": "A monitored private email address.", "example": "review@example.com", "why": "Store review teams send questions here; use a mailbox someone actually checks."},
        "tr": {"format": "Takip edilen, özel bir e-posta adresi.", "example": "review@example.com", "why": "Mağaza inceleme ekipleri sorularını buraya gönderir; gerçekten takip edilen bir adres kullanın."},
    },
    "review.phone": {
        "en": {"format": "International format with country code; digits only after the plus sign.", "example": "+15551234567", "why": "Apple requires a reachable number for urgent review contact."},
        "tr": {"format": "Ülke koduyla uluslararası biçim; artı işaretinden sonra yalnızca rakam.", "example": "+15551234567", "why": "Apple acil inceleme iletişimi için ulaşılabilir bir numara ister."},
    },
    "review.demo_access_required": {
        "en": {"format": "Choose one option: yes, no, or manual.", "example": "no", "why": "Tells reviewers how they reach the app; credentials are never entered here."},
        "tr": {"format": "Bir seçenek seçin: yes, no veya manual.", "example": "no", "why": "İnceleyicilerin uygulamaya nasıl erişeceğini belirtir; kimlik bilgileri buraya girilmez."},
    },
    "listing.primary_locale": {
        "en": {"format": "One canonical App Store Connect locale code.", "example": "tr", "why": "Fallback source locale when localized metadata is missing; use tr, never tr-TR."},
        "tr": {"format": "Tek bir kanonik App Store Connect dil kodu.", "example": "tr", "why": "Yerelleştirilmiş meta veri olmadığında kaynak dil olarak kullanılır; tr kullanın, tr-TR değil."},
    },
    "listing.locales": {
        "en": {"format": "Comma-separated canonical App Store Connect locale codes.", "example": "tr,en-US", "why": "Each listed locale needs complete, reviewed metadata before submission; tr is the canonical Turkish code, not tr-TR."},
        "tr": {"format": "Virgülle ayrılmış kanonik App Store Connect dil kodları.", "example": "tr,en-US", "why": "Listelenen her dil için gönderimden önce eksiksiz ve incelenmiş meta veri gerekir; Türkçe için kanonik kod tr'dir, tr-TR değildir."},
    },
    "listing.territories": {
        "en": {"format": "Comma-separated uppercase ISO country codes.", "example": "TR,US", "why": "Limits the countries or regions where pricing and availability are planned."},
        "tr": {"format": "Virgülle ayrılmış, büyük harfli ISO ülke kodları.", "example": "TR,US", "why": "Fiyatlandırma ve kullanılabilirliğin planlanacağı ülke veya bölgeleri sınırlar."},
    },
    "pricing.app": {
        "en": {"format": "free or amount|currency|baseTerritory on one line.", "example": "free or 4.99|USD|US", "why": "free means no price; the pipe form records the intended base price with uppercase currency and territory codes."},
        "tr": {"format": "free veya tutar|paraBirimi|bölge tek satırda.", "example": "free veya 4.99|USD|US", "why": "free ücretsiz demektir; dikey çizgili biçim, büyük harfli para birimi ve bölge koduyla amaçlanan temel fiyatı kaydeder."},
    },
    "pricing.iaps": {
        "en": {"format": "Semicolon-separated productId|type|amount|currency|baseTerritory rows; [] means no in-app purchases.", "example": "com.example.app.premium|non_consumable|4.99|USD|US", "why": "One row per product so store and RevenueCat records can be reconciled; type must be one of the listed product types."},
        "tr": {"format": "Noktalı virgülle ayrılmış productId|type|tutar|paraBirimi|bölge satırları; [] uygulama içi satın alma yok demektir.", "example": "com.example.app.premium|non_consumable|4.99|USD|US", "why": "Mağaza ve RevenueCat kayıtlarının karşılaştırılabilmesi için her ürüne bir satır; type listedeki ürün türlerinden biri olmalıdır."},
    },
    "distribution.release_mode": {
        "en": {"format": "Choose one option: manual, automatic, or phased.", "example": "manual", "why": "Controls how an approved version becomes available after store approval."},
        "tr": {"format": "Bir seçenek seçin: manual, automatic veya phased.", "example": "manual", "why": "Onaylanan sürümün mağaza onayından sonra nasıl kullanıma açılacağını belirler."},
    },
    "screenshots.device_families": {
        "en": {"format": "Choose one option: iphone, ipad, or both in either order.", "example": "iphone,ipad", "why": "Sets which Apple device families need compliant screenshot sets before submission."},
        "tr": {"format": "Bir seçenek seçin: iphone, ipad veya her ikisi.", "example": "iphone,ipad", "why": "Gönderimden önce hangi Apple cihaz aileleri için uyumlu ekran görüntüsü setleri gerektiğini belirler."},
    },
    "privacy.readiness": {
        "en": {"format": "Choose one option: ready, pending, or manual.", "example": "ready", "why": "Records whether data-use declarations are reviewable now or remain a submission blocker."},
        "tr": {"format": "Bir seçenek seçin: ready, pending veya manual.", "example": "ready", "why": "Veri kullanımı beyanlarının şimdi incelenebilir olup olmadığını ya da gönderim engeli olarak kalacağını kaydeder."},
    },
    "distribution.build_policy": {
        "en": {"format": "Choose one option; specific_build and manual require a later human step.", "example": "latest_testflight", "why": "Defines which inspected build may be proposed for TestFlight or submission and avoids accidental latest-build selection."},
        "tr": {"format": "Bir seçenek seçin; specific_build ve manual sonradan insan adımı gerektirir.", "example": "latest_testflight", "why": "TestFlight veya gönderim için hangi incelenmiş derlemenin önerilebileceğini belirler ve yanlışlıkla en son derlemenin seçilmesini önler."},
    },
}
_AUTHORIZATION_GUIDANCE = {
    "firebase.create_deploy": ("creating or deploying Firebase resources", "Firebase kaynağı oluşturmayı veya dağıtmayı"),
    "app_store.records_metadata": ("creating or changing App Store records and metadata", "App Store kayıtları ve meta verilerini oluşturmayı veya değiştirmeyi"),
    "iap.catalog": ("creating or changing in-app purchase products", "uygulama içi satın alma ürünleri oluşturmayı veya değiştirmeyi"),
    "pricing.availability": ("changing store price or territory availability", "mağaza fiyatını veya bölgesel kullanılabilirliği değiştirmeyi"),
    "revenuecat.config": ("changing RevenueCat products, entitlements, or offerings", "RevenueCat ürün, yetki veya tekliflerini değiştirmeyi"),
    "signing.assets": ("changing certificates, profiles, or signing configuration", "sertifika, profil veya imzalama yapılandırmasını değiştirmeyi"),
    "screenshots.upload_replace": ("uploading or replacing store screenshots", "mağaza ekran görüntülerini yüklemeyi veya değiştirmeyi"),
    "build.upload": ("uploading an inspected binary to a store", "incelenmiş bir uygulama dosyasını mağazaya yüklemeyi"),
    "testflight.distribution": ("assigning a build to TestFlight testers", "bir derlemeyi TestFlight test kullanıcılarına atamayı"),
    "review.submission": ("submitting a prepared version for store review", "hazırlanmış bir sürümü mağaza incelemesine göndermeyi"),
    "public_release": ("making an approved version public", "onaylı bir sürümü herkese açmayı"),
}
for _key, _scope in AUTHORIZATION_SCOPES.items():
    _action_en, _action_tr = _AUTHORIZATION_GUIDANCE[_scope]
    FIELD_GUIDANCE[_key] = {
        "en": {"format": "Choose one option; defaults to no.", "example": "no", "why": f"Records whether a future plan may propose {_action_en}; every real mutation still needs its own exact single-use approval."},
        "tr": {"format": "Bir seçenek seçin; varsayılanı no.", "example": "no", "why": f"Gelecekteki bir planın {_action_tr} önerip öneremeyeceğini kaydeder; her gerçek değişiklik yine kendi kesin tek kullanımlık onayını gerektirir."},
    }
ONBOARDING_FIELDS = {key: descriptor[2] for key, descriptor in FIELD_DESCRIPTORS.items()}
ONBOARDING_ORDER = list(FIELD_DESCRIPTORS)
READINESS_VALUES = {"ready", "deferred", "not_needed"}
ONBOARDING = ".mobile-app-ship-decisions.json"
EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
LOCALE_RE = re.compile(r"[a-z]{2}(?:-(?:[A-Z]{2}|[A-Z][a-z]{3}))?")
NONCANONICAL_APPLE_LOCALES = {"tr-TR", "it-IT", "ja-JP", "ko-KR", "ru-RU", "hi-IN", "pl-PL", "uk-UA", "id-ID", "vi-VN", "th-TH"}
IAP_TYPES = {"consumable", "non_consumable", "auto_renewable_subscription", "non_renewing_subscription"}
SECRET_PREFIX = r"-----BEGIN|\b(?:sk_(?:live|test)_|AIza|gh[pousr]_|xox[baprs]-)[A-Za-z0-9_-]+|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
SECRET_KEY = r"password|passwd|token|access[_-]?token|refresh[_-]?token|id[_-]?token|oauth[_-]?token|api[_-]?key|client[_-]?secret|session[_-]?secret|private[_-]?key"
SECRET_LABEL = rf"(?i:\b(?:{SECRET_KEY})\b\s*[\"']?\s*[:=])"
SECRET_AUTH_HEADER = r"(?i:\bauthorization\b\s*[\"']?\s*[:=]\s*(?:bearer|basic)\b)"
SECRET_KEY_RE = re.compile(rf"(?i)^(?:{SECRET_KEY}|authorization)$")
# Input rejection at onboarding/trust boundaries only needs the label to be present.
SECRET_RE = re.compile(SECRET_PREFIX + "|" + SECRET_LABEL + "|" + SECRET_AUTH_HEADER)
SECRET_PEM_RE = re.compile(r"-----BEGIN[^\r\n]*-----.*?(?:-----END[^\r\n]*-----|$)", re.DOTALL)
# Report masking extends credential assignments through a delimiter or line end.
SECRET_VALUE_RE = re.compile(
    SECRET_PREFIX + "|(?:" + SECRET_LABEL + "|" + SECRET_AUTH_HEADER + ")"
    + r"\s*(?:\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|[^,;}\]\r\n]*)"
)


def run_capture(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=5, check=False, env=env)
        output = " ".join((result.stdout + result.stderr).strip().splitlines())
        return result.returncode, output[:500] or "unavailable"
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, str(exc)[:500]


def brew_prefix(formula: str) -> Path | None:
    brew = shutil.which("brew")
    if not brew:
        return None
    code, output = run_capture([brew, "--prefix", formula])
    return Path(output) if code == 0 and output.startswith("/") else None


def tool_candidates(tool: dict) -> list[Path]:
    candidates: list[Path] = []
    formula = {"node": "node@24", "java": "openjdk@17"}.get(tool["id"])
    if formula:
        prefix = brew_prefix(formula)
        if prefix:
            candidates.append(prefix / "bin" / tool["command"])
        candidates.extend(Path(root) / "opt" / formula / "bin" / tool["command"] for root in ("/opt/homebrew", "/usr/local"))
    generic = shutil.which(tool["command"])
    if generic:
        candidates.append(Path(generic))
    return list(dict.fromkeys(path for path in candidates if path.is_file() and os.access(path, os.X_OK)))


def version_probe(tool: dict, executable: Path) -> tuple[int, str]:
    flag = "-version" if tool["command"] == "xcodebuild" else "--version"
    return run_capture([str(executable), flag])


def resolve_tool(tool: dict) -> tuple[Path | None, str | None, str | None]:
    """Return an exact tested executable, its output, and any generic-PATH problem."""
    expected = tool["testedVersion"]
    generic = shutil.which(tool["command"])
    generic_detail = None
    if generic:
        code, output = version_probe(tool, Path(generic))
        if code or expected not in output:
            generic_detail = f"PATH resolves {generic}: {output}"
    else:
        generic_detail = f"{tool['command']} is not on PATH"
    drift: tuple[Path, str] | None = None
    for candidate in tool_candidates(tool):
        code, output = version_probe(tool, candidate)
        if code == 0 and expected in output:
            return candidate, output, generic_detail
        if drift is None:
            drift = candidate, output
    return (drift[0], drift[1], generic_detail) if drift else (None, None, generic_detail)


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def target_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def android_sdk_root() -> Path:
    configured = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    return Path(configured).expanduser() if configured else Path.home() / "Library/Android/sdk"


def android_cmdline_source() -> Path | None:
    executable = shutil.which("sdkmanager")
    if not executable:
        return None
    resolved = Path(executable).resolve()
    source = resolved.parent.parent
    return source if source.name == "latest" and (source / "bin/sdkmanager").is_file() else None


def android_cmdline_check() -> dict:
    destination = android_sdk_root() / "cmdline-tools/latest"
    if (destination / "bin/sdkmanager").is_file():
        return status("PASS", f"Flutter SDK command-line tools: {destination}")
    source = android_cmdline_source()
    detail = f"missing {destination}; installed source: {source}" if source else f"missing {destination} and no installed sdkmanager source"
    return status("GAP", detail)


def install_android_cmdline() -> dict:
    check = android_cmdline_check()
    if check["status"] == "PASS":
        return check
    source = android_cmdline_source()
    destination = android_sdk_root() / "cmdline-tools/latest"
    if not source:
        return status("GAP", "install android-commandlinetools before copying it into the Flutter Android SDK")
    if destination.exists() or destination.is_symlink():
        return status("GAP", f"refusing to replace existing {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    readback = android_cmdline_check()
    return readback if readback["status"] == "PASS" else status("GAP", f"copy read-back failed: {destination}")


def status(label: str, value: str) -> dict:
    return {"status": label, "detail": value}


def in_scope(tool: dict, selected: str) -> bool:
    return "shared" in tool["platforms"] or selected == "both" or selected in tool["platforms"]


def required_for_target(tool: dict, target: Path | None, selected: str) -> bool:
    """Whether a required tool is relevant to this target; None preserves direct checks."""
    if target is None:
        return True
    if tool["id"] == "node":
        return any((target / name).exists() for name in ("firebase.json", ".firebaserc", "package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml"))
    if tool["id"] == "pod":
        return any((target / "ios" / name).exists() for name in ("Podfile", "Podfile.lock"))
    return True


def tool_check(tool: dict, selected: str, target: Path | None = None) -> dict:
    if not in_scope(tool, selected):
        return status("DEFER", f"out of {selected} scope; owner {tool['ownerDomain']}")
    required = tool["requirement"] == "required"
    if required and not required_for_target(tool, target, selected):
        signals = "Firebase/Node project signal" if tool["id"] == "node" else "ios/Podfile or ios/Podfile.lock"
        return status("DEFER", f"not required for this target: no {signals}; owner {tool['ownerDomain']}")
    if tool.get("macosOnly") and platform.system() != "Darwin":
        label = "GAP" if required else "DEFER"
        return status(label, f"{tool['ownerDomain']} manual macOS requirement; expected {tool['testedVersion']}")
    path, found, path_problem = resolve_tool(tool)
    exact = bool(path and found and tool["testedVersion"] in found)
    if exact:
        detail = f"{path}: {found}; owner {tool['ownerDomain']}"
        if path_problem:
            detail += f"; preferred candidate works, PATH needs configuration ({path_problem})"
        return status("PASS", detail)
    label = "GAP" if required else "DEFER"
    detail = f"{path}: {found}; expected {tool['testedVersion']}" if path else f"missing; expected {tool['testedVersion']}"
    return status(label, f"{detail}; owner {tool['ownerDomain']}")


def doctor(args: argparse.Namespace) -> int:
    target = target_path(args.target)
    report = {
        "platform": {"os": platform.system(), "arch": platform.machine(), "selected": args.platform},
        "harness": args.harness,
        "target": str(target),
        "checks": {},
    }
    checks = report["checks"]
    checks["canonicalSkill"] = status("PASS" if (SKILL / "SKILL.md").is_file() else "GAP", str(SKILL / "SKILL.md"))
    harness = HARNESSES[args.harness]
    skill_destination = harness["skill"]
    checks["targetSkill"] = status("DEFER" if not skill_destination else ("PASS" if (target / skill_destination / "SKILL.md").is_file() else "GAP"), skill_destination or "no supported native skill path; use canonical skill manually")
    adapter = harness["adapter"]
    if args.harness == "windsurf":
        checks["adapter"] = status("DEFER", f"Human gate: review {ROOT / harness['template']} and manually merge to {harness['manualAdapter']}; toolkit never writes global config")
    else:
        checks["adapter"] = status("DEFER" if not adapter else ("PASS" if (target / adapter).exists() else "GAP"), adapter or "no native adapter")
    checks["target"] = status("PASS" if target.is_dir() else "GAP", "target directory")
    manifest = load_manifest()
    for tool in manifest["tools"]:
        checks[tool["id"]] = tool_check(tool, args.platform, target)
    if args.platform in {"android", "both"}:
        checks["androidSdkCmdline"] = android_cmdline_check()
    for tool_id in ("node", "java"):
        tool = next(item for item in manifest["tools"] if item["id"] == tool_id)
        if not in_scope(tool, args.platform):
            continue
        check = checks[tool_id]
        if check["status"] == "PASS" and "PATH needs configuration" in check["detail"]:
            required = tool["requirement"] == "required"
            checks[f"{tool_id}Environment"] = status("GAP" if required else "DEFER", f"operational commands may not inherit the tested {tool_id}; configure PATH/JAVA_HOME manually, without profile edits by toolkit")
    status_file, progress_file = target / "STATUS.json", target / "PROGRESS.md"
    checks["state"] = status("GAP" if status_file.exists() and progress_file.exists() else "PASS", "STATUS.json and PROGRESS.md conflict" if status_file.exists() and progress_file.exists() else "single/no state file")
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"doctor: {args.harness} -> {target} ({args.platform})")
        for name, check in checks.items():
            print(f"{check['status']}: {name}: {check['detail']}")
    return 1 if any(item["status"] == "GAP" for item in checks.values()) else 0


def approved(args: argparse.Namespace, item: str) -> bool:
    if item in args.approve or f"tool:{item}" in args.approve:
        return True
    if not args.apply or not sys.stdin.isatty():
        return False
    return input(f"Approve {item}? [y/N] ").strip().lower() in {"y", "yes"}


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))


def node24_npm() -> tuple[Path, dict[str, str]] | None:
    prefix = brew_prefix("node@24")
    if not prefix:
        return None
    node, npm = prefix / "bin/node", prefix / "bin/npm"
    env = os.environ.copy()
    env["PATH"] = f"{prefix / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    node_code, node_output = run_capture([str(node), "--version"], env)
    npm_code, _ = run_capture([str(npm), "--version"], env)
    if node_code or "24." not in node_output or npm_code:
        return None
    return npm, env


def install_argv(tool: dict) -> tuple[list[str], dict[str, str] | None] | None:
    packages = {"firebase": "firebase-tools", "xcodebuildmcp": "xcodebuildmcp"}
    if tool["id"] in packages:
        resolved = node24_npm()
        if not resolved:
            return None
        npm, env = resolved
        return [str(npm), "install", "--global", f"{packages[tool['id']]}@{tool['testedVersion']}"], env
    command = tool["install"]["macos"]
    return None if command.startswith("Install ") else (shlex.split(command), None)


def bootstrap(args: argparse.Namespace) -> int:
    target, harness, manifest = target_path(args.target), HARNESSES[args.harness], load_manifest()
    approved_names = {tool["id"] for tool in manifest["tools"]} | {"android-sdk-cmdline", "skill", "adapter", "gemini-context"}
    unknown_approvals = sorted({value.removeprefix("tool:") for value in args.approve if value.removeprefix("tool:") not in approved_names})
    if unknown_approvals:
        print(f"GAP: unknown bootstrap approval name(s): {', '.join(unknown_approvals)}", file=sys.stderr)
        return 2
    print(f"bootstrap plan: {args.harness} -> {target} ({args.platform})")
    checks: dict[str, dict] = {}
    for tool in manifest["tools"]:
        check = tool_check(tool, args.platform, target)
        checks[tool["id"]] = check
        if check["status"] == "PASS":
            print(f"PASS: tool:{tool['id']}: {check['detail']}")
        elif in_scope(tool, args.platform):
            print(f"{check['status']}: tool:{tool['id']}: {check['detail']}; proposal: {tool['install']['macos']}")
    skill_dest = target / harness["skill"] if harness["skill"] else None
    adapter_dest = target / harness["adapter"] if harness["adapter"] else None
    print("DEFER: skill" if skill_dest else "DEFER: skill: no supported native skill path; use the canonical repository skill manually")
    if args.harness == "windsurf":
        print(f"DEFER: adapter: Human gate: review {ROOT / harness['template']} and manually merge to {harness['manualAdapter']}; toolkit never writes it")
    else:
        print("DEFER: adapter" if adapter_dest else "DEFER: adapter: no native adapter")
    if args.platform in {"android", "both"}:
        cmdline = android_cmdline_check()
        print(f"{cmdline['status']}: android-sdk-cmdline: {cmdline['detail']}; approve android-sdk-cmdline to copy command-line tools into the Flutter SDK without replacing existing files")
    if not args.apply:
        print("dry-run: no writes")
        return 0
    if not target.is_dir():
        print("GAP: target directory does not exist", file=sys.stderr)
        return 2
    for tool in manifest["tools"]:
        if not approved(args, tool["id"]):
            continue
        if not in_scope(tool, args.platform):
            print(f"DEFER: tool:{tool['id']}: outside approved platform scope")
            continue
        if checks[tool["id"]]["status"] == "PASS":
            print(f"PASS: tool:{tool['id']}: exact tested version already installed; no install run")
            continue
        if platform.system() != "Darwin":
            print(f"DEFER: tool:{tool['id']}: manual install required off macOS")
            continue
        invocation = install_argv(tool)
        if invocation is None:
            reason = "supported Homebrew Node 24 npm unavailable; refusing npm install" if tool["id"] in {"firebase", "xcodebuildmcp"} else tool["install"]["macos"]
            print(f"DEFER: tool:{tool['id']}: {reason}")
            continue
        argv, env = invocation
        print(f"APPLY: tool:{tool['id']}: {shlex.join(argv)}")
        result = subprocess.run(argv, check=False, env=env)
        readback = tool_check(tool, args.platform, target)
        label = "PASS" if result.returncode == 0 and readback["status"] == "PASS" else "GAP"
        print(f"{label}: tool:{tool['id']}: install exit {result.returncode}; readback: {readback['detail']}")
        if tool["id"] == "node" and label == "PASS":
            print("DEFER: select/link Node 24 yourself; bootstrap never edits shell profiles.")
    if args.platform in {"android", "both"} and approved(args, "android-sdk-cmdline"):
        installed = install_android_cmdline()
        print(f"{installed['status']}: android-sdk-cmdline: {installed['detail']}")
    if args.harness == "gemini-cli":
        print("DEFER: Gemini has no supported native skill target; no GEMINI.md fallback is written")
    elif skill_dest and approved(args, "skill"):
        if skill_dest.exists():
            print(f"GAP: refusing overwrite {skill_dest}; manual merge/copy path: {SKILL}")
        else:
            skill_dest.parent.mkdir(parents=True, exist_ok=True)
            copy_tree(SKILL, skill_dest)
            print(f"PASS: copied skill to {skill_dest}")
    if adapter_dest and approved(args, "adapter"):
        template = ROOT / harness["template"]
        if adapter_dest.exists():
            print(f"GAP: refusing overwrite/merge {adapter_dest}; manual merge path: {template}")
        else:
            adapter_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template, adapter_dest)
            print(f"PASS: copied adapter to {adapter_dest}")
    return 0


def safe_text(value: str, field: str, required: bool = False) -> str:
    value = value.strip()
    if required and not value:
        raise ValueError(f"{field} is required")
    if len(value) > 500 or "\n" in value or "\r" in value or SECRET_RE.search(value):
        raise ValueError(f"{field} must be short, single-line, sanitized text; never provide secrets")
    return value


def load_progress(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schemaVersion", "steps"} or data["schemaVersion"] != "1.0.0" or not isinstance(data["steps"], list):
        raise ValueError("onboarding progress top-level shape")
    valid_ids = {name for name, _ in AUTH_SEQUENCE}
    for item in data["steps"]:
        if not isinstance(item, dict) or set(item) != {"id", "outcome", "claim", "evidenceId", "limitation"}:
            raise ValueError("onboarding progress step shape")
        if item["id"] not in valid_ids or item["outcome"] not in {"verified", "deferred", "not_needed"} or not all(isinstance(value, str) for value in item.values()):
            raise ValueError("onboarding progress step values")
        safe_text(item["claim"], "claim", item["outcome"] == "verified")
        evidence = safe_text(item["evidenceId"], "evidence ID", item["outcome"] == "verified")
        if evidence and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", evidence):
            raise ValueError("evidence ID format")
        safe_text(item["limitation"], "limitation", item["outcome"] in {"deferred", "not_needed"})
    ids = [item["id"] for item in data["steps"]]
    sequence_ids = [name for name, _ in AUTH_SEQUENCE]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate onboarding progress step")
    if ids != sequence_ids[:len(ids)] or any(item["outcome"] == "deferred" for item in data["steps"][:-1]):
        raise ValueError("onboarding progress must be an ordered verified prefix with at most one resumable deferred step")
    return data["steps"]


def atomic_progress(path: Path, steps: list[dict[str, str]]) -> None:
    payload = json.dumps({"schemaVersion": "1.0.0", "steps": steps}, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temp = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def canonical_locale(value: str, field: str) -> str:
    if not LOCALE_RE.fullmatch(value) or value in NONCANONICAL_APPLE_LOCALES:
        raise ValueError(f"{field} must use a canonical App Store Connect locale (for example en-US or tr, not tr-TR)")
    return value


def price_object(value: object, field: str) -> dict[str, str]:
    keys = {"amount", "currency", "baseTerritory"}
    if not isinstance(value, dict) or set(value) != keys or not all(isinstance(item, str) for item in value.values()):
        raise ValueError(f"{field} must contain exactly amount, currency, and baseTerritory strings")
    amount = safe_text(value["amount"], f"{field}.amount", required=True)
    try:
        if Decimal(amount) <= 0 or not re.fullmatch(r"(?:0|[1-9]\d*)(?:\.\d{1,2})?", amount):
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field}.amount must be a positive decimal with at most two fractional digits") from None
    if not re.fullmatch(r"[A-Z]{3}", value["currency"]):
        raise ValueError(f"{field}.currency must be an uppercase ISO currency code")
    if not re.fullmatch(r"[A-Z]{2}", value["baseTerritory"]):
        raise ValueError(f"{field}.baseTerritory must be an uppercase ISO country code")
    return {"amount": amount, "currency": value["currency"], "baseTerritory": value["baseTerritory"]}


def onboarding_value(key: str, raw: object) -> object:
    if key == "pricing.app":
        value = raw
        if isinstance(raw, str):
            text = safe_text(raw, key, required=True)
            if text == "free":
                return text
            if not text.startswith("{"):
                parts = text.split("|")
                if len(parts) != 3:
                    raise ValueError(f"{key} must be free or amount|currency|baseTerritory")
                value = dict(zip(("amount", "currency", "baseTerritory"), parts))
            else:
                try:
                    value = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{key} must be free, concise pipe format, or valid JSON: {exc.msg}") from None
        return price_object(value, key)
    if key == "pricing.iaps":
        value = raw
        if isinstance(raw, str):
            text = safe_text(raw, key, required=True)
            if text == "[]":
                value = []
            elif text.startswith("["):
                try:
                    value = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{key} must be valid JSON or the concise pipe format: {exc.msg}") from None
            else:
                rows = [item.split("|") for item in text.split(";")]
                if any(len(item) != 5 for item in rows):
                    raise ValueError(f"{key} entries must be productId|type|amount|currency|baseTerritory")
                value = [dict(zip(("productId", "type", "amount", "currency", "baseTerritory"), item)) for item in rows]
        if not isinstance(value, list) or len(value) > 100:
            raise ValueError(f"{key} must contain at most 100 products")
        products, seen = [], set()
        for index, item in enumerate(value):
            if not isinstance(item, dict) or set(item) != {"productId", "type", "amount", "currency", "baseTerritory"}:
                raise ValueError(f"{key}[{index}] has unknown or missing fields")
            product_id = safe_text(item.get("productId", ""), f"{key}[{index}].productId", required=True)
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,199}", product_id) or product_id in seen:
                raise ValueError(f"{key}[{index}].productId is invalid or duplicated")
            if item.get("type") not in IAP_TYPES:
                raise ValueError(f"{key}[{index}].type is invalid")
            price = price_object({name: item.get(name) for name in ("amount", "currency", "baseTerritory")}, f"{key}[{index}]")
            products.append({"productId": product_id, "type": item["type"], **price})
            seen.add(product_id)
        return products
    if not isinstance(raw, str):
        raise ValueError(f"{key} must be a string")
    value = safe_text(raw, key, required=True)
    if key == "tooling.harness" and value not in HARNESSES:
        raise ValueError(f"{key} must name a supported harness")
    if key == "project.platforms" and value not in {"ios", "android", "both"}:
        raise ValueError(f"{key} must be ios, android, or both")
    if key.startswith("connection.") and value not in READINESS_VALUES:
        raise ValueError(f"{key} must be ready, deferred, or not_needed")
    if key in {"support.email", "review.email"} and not EMAIL_RE.fullmatch(value):
        raise ValueError(f"{key} must be a valid email address")
    if key == "review.phone" and not re.fullmatch(r"\+[1-9]\d{6,14}", value):
        raise ValueError("review.phone must use +countrycode format with 7-15 digits")
    if key == "review.demo_access_required" and value not in {"yes", "no", "manual"}:
        raise ValueError(f"{key} must be yes, no, or manual; never enter a password")
    if key == "listing.primary_locale":
        return canonical_locale(value, key)
    if key == "listing.locales":
        locales = value.split(",")
        if len(locales) != len(set(locales)):
            raise ValueError(f"{key} must not contain duplicates")
        for locale in locales:
            canonical_locale(locale, key)
    if key == "listing.territories" and not re.fullmatch(r"[A-Z]{2}(?:,[A-Z]{2})*", value):
        raise ValueError("listing.territories must be uppercase ISO country codes")
    if key == "screenshots.device_families" and value not in {"iphone", "ipad", "iphone,ipad", "ipad,iphone"}:
        raise ValueError(f"{key} must contain iphone and/or ipad without duplicates")
    if key == "distribution.release_mode" and value not in {"manual", "automatic", "phased"}:
        raise ValueError(f"{key} must be manual, automatic, or phased")
    if key == "privacy.readiness" and value not in {"ready", "pending", "manual"}:
        raise ValueError(f"{key} must be ready, pending, or manual")
    if key == "distribution.build_policy" and value not in {"latest_processed", "latest_testflight", "specific_build", "manual"}:
        raise ValueError(f"{key} has an invalid latest-build/TestFlight policy")
    if key in AUTHORIZATION_SCOPES and value not in {"yes", "no"}:
        raise ValueError(f"{key} must be yes or no")
    if key in {"app.bundle_id", "app.package_name"} and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,199}", value):
        raise ValueError(f"{key} has an unsafe identifier format")
    return value


def missing_auth_steps(data: dict, progress_path: Path) -> list[str]:
    records = load_progress(progress_path)
    completed = {item["id"] for item in records if item["outcome"] in {"verified", "not_needed"}}
    return sorted(step for key, step in AUTH_CONNECTIONS.items() if data["decisions"].get(key) == "ready" and step not in completed)


def selected_scopes(data: dict) -> list[str]:
    return sorted(scope for key, scope in AUTHORIZATION_SCOPES.items() if data["decisions"].get(key) == "yes")


def acknowledgement_digest(data: dict) -> str:
    canonical = json.dumps(data["decisions"], ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def valid_plan_acknowledgement(data: dict) -> bool:
    acknowledgement = data.get("planAcknowledgement")
    return bool(isinstance(acknowledgement, dict) and acknowledgement.get("canonicalSha256") == acknowledgement_digest(data))


def onboarding_summary(data: dict, target: Path) -> dict[str, object]:
    missing = [key for key in ONBOARDING_ORDER if key not in data["decisions"]]
    blockers = [key for key in ONBOARDING_ORDER if key.startswith("connection.") and data["decisions"].get(key) not in {"ready", "not_needed"}]
    auth_blockers = missing_auth_steps(data, target / PROGRESS) if not missing and not blockers else []
    acknowledged = valid_plan_acknowledgement(data)
    return {
        "completed": len(ONBOARDING_ORDER) - len(missing),
        "total": len(ONBOARDING_ORDER),
        "missing": missing,
        "next": missing[0] if missing else None,
        "connectionBlockers": blockers,
        "authEvidenceBlockers": auth_blockers,
        "selectedScopes": selected_scopes(data),
        "planAcknowledged": acknowledged,
        "planAcknowledgementStatus": "current" if acknowledged else "stale" if data["planAcknowledgement"] else "missing",
    }


def show_onboarding(args: argparse.Namespace, data: dict, target: Path, path: Path) -> int:
    summary = onboarding_summary(data, target)
    if args.json:
        print(json.dumps({**summary, "schemaVersion": ONBOARDING_SCHEMA_VERSION, "approvalMode": data["approvalMode"], "configPath": str(path)}, sort_keys=True))
        return 0
    lang = resolve_language(args)
    human = HUMAN[lang]
    print(human["show_header"].format(completed=summary["completed"], total=summary["total"], path=path))
    print(human["show_readonly"])
    if summary["missing"]:
        key = summary["next"]
        print(human["next_field"].format(label=field_label(lang, key), key=key))
    elif summary["connectionBlockers"]:
        print(human["connections_blocker"].format(joined=field_names(lang, summary["connectionBlockers"])))
    elif summary["authEvidenceBlockers"]:
        print(human["evidence_blocker"])
    elif not summary["planAcknowledged"]:
        print(human["unacknowledged"])
    else:
        print(human["plan_pass"])
    return 0


def load_onboarding(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": ONBOARDING_SCHEMA_VERSION, "decisions": {}, "approvalMode": "strict", "planAcknowledgement": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("onboarding top-level shape")
    if data.get("schemaVersion") == LEGACY_ONBOARDING_SCHEMA_VERSION:
        decisions = data.get("decisions")
        if not isinstance(decisions, dict):
            raise ValueError("legacy onboarding decisions")
        data = {"schemaVersion": ONBOARDING_SCHEMA_VERSION, "decisions": decisions, "approvalMode": "strict", "planAcknowledgement": None}
    expected = {"schemaVersion", "decisions", "approvalMode", "planAcknowledgement"}
    if not isinstance(data, dict) or set(data) != expected or data["schemaVersion"] != ONBOARDING_SCHEMA_VERSION:
        raise ValueError("onboarding top-level shape")
    if not isinstance(data["decisions"], dict) or data["approvalMode"] != "strict":
        raise ValueError("onboarding decisions/approval shape")
    for key, value in data["decisions"].items():
        if key not in ONBOARDING_FIELDS or onboarding_value(key, value) != value:
            raise ValueError("onboarding unknown or noncanonical decision")
    acknowledgement = data["planAcknowledgement"]
    if acknowledgement is not None:
        if not isinstance(acknowledgement, dict) or set(acknowledgement) != {"acknowledgedAt", "canonicalSha256"}:
            raise ValueError("planAcknowledgement shape")
        try:
            timestamp = datetime.fromisoformat(acknowledgement["acknowledgedAt"].replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            raise ValueError("planAcknowledgement acknowledgedAt must be UTC") from None
        if not acknowledgement["acknowledgedAt"].endswith("Z") or timestamp.utcoffset().total_seconds() != 0 or not re.fullmatch(r"[0-9a-f]{64}", acknowledgement["canonicalSha256"]):
            raise ValueError("planAcknowledgement timestamp/digest")
    return data


def atomic_json(path: Path, data: dict) -> None:
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temp = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def interactive_value(key: str, lang: str) -> object:
    descriptor = FIELD_DESCRIPTORS[key]
    description = descriptor[2] if lang == "en" else descriptor[3]
    if key != "pricing.iaps":
        return onboarding_value(key, input(f"{field_label(lang, key)}: {description}: "))
    products: list[dict[str, str]] = []
    while True:
        raw = input(HUMAN[lang]["iap_prompt"]).strip()
        if not raw:
            return onboarding_value(key, products)
        parsed = onboarding_value(key, raw)
        products = onboarding_value(key, [*products, *parsed])


def onboard(args: argparse.Namespace) -> int:
    target, path = target_path(args.target), target_path(args.target) / ONBOARDING
    lang = resolve_language(args)
    if not target.is_dir():
        print(f"{HUMAN[lang]['gap']}: {HUMAN[lang]['target_missing']}", file=sys.stderr)
        return 2
    if args.check_scope:
        print(json.dumps({"approved": False, "scope": args.check_scope if args.check_scope in AUTHORIZATION_SCOPES.values() else None, "reason": "future_intent_only"}, sort_keys=True))
        return 2
    if getattr(args, "show", False):
        try:
            data = load_onboarding(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"GAP: invalid onboarding data: {exc}", file=sys.stderr)
            return 2
        return show_onboarding(args, data, target, path)
    try:
        data, changed = load_onboarding(path), False
        for assignment in args.set:
            key, separator, value = assignment.partition("=")
            if not separator or key not in ONBOARDING_FIELDS:
                raise ValueError(f"unknown onboarding decision: {key or assignment}")
            canonical = onboarding_value(key, value)
            if data["decisions"].get(key) != canonical:
                data["decisions"][key], data["planAcknowledgement"], changed = canonical, None, True
        if args.approval_mode and args.approval_mode != "strict":
            raise ValueError("only strict approvalMode is supported")
        if args.allow_batch_category:
            raise ValueError("batch categories cannot authorize external mutations")
        if args.interactive and sys.stdin.isatty():
            for key in ONBOARDING_ORDER:
                if key not in data["decisions"]:
                    data["decisions"][key] = interactive_value(key, lang)
                    data["planAcknowledgement"], changed = None, True
                    atomic_json(path, data)
        if changed or not path.exists():
            atomic_json(path, data)
        summary = onboarding_summary(data, target)
        if getattr(args, "acknowledge_plan", False) or args.approve_plan:
            if summary["missing"]:
                raise ValueError("--acknowledge-plan requires every onboarding decision")
            if summary["connectionBlockers"]:
                raise ValueError("--acknowledge-plan requires ready/not_needed connections: " + ", ".join(summary["connectionBlockers"]))
            if summary["authEvidenceBlockers"]:
                raise ValueError("--acknowledge-plan requires verified/not_needed next-auth evidence: " + ", ".join(summary["authEvidenceBlockers"]))
            data["planAcknowledgement"] = {"acknowledgedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "canonicalSha256": acknowledgement_digest(data)}
            atomic_json(path, data)
            summary = onboarding_summary(data, target)
    except (EOFError, KeyboardInterrupt):
        print(HUMAN[lang]["paused"], file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(HUMAN[lang]["invalid_onboarding"].format(detail=exc), file=sys.stderr)
        return 2
    summary = onboarding_summary(data, target)
    plan = {"schemaVersion": ONBOARDING_SCHEMA_VERSION, "connectionBlockers": summary["connectionBlockers"], "authEvidenceBlockers": summary["authEvidenceBlockers"], "completed": summary["completed"], "total": summary["total"], "next": summary["next"], "approvalMode": "strict", "planAcknowledged": summary["planAcknowledged"], "configPath": str(path), "nextAuthCommand": f"scripts/mobile-app-ship next-auth --harness {data['decisions']['tooling.harness']} --target {target}" if "tooling.harness" in data["decisions"] else None}
    if args.json:
        print(json.dumps(plan))
    else:
        human = HUMAN[lang]
        print(human["onboard_header"].format(completed=plan["completed"], total=plan["total"], path=path))
        print(human["onboard_ack"])
        if summary["missing"]:
            key = summary["next"]
            print(human["next_field"].format(label=field_label(lang, key), key=key))
        elif summary["authEvidenceBlockers"]:
            print(human["evidence_blocker"].format(joined=", ".join(summary["authEvidenceBlockers"])))
        elif not plan["planAcknowledged"]:
            print(human["unacknowledged"])
        else:
            print(human["plan_pass"])
    return 0


WEB_GROUPS = {
    "setup": {
        "en": "Harness and platform", "tr": "Araç ortamı ve platform",
        "description": {"en": "Decides which local coding harness receives the plan and which platforms the active path covers. It does not install tools or write any adapter.", "tr": "Planı alacak yerel kodlama araç ortamını ve etkin yolun hangi platformları kapsadığını belirler. Araç kurmaz veya adaptör yazmaz."},
    },
    "connections": {
        "en": "Local readiness and connections", "tr": "Yerel hazırlık ve bağlantılar",
        "description": {"en": "Records which local tools and vendor connections are ready for later read-only verification. It never authenticates here and grants no access.", "tr": "Hangi yerel araçların ve satıcı bağlantılarının sonraki salt okunur doğrulamaya hazır olduğunu kaydeder. Burada kimlik doğrulamaz ve erişim vermez."},
    },
    "identity": {
        "en": "App and review contact", "tr": "Uygulama ve inceleme kişisi",
        "description": {"en": "Names the app and the accountable review contact that store records use. It never stores credentials, passwords, or signing material.", "tr": "Mağaza kayıtlarının kullandığı uygulamayı ve sorumlu inceleme kişisini adlandırır. Kimlik bilgisi, şifre veya imzalama materyali saklamaz."},
    },
    "listing": {
        "en": "Store listing, price, and media", "tr": "Mağaza listesi, fiyat ve medya",
        "description": {"en": "Defines store locales, sales territories, price, and screenshots that later evidence checks. It does not publish, submit, or change anything in a store.", "tr": "Mağaza dillerini, satış bölgelerini, fiyatı ve ekran görüntülerini tanımlar; sonraki kanıtlar bunları denetler. Hiçbir mağazada yayın, gönderim veya değişiklik yapmaz."},
    },
    "release": {
        "en": "Privacy and distribution", "tr": "Gizlilik ve dağıtım",
        "description": {"en": "Chooses privacy readiness and how an approved version becomes available. It does not release or distribute anything here.", "tr": "Gizlilik hazırlığını ve onaylanan sürümün nasıl kullanıma açılacağını seçer. Burada hiçbir şey yayınlamaz veya dağıtmaz."},
    },
    "authorization": {
        "en": "Future mutation intent", "tr": "Gelecek değişiklik niyeti",
        "description": {"en": "Records which future mutations a plan may propose. Selected scopes are future intent only and do not authorize any real change; each one still needs its own exact single-use approval.", "tr": "Bir planın hangi gelecek değişiklikleri önerebileceğini kaydeder. Seçilen kapsamlar yalnızca gelecek niyetidir ve hiçbir gerçek değişikliği yetkilendirmez; her biri yine kendi kesin tek kullanımlık onayını gerektirir."},
    },
}

def web_group(key: str) -> str:
    if key.startswith(("tooling.", "project.")):
        return "setup"
    if key.startswith("connection."):
        return "connections"
    if key.startswith(("app.", "support.", "review.")):
        return "identity"
    if key.startswith(("listing.", "pricing.", "screenshots.")):
        return "listing"
    if key.startswith(("distribution.", "privacy.")):
        return "release"
    return "authorization"


def localized_choice(value: str, en_label: str, tr_label: str, en_detail: str, tr_detail: str) -> dict[str, object]:
    return {"value": value, "label": {"en": en_label, "tr": tr_label}, "detail": {"en": en_detail, "tr": tr_detail}}


def web_choices(key: str) -> list[dict[str, object]] | None:
    choice = localized_choice
    options = {
        "tooling.harness": [
            choice("claude-code", "Claude Code", "Claude Code", "Targets Claude Code project instructions and its inactive adapter template.", "Claude Code proje talimatlarını ve etkin olmayan adaptör şablonunu hedefler."),
            choice("codex", "Codex CLI", "Codex CLI", "Targets Codex CLI project instructions and its inactive MCP configuration.", "Codex CLI proje talimatlarını ve etkin olmayan MCP yapılandırmasını hedefler."),
            choice("cursor", "Cursor", "Cursor", "Targets Cursor project instructions and its inactive MCP configuration.", "Cursor proje talimatlarını ve etkin olmayan MCP yapılandırmasını hedefler."),
            choice("vscode", "VS Code with GitHub Copilot", "GitHub Copilot ile VS Code", "Targets VS Code project instructions and its inactive MCP configuration.", "VS Code proje talimatlarını ve etkin olmayan MCP yapılandırmasını hedefler."),
            choice("windsurf", "Windsurf", "Windsurf", "Records Windsurf as the harness; adapter setup remains a manual user-global gate.", "Windsurf araç ortamını kaydeder; adaptör kurulumu manuel kullanıcı geneli kapı olarak kalır."),
            choice("gemini-cli", "Gemini CLI", "Gemini CLI", "Targets Gemini CLI settings without inventing a native skill location.", "Yerel beceri konumu uydurmadan Gemini CLI ayarlarını hedefler."),
            choice("pi", "Pi", "Pi", "Targets Pi project skill instructions with no MCP adapter write.", "MCP adaptörü yazmadan Pi proje beceri talimatlarını hedefler."),
        ],
        "project.platforms": [
            choice("ios", "iOS only", "Yalnızca iOS", "Excludes Android tools, identifiers, and Play work from the active path.", "Android araçlarını, kimliklerini ve Play işlerini etkin yolun dışında bırakır."),
            choice("android", "Android only", "Yalnızca Android", "Excludes Apple tools, identifiers, and App Store work from the active path.", "Apple araçlarını, kimliklerini ve App Store işlerini etkin yolun dışında bırakır."),
            choice("both", "iOS and Android", "iOS ve Android", "Plans two independent store paths with separate evidence and release gates.", "Ayrı kanıt ve yayın kapılarıyla iki bağımsız mağaza yolu planlar."),
        ],
        "review.demo_access_required": [
            choice("yes", "Demo access required", "Demo erişimi gerekli", "Plans a later secure credential handoff outside this file; never enter credentials here.", "Bu dosyanın dışında daha sonra güvenli kimlik bilgisi aktarımı planlar; bilgileri buraya girmeyin."),
            choice("no", "No demo access needed", "Demo erişimi gerekmiyor", "Records that reviewers can evaluate the app without a protected account.", "İnceleyicilerin uygulamayı korumalı hesap olmadan değerlendirebildiğini kaydeder."),
            choice("manual", "Decide with a human", "İnsanla birlikte karar ver", "Stops automated preparation until a person defines the review access path.", "Bir kişi inceleme erişim yolunu tanımlayana kadar otomatik hazırlığı durdurur."),
        ],
        "distribution.release_mode": [
            choice("manual", "Manual release", "Manuel yayın", "Keeps the approved version unavailable until a separate human-controlled release action.", "Ayrı ve insan denetimli yayın işlemine kadar onaylı sürümü kullanıma kapalı tutar."),
            choice("automatic", "Automatic after approval", "Onaydan sonra otomatik", "Plans store release after approval where supported, increasing the consequence of submission readiness.", "Desteklendiği yerde mağaza onayından sonra yayını planlar ve gönderim hazırlığının sonucunu büyütür."),
            choice("phased", "Phased release", "Aşamalı yayın", "Plans gradual availability after approval so rollout can be monitored.", "Yayının izlenebilmesi için onaydan sonra kademeli kullanılabilirlik planlar."),
        ],
        "privacy.readiness": [
            choice("ready", "Ready for review", "İncelemeye hazır", "States that data collection and privacy declarations are complete enough to inspect.", "Veri toplama ve gizlilik beyanlarının incelenebilecek kadar tamamlandığını belirtir."),
            choice("pending", "Work pending", "Çalışma bekliyor", "Keeps privacy declarations as a blocker before submission.", "Gizlilik beyanlarını gönderim öncesi engel olarak tutar."),
            choice("manual", "Human review required", "İnsan incelemesi gerekli", "Requires a person to resolve legal or policy details before submission.", "Gönderimden önce yasal veya politika ayrıntılarını bir kişinin çözmesini gerektirir."),
        ],
        "distribution.build_policy": [
            choice("latest_processed", "Latest processed build", "İşlenen en son derleme", "Proposes the newest store-processed build, which must still be inspected before use.", "Mağazada işlenen en yeni derlemeyi önerir; kullanılmadan önce yine incelenmelidir."),
            choice("latest_testflight", "Latest TestFlight build", "En son TestFlight derlemesi", "Proposes the newest TestFlight build after its identity and evidence are checked.", "Kimliği ve kanıtı denetlendikten sonra en yeni TestFlight derlemesini önerir."),
            choice("specific_build", "Specific build", "Belirli derleme", "Requires an explicit build selection later and prevents automatic newest-build choice.", "Daha sonra açık bir derleme seçimi gerektirir ve en yeni derlemenin otomatik seçimini önler."),
            choice("manual", "Human selects build", "Derlemeyi insan seçer", "Keeps build selection behind a manual gate.", "Derleme seçimini manuel kapının arkasında tutar."),
        ],
        "screenshots.device_families": [
            choice("iphone", "iPhone", "iPhone", "Requires reviewed iPhone screenshot sets only.", "Yalnızca incelenmiş iPhone ekran görüntüsü setlerini gerektirir."),
            choice("ipad", "iPad", "iPad", "Requires reviewed iPad screenshot sets only.", "Yalnızca incelenmiş iPad ekran görüntüsü setlerini gerektirir."),
            choice("iphone,ipad", "iPhone and iPad", "iPhone ve iPad", "Requires complete reviewed screenshot sets for both device families in canonical iPhone-first order.", "Her iki cihaz ailesi için kanonik iPhone öncelikli sırada eksiksiz ve incelenmiş ekran görüntüsü setleri gerektirir."),
            choice("ipad,iphone", "iPad and iPhone", "iPad ve iPhone", "Accepts the equivalent iPad-first order and still requires both reviewed screenshot sets.", "Eşdeğer iPad öncelikli sırayı kabul eder ve yine iki incelenmiş ekran görüntüsü setini gerektirir."),
        ],
    }
    if key.startswith("connection."):
        subject = FIELD_DESCRIPTORS[key]
        return [
            choice("ready", "Ready for later verification", "Sonraki doğrulamaya hazır", f"Records {subject[0].lower()} as available for later read-only verification; it grants no access or write permission.", f"{subject[1]} durumunu sonraki salt okunur doğrulama için kullanılabilir kaydeder; erişim veya yazma izni vermez."),
            choice("deferred", "Deferred and blocking", "Ertelendi ve engelliyor", f"Keeps {subject[0].lower()} as an explicit blocker to resume later.", f"{subject[1]} durumunu daha sonra sürdürülmek üzere açık bir engel olarak tutar."),
            choice("not_needed", "Not needed for this plan", "Bu plan için gerekli değil", f"Excludes {subject[0].lower()} from the active plan.", f"{subject[1]} durumunu etkin planın dışında bırakır."),
        ]
    if key in AUTHORIZATION_SCOPES:
        action_en, action_tr = FIELD_DESCRIPTORS[key][0], FIELD_DESCRIPTORS[key][1]
        return [
            choice("no", "Do not include", "Kapsama alma", f"Does not include {action_en.lower()} in future intent.", f"{action_tr.lower()} gelecekteki niyete dahil edilmez."),
            choice("yes", "Include as future intent", "Gelecek niyetine dahil et", f"Includes {action_en.lower()} as future intent only. Every external mutation still needs its own exact single-use approval.", f"{action_tr.lower()} yalnızca gelecek niyetine eklenir. Her harici değişiklik yine kendi kesin tek kullanımlık onayını gerektirir."),
        ]
    return options.get(key)


def web_embedded_choices(key: str) -> list[dict[str, object]]:
    if key != "pricing.iaps":
        return []
    choice = localized_choice
    return [
        choice("consumable", "Consumable", "Tüketilebilir", "The customer can buy this depleted item again, such as credits or hints.", "Müşteri kredi veya ipucu gibi tükenen bu ürünü yeniden satın alabilir."),
        choice("non_consumable", "Non-consumable", "Tüketilemez", "A durable one-time purchase remains restorable for the store account.", "Kalıcı tek seferlik satın alma mağaza hesabı için geri yüklenebilir kalır."),
        choice("auto_renewable_subscription", "Auto-renewable subscription", "Otomatik yenilenen abonelik", "The store renews access by billing period until the customer cancels.", "Müşteri iptal edene kadar mağaza erişimi fatura dönemine göre yeniler."),
        choice("non_renewing_subscription", "Non-renewing subscription", "Yenilenmeyen abonelik", "Access expires after the purchased period and requires a new purchase.", "Satın alınan dönemden sonra erişim sona erer ve yeni satın alma gerekir."),
    ]


def web_field_schema() -> list[dict[str, object]]:
    fields = []
    for key, descriptor in FIELD_DESCRIPTORS.items():
        choices = web_choices(key)
        fields.append({
            "key": key,
            "group": web_group(key),
            "label": {"en": descriptor[0], "tr": descriptor[1]},
            "description": {"en": descriptor[2], "tr": descriptor[3]},
            "guidance": FIELD_GUIDANCE[key],
            "kind": "select" if choices else "text",
            "choices": choices,
            "valueOptions": web_embedded_choices(key),
            "sensitive": key in {"pricing.iaps", "pricing.app", "review.demo_access_required"},
        })
    return fields


def web_value(value: object) -> str:
    if isinstance(value, dict):
        return "|".join(value[name] for name in ("amount", "currency", "baseTerritory"))
    if isinstance(value, list):
        return ";".join("|".join(item[name] for name in ("productId", "type", "amount", "currency", "baseTerritory")) for item in value) or "[]"
    return value if isinstance(value, str) else ""


def onboarding_web_state(target: Path) -> dict[str, object]:
    data = load_onboarding(target / ONBOARDING)
    decisions = {key: web_value(value) for key, value in data["decisions"].items()}
    decisions.setdefault("authorization.public_release", "no")
    summary = onboarding_summary(data, target)
    acknowledgement_command = None
    if not summary["missing"] and not summary["connectionBlockers"] and not summary["authEvidenceBlockers"] and not summary["planAcknowledged"]:
        acknowledgement_command = f"scripts/mobile-app-ship onboard --target {shlex.quote(str(target))} --acknowledge-plan"
    return {
        "schemaVersion": ONBOARDING_SCHEMA_VERSION,
        "fields": web_field_schema(),
        "groups": WEB_GROUPS,
        "decisions": decisions,
        "approvalMode": data["approvalMode"],
        "completed": summary["completed"],
        "total": summary["total"],
        "missing": summary["missing"],
        "connectionBlockers": summary["connectionBlockers"],
        "authEvidenceBlockers": summary["authEvidenceBlockers"],
        "selectedScopes": summary["selectedScopes"],
        "planAcknowledged": summary["planAcknowledged"],
        "planAcknowledgementStatus": summary["planAcknowledgementStatus"],
        "planAcknowledgementCommand": acknowledgement_command,
    }


def loopback_name(value: str | None) -> bool:
    if not value:
        return True
    host = value.strip().lower().rstrip(".")
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def local_request(handler: BaseHTTPRequestHandler) -> bool:
    host = handler.headers.get("Host", "").rsplit("@", 1)[-1]
    host = host[1:].split("]", 1)[0] if host.startswith("[") else host.rsplit(":", 1)[0]
    origin = handler.headers.get("Origin")
    origin_host = urlparse(origin).hostname if origin else None
    return bool(origin is None or origin_host is not None and loopback_name(origin_host)) and loopback_name(handler.client_address[0]) and loopback_name(host)


def create_onboarding_server(target: Path, port: int = 0) -> ThreadingHTTPServer:
    html = ONBOARDING_HTML.read_bytes()

    class OnboardingHandler(BaseHTTPRequestHandler):
        server_version = "MobileAppShipLocal/1"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def respond(self, code: int, body: object, content_type: str = "application/json; charset=utf-8") -> None:
            payload = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; connect-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Permissions-Policy", "accelerometer=(), autoplay=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()")
            self.end_headers()
            self.wfile.write(payload)

        def permitted(self) -> bool:
            if local_request(self):
                return True
            self.respond(403, {"error": "Local requests only"})
            return False

        def do_GET(self) -> None:
            if not self.permitted():
                return
            if self.path == "/":
                self.respond(200, html, "text/html; charset=utf-8")
            elif self.path == "/api/state":
                try:
                    self.respond(200, onboarding_web_state(target))
                except (OSError, json.JSONDecodeError, ValueError):
                    self.respond(500, {"error": "Saved onboarding data is invalid"})
            elif self.path == "/api/schema":
                try:
                    self.respond(200, json.loads(ONBOARDING_SCHEMA.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError):
                    self.respond(500, {"error": "Onboarding schema is unavailable"})
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if not self.permitted():
                return
            if self.path != "/api/save":
                self.respond(404, {"error": "Not found"})
                return
            if self.headers.get("Content-Type") != "application/json":
                self.respond(415, {"error": "Content type must be application/json"})
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > 65536:
                    raise ValueError
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict) or set(payload) != {"decisions"}:
                    raise ValueError
                if not isinstance(payload["decisions"], dict):
                    raise ValueError
                data = load_onboarding(target / ONBOARDING)
                decisions: dict[str, object] = {}
                for key, raw in payload["decisions"].items():
                    if key not in ONBOARDING_FIELDS:
                        raise ValueError("unknown decision")
                    decisions[key] = onboarding_value(key, raw)
                changed = decisions != data["decisions"]
                data["decisions"] = decisions
                if changed:
                    data["planAcknowledgement"] = None
                atomic_json(target / ONBOARDING, data)
                self.respond(200, {"saved": True, "state": onboarding_web_state(target)})
            except (UnicodeDecodeError, json.JSONDecodeError, OSError, ValueError):
                self.respond(400, {"error": "Invalid or secret-like onboarding value"})

    return ThreadingHTTPServer(("127.0.0.1", port), OnboardingHandler)


def onboard_web(args: argparse.Namespace) -> int:
    target = target_path(args.target)
    if not target.is_dir():
        print("GAP: target directory does not exist", file=sys.stderr)
        return 2
    try:
        server = create_onboarding_server(target, args.port)
    except OSError as exc:
        print(f"GAP: local server unavailable: {exc}", file=sys.stderr)
        return 2
    address = f"http://127.0.0.1:{server.server_port}/"
    print(f"LOCAL: onboarding UI at {address}; Ctrl-C stops it. No vendor operation is available.")
    if not args.no_open:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("LOCAL: onboarding UI stopped")
    finally:
        server.server_close()
    return 0


def next_auth(args: argparse.Namespace) -> int:
    target, progress = target_path(args.target), target_path(args.target) / PROGRESS
    try:
        records = load_progress(progress)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"GAP: invalid onboarding progress file: {progress}: {exc}", file=sys.stderr)
        return 2
    completed = {item["id"] for item in records if item["outcome"] in {"verified", "not_needed"}}
    step, instruction = next(((name, text) for name, text in AUTH_SEQUENCE if name not in completed), (None, "All onboarding steps have verified read-back evidence."))
    if not step:
        print("PASS: onboarding sequence complete")
        return 0
    print(f"NEXT {step}: {instruction}")
    print("Authentication is not write approval. Never provide secrets to this command.")
    if not args.record:
        return 0
    if not args.approve_progress:
        print("DEFER: pass --approve-progress with an explicit --outcome to write sanitized onboarding progress")
        return 0
    if not args.outcome:
        print("GAP: --outcome verified|deferred|not_needed is required; printing a step never completes it", file=sys.stderr)
        return 2
    if not target.is_dir():
        print("GAP: target directory does not exist", file=sys.stderr)
        return 2
    try:
        claim = safe_text(args.claim or "", "claim", args.outcome == "verified")
        evidence = safe_text(args.evidence_id or "", "evidence ID", args.outcome == "verified")
        limitation = safe_text(args.limitation or "", "limitation", args.outcome in {"deferred", "not_needed"})
        if evidence and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", evidence):
            raise ValueError("evidence ID must contain only letters, digits, dot, underscore, colon, or hyphen")
    except ValueError as exc:
        print(f"GAP: {exc}", file=sys.stderr)
        return 2
    record = {"id": step, "outcome": args.outcome, "claim": claim, "evidenceId": evidence, "limitation": limitation}
    records = [item for item in records if item["id"] != step] + [record]
    atomic_progress(progress, records)
    if args.outcome == "verified":
        print(f"PASS: recorded verified read-back evidence {evidence} for {step}; next invocation advances one step")
    elif args.outcome == "not_needed":
        print(f"PASS: recorded out-of-scope provider {step}; next invocation advances one step")
    else:
        print(f"DEFER: recorded limitation for {step}; step remains resumable and is not complete")
    print(f"Local progress: {progress}; keep {PROGRESS} ignored")
    return 0


VALIDATOR_SCRIPT = SKILL / "scripts/validate_playbook.py"
_VALIDATOR_MODULE: object | None = None


def status_errors(data: object) -> list[str]:
    global _VALIDATOR_MODULE
    if _VALIDATOR_MODULE is None:
        spec = importlib.util.spec_from_file_location("mobile_app_ship_playbook_validator", VALIDATOR_SCRIPT)
        assert spec and spec.loader
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            _VALIDATOR_MODULE = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_VALIDATOR_MODULE)
        finally:
            sys.dont_write_bytecode = previous
    return _VALIDATOR_MODULE.status_errors(data)


def sanitize_report(value: object) -> object:
    if isinstance(value, str):
        masked = SECRET_PEM_RE.sub("[redacted]", value)
        return SECRET_VALUE_RE.sub("[redacted]", masked)
    if isinstance(value, list):
        return [sanitize_report(item) for item in value]
    if isinstance(value, dict):
        return {
            key: "[redacted]" if isinstance(key, str) and SECRET_KEY_RE.fullmatch(key) else sanitize_report(item)
            for key, item in value.items()
        }
    return value


def resolve_language(args: argparse.Namespace) -> str:
    """Human-output language: explicit --language tr|en > MOBILE_APP_SHIP_LANGUAGE > auto.

    `auto` reads only LC_ALL/LC_MESSAGES/LANG and can never infer conversational
    language, so agents must pass --language explicitly when invoking human output.
    JSON output is never localized and never consults this function.
    """
    explicit = getattr(args, "language", None)
    if explicit in {"tr", "en"}:
        return explicit
    env = os.environ.get("MOBILE_APP_SHIP_LANGUAGE", "").strip().lower()
    if env in {"tr", "en"}:
        return env
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "").strip().lower()
        if value.startswith("tr"):
            return "tr"
        if value:
            return "en"
    return "en"


def field_label(lang: str, key: str) -> str:
    return FIELD_DESCRIPTORS[key][0 if lang == "en" else 1]


def field_names(lang: str, keys: list[str]) -> str:
    return ", ".join(field_label(lang, key) if key in FIELD_DESCRIPTORS else key for key in keys)


def platform_label(lang: str, platform: str) -> str:
    labels = {
        "en": {"ios": "iPhone", "android": "Android", "shared": "iPhone and Android"},
        "tr": {"ios": "iPhone", "android": "Android", "shared": "iPhone ve Android"},
    }
    return labels[lang].get(platform, platform)


def target_names(lang: str, targets: dict[str, object]) -> str:
    labels = {"ios": "iPhone", "android": "Android"}
    return ", ".join(labels.get(name, name) for name in targets) or ("none" if lang == "en" else "yok")


# Human-facing wording for preflight and onboard. `--language` / MOBILE_APP_SHIP_LANGUAGE
# pick the language; `--json` output never uses these strings. Raw action/gate/evidence IDs
# and internal state identifiers stay in JSON only.
HUMAN: dict[str, dict[str, str]] = {
    "en": {
        "gap": "Needs attention",
        "pass": "Done",
        "preflight_header": "Checking the app status: {target}",
        "preflight_readonly": "I am only checking; nothing will be changed.",
        "preflight_pass": "Check complete. Nothing was changed.",
        "unset": "not provided",
        "none": "none",
        "app_line": "App: {name}",
        "targets_line": "Platforms: {joined}",
        "counts_line": "Summary: {actions} recorded steps and {evidence} check results found.",
        "next_read_back_before_retry": "Next: check the previous result before trying again. We will not repeat it yet.",
        "next_approval_required": "Next: your approval is needed before the next change.",
        "next_resume_action": "Next: we will continue the unfinished step.",
        "next_no_pending_action": "Next: there is nothing waiting for action.",
        "iap_not_ios_scope": "In-app purchase preparation does not apply to Android.",
        "iap_already_verified": "In-app purchase preparation is complete. I will not suggest doing the same thing again.",
        "iap_already_recorded": "In-app purchase preparation has started. I will check its result before doing anything else.",
        "iap_first_external_action_not_recorded": "The first in-app purchase step has not been recorded yet. I will not create it automatically.",
        "show_header": "Starting information: {completed}/{total} completed.",
        "show_readonly": "Check only: this does not approve or change anything.",
        "onboard_header": "Starting information: {completed}/{total} completed.",
        "onboard_ack": "This records the plan only. Every change still needs its own permission.",
        "next_field": "Next information: {label}",
        "connections_blocker": "Still needed: {joined}.",
        "evidence_blocker": "Some account and tool checks still need to be completed.",
        "unacknowledged": "The information is complete. Please confirm the plan before continuing; this does not change anything.",
        "plan_pass": "The plan is saved. Each future change will still ask for separate permission.",
        "iap_prompt": "Add a paid product (product code|product type|price|currency|country; leave blank when finished): ",
        "invalid_onboarding": "I could not read the saved starting information: {detail}",
        "target_missing": "The app folder was not found.",
        "status_missing": "the app status file is missing",
        "status_invalid": "the app status file is not readable",
        "validation_issue": "I could not confirm part of the app status: {issue}",
        "paused": "The questions were paused. Completed answers were saved for later.",
    },
    "tr": {
        "gap": "Eksik",
        "pass": "Tamam",
        "preflight_header": "Uygulamanın durumu kontrol ediliyor: {target}",
        "preflight_readonly": "Sadece kontrol yapıyorum; hiçbir şeyi değiştirmeyeceğim.",
        "preflight_pass": "Kontrol tamamlandı. Hiçbir değişiklik yapılmadı.",
        "unset": "belirtilmedi",
        "none": "yok",
        "app_line": "Uygulama: {name}",
        "targets_line": "Platformlar: {joined}",
        "counts_line": "Kısa özet: {actions} işlem kaydı ve {evidence} kontrol sonucu bulundu.",
        "next_read_back_before_retry": "Sıradaki adım: önceki işlemin sonucunu kontrol etmeliyiz. Aynı işi henüz tekrarlamayacağız.",
        "next_approval_required": "Sıradaki adım için onayınız gerekiyor.",
        "next_resume_action": "Sıradaki adım: yarım kalan işlemi sürdüreceğiz.",
        "next_no_pending_action": "Sıradaki adım: şu anda bekleyen bir iş yok.",
        "iap_not_ios_scope": "Uygulama içi satın alma hazırlığı Android için geçerli değil.",
        "iap_already_verified": "Uygulama içi satın alma hazırlığı tamamlandı. Aynı işlemi tekrar önermeyeceğim.",
        "iap_already_recorded": "Uygulama içi satın alma hazırlığı başladı. Başka bir şey yapmadan önce sonucunu kontrol edeceğim.",
        "iap_first_external_action_not_recorded": "İlk uygulama içi satın alma adımı henüz kaydedilmedi. Bunu kendiliğimden oluşturmayacağım.",
        "show_header": "Başlangıç bilgileri: {completed}/{total} tamamlandı.",
        "show_readonly": "Sadece kontrol: hiçbir şeyi onaylamaz veya değiştirmez.",
        "onboard_header": "Başlangıç bilgileri: {completed}/{total} tamamlandı.",
        "onboard_ack": "Bu işlem yalnızca planı kaydeder. Her değişiklik için ayrıca izin alınır.",
        "next_field": "Sıradaki bilgi: {label}",
        "connections_blocker": "Eksik kalan hazırlıklar: {joined}.",
        "evidence_blocker": "Bazı hesap ve araç kontrollerinin tamamlanması gerekiyor.",
        "unacknowledged": "Bilgiler tamamlandı. Devam etmeden önce planı onaylayın; bu işlem hiçbir şeyi değiştirmez.",
        "plan_pass": "Plan kaydedildi. Gelecekteki her değişiklik için ayrıca izin alınacak.",
        "iap_prompt": "Ücretli ürün ekleyin (ürün kodu|ürün türü|fiyat|para birimi|ülke; bitince boş bırakın): ",
        "invalid_onboarding": "Kayıtlı başlangıç bilgileri okunamadı: {detail}",
        "target_missing": "Uygulama klasörü bulunamadı.",
        "status_missing": "uygulama durum dosyası bulunamadı",
        "status_invalid": "uygulama durum dosyası okunamadı",
        "validation_issue": "Uygulama durumunun bir bölümü doğrulanamadı: {issue}",
        "paused": "Sorular duraklatıldı. Verilen cevaplar daha sonra devam etmek için kaydedildi.",
    },
}


def select_next_action(actions: list[dict], gates: list[dict], platform: str) -> dict[str, object]:
    scope = {"ios", "android", "shared"} if platform == "shared" else {platform, "shared"}
    scoped = [action for action in actions if action.get("target") in scope]
    unknown = [action["id"] for action in scoped if action.get("status") == "outcome_unknown"]
    if unknown:
        return {"state": "read_back_before_retry", "actionIds": unknown, "gateIds": [], "detail": "outcome_unknown action requires vendor read-back before any retry"}
    pending_gates = {gate["id"] for gate in gates if gate.get("state") == "pending"}
    linked = [action for action in scoped if action.get("classification") == "external_mutation" and action.get("status") in {"planned", "approved", "started"} and action.get("gateId") in pending_gates]
    if linked:
        return {"state": "approval_required", "actionIds": [action["id"] for action in linked], "gateIds": sorted(dict.fromkeys(action["gateId"] for action in linked)), "detail": "pending gate linked to planned/approved/started external mutation"}
    resumable = [action["id"] for action in scoped if action.get("status") in {"planned", "approved", "started"}]
    if resumable:
        return {"state": "resume_action", "actionIds": resumable, "gateIds": [], "detail": "planned/approved/started action remains resumable"}
    return {"state": "no_pending_action", "actionIds": [], "gateIds": [], "detail": "no pending action"}


def iap_version_status(actions: list[dict], gates: list[dict], platform: str) -> dict[str, object]:
    if platform == "android":
        return {"status": "not_ios_scope", "actionId": None, "gateId": None}
    action = next((item for item in actions if item.get("id") == "act-asc-iap-version-create"), None)
    gate = next((item for item in gates if item.get("id") == "gate-asc-iap-version-create"), None)
    if action is not None:
        if action.get("status") == "verified":
            return {"status": "already_verified", "actionId": action["id"], "gateId": action.get("gateId"), "gateState": gate.get("state") if gate else None, "detail": "first IAP version action already recorded as verified; do not propose a duplicate"}
        return {"status": "already_recorded", "actionId": action["id"], "actionStatus": action.get("status"), "gateId": action.get("gateId"), "gateState": gate.get("state") if gate else None}
    return {"status": "first_external_action_not_recorded", "actionId": None, "gateId": None, "detail": "read-only gap: first IAP version action is not recorded; preflight never creates plans or gates"}


def preflight_analysis(target: Path, platform: str) -> dict[str, object]:
    status_file = target / "STATUS.json"
    base = {"command": "preflight", "readOnly": True, "target": str(target), "platform": platform, "statusFile": str(status_file), "mutationStatement": "preflight never calls vendor tools or writes target files"}
    if not status_file.is_file():
        return {**base, "valid": False, "validationErrors": [], "error": "missing STATUS.json"}
    try:
        data = json.loads(status_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {**base, "valid": False, "validationErrors": [], "error": f"invalid STATUS.json: {exc}"}
    errors = status_errors(data)
    report = {**base, "valid": not errors, "validationErrors": errors}
    if isinstance(data, dict):
        report["app"] = data.get("app")
        targets = data.get("targets")
        report["targets"] = {name: {"state": targets.get(name, {}).get("state")} for name in ("ios", "android")} if isinstance(targets, dict) else None
        actions = data.get("actions") if isinstance(data.get("actions"), list) else []
        gates = data.get("gates") if isinstance(data.get("gates"), list) else []
        evidence = data.get("evidence") if isinstance(data.get("evidence"), list) else []
        report["counts"] = {
            "actions": len(actions),
            "evidence": len(evidence),
            "gates": len(gates),
            "gatesPending": sum(1 for gate in gates if gate.get("state") == "pending"),
            "gatesApproved": sum(1 for gate in gates if gate.get("state") == "approved"),
            "gatesConsumed": sum(1 for gate in gates if gate.get("state") == "consumed"),
            "gatesRevoked": sum(1 for gate in gates if gate.get("state") == "revoked"),
        }
        if errors:
            # Semantic validation failed: malformed records must never reach selectors
            # that assume validated keys (for example action["id"] or target state).
            report["next"] = {"state": "no_pending_action", "actionIds": [], "gateIds": [], "detail": "no usable STATUS model"}
            report["iapVersion"] = {"status": "first_external_action_not_recorded", "actionId": None, "gateId": None}
        else:
            report["next"] = select_next_action(actions, gates, platform)
            report["iapVersion"] = iap_version_status(actions, gates, platform)
    else:
        report["counts"] = {"actions": 0, "evidence": 0, "gates": 0, "gatesPending": 0, "gatesApproved": 0, "gatesConsumed": 0, "gatesRevoked": 0}
        report["next"] = {"state": "no_pending_action", "actionIds": [], "gateIds": [], "detail": "no usable STATUS model"}
        report["iapVersion"] = {"status": "first_external_action_not_recorded", "actionId": None, "gateId": None}
    return report


def status_file_for_write(target: Path) -> Path:
    path = target / "STATUS.json"
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"STATUS.json unavailable: {exc}") from None
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError("STATUS.json must be a non-symlink regular file")
    return path


@contextmanager
def status_write_lock(path: Path):
    """Serialize this toolkit's read/hash/validate/replace sequence without a target artifact."""
    if fcntl is None:
        raise OSError("STATUS writes require POSIX directory locking")
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(directory, fcntl.LOCK_UN)
        os.close(directory)


def secret_in(value: object) -> bool:
    if isinstance(value, str):
        return bool(SECRET_RE.search(value))
    if isinstance(value, list):
        return any(secret_in(item) for item in value)
    if isinstance(value, dict):
        return any((isinstance(key, str) and SECRET_KEY_RE.fullmatch(key)) or secret_in(item) for key, item in value.items())
    return False


def atomic_status(path: Path, data: dict, mode: int) -> str:
    payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temp = Path(handle.name)
            os.fchmod(handle.fileno(), stat.S_IMODE(mode))
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        try:
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
        return hashlib.sha256(path.read_bytes()).hexdigest()
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def apply_status_transaction(current: dict, transaction: object, approval_gate: str | None, consume_gate: str | None) -> dict:
    if not exact_transaction(transaction):
        raise ValueError("transaction must contain only append/update action, gate, and evidence arrays")
    assert isinstance(transaction, dict)
    if not any(transaction[group][kind] for group in ("append", "update") for kind in ("actions", "gates", "evidence")):
        raise ValueError("transaction must change at least one record")
    if approval_gate and consume_gate:
        raise ValueError("choose one transition flag")
    if secret_in(transaction):
        raise ValueError("transaction contains possible secret")
    if transaction["update"]["evidence"]:
        raise ValueError("evidence records are append-only")

    candidate = json.loads(json.dumps(current))
    original = json.loads(json.dumps(current))
    for kind in ("actions", "gates", "evidence"):
        existing = {item.get("id") for item in candidate[kind] if isinstance(item, dict)}
        append = transaction["append"][kind]
        update = transaction["update"][kind]
        ids = [item.get("id") for item in append + update if isinstance(item, dict)]
        if len(ids) != len(set(ids)) or any(not isinstance(item, str) or not item for item in ids):
            raise ValueError(f"duplicate or missing {kind} ID")
        if any(item["id"] in existing for item in append):
            raise ValueError(f"append {kind} ID already exists")
        if any(item["id"] not in existing for item in update):
            raise ValueError(f"update {kind} ID does not exist")
        positions = {item["id"]: index for index, item in enumerate(candidate[kind]) if isinstance(item, dict) and isinstance(item.get("id"), str)}
        candidate[kind].extend(append)
        for item in update:
            candidate[kind][positions[item["id"]]] = item

    # Introducing the structured scope contract is an explicit, backward-compatible upgrade.
    if current.get("schemaVersion") == "1.0.0" and any(
        isinstance(item, dict) and "scope" in item
        for group in ("append", "update")
        for kind in ("actions", "gates")
        for item in transaction[group][kind]
    ):
        candidate["schemaVersion"] = "1.1.0"

    before_gates = {item["id"]: item for item in original["gates"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    after_gates = {item["id"]: item for item in candidate["gates"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    before_actions = {item["id"]: item for item in original["actions"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    after_actions = {item["id"]: item for item in candidate["actions"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    changed_gates = [gate_id for gate_id in before_gates if before_gates[gate_id] != after_gates.get(gate_id)]
    changed_actions = [action_id for action_id in before_actions if before_actions[action_id] != after_actions.get(action_id)]

    def changed_fields(before: dict, after: dict) -> set[str]:
        return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}

    for gate_id in changed_gates:
        before, after = before_gates[gate_id], after_gates[gate_id]
        fields = changed_fields(before, after)
        legacy_scope_reapproval = (
            bool(approval_gate) and before.get("state") == "approved" and after.get("state") == "approved"
            and before.get("scope") is None and after.get("scope") is not None
        )
        if (before.get("state") in {"approved", "consumed"} and before.get("scope") != after.get("scope")
                and not legacy_scope_reapproval):
            raise ValueError("approved or consumed gate scope cannot change")
        if (gate_id == consume_gate
                or (before.get("state") == "approved" and after.get("state") == "consumed")):
            if fields - {"state"}:
                raise ValueError("consumption may change only gate state")
        elif before.get("state") == after.get("state") and fields:
            if not legacy_scope_reapproval or fields - {"scope", "approvedAt"}:
                raise ValueError("gate updates require an approval transition")
        elif before.get("state") == "pending" and after.get("state") == "approved":
            if fields - {"state", "approvedAt", "scope"}:
                raise ValueError("approval may change only gate state, timestamp, and scope")
        elif not legacy_scope_reapproval:
            raise ValueError("unsupported gate state transition")

    terminal_statuses = {"outcome_unknown", "verified", "failed"}
    for action_id in changed_actions:
        before, after = before_actions[action_id], after_actions[action_id]
        fields = changed_fields(before, after)
        old_status, new_status = before.get("status"), after.get("status")
        legacy_scope_reapproval = (
            bool(approval_gate) and old_status == "approved" and new_status == "approved"
            and before.get("scope") is None and after.get("scope") is not None
        )
        if ((consume_gate and before.get("gateId") == consume_gate)
                or (old_status, new_status) == ("approved", "started")):
            allowed = {"status"}
        elif old_status == new_status:
            if not legacy_scope_reapproval:
                raise ValueError("action updates require a status transition")
            allowed = {"scope", "verificationQuery"}
        elif (old_status, new_status) == ("planned", "approved"):
            allowed = {"status", "scope", "verificationQuery"}
        elif old_status in {"started", "outcome_unknown"} and new_status in terminal_statuses:
            allowed = {"status", "evidenceIds"}
            if not set(before.get("evidenceIds", [])).issubset(set(after.get("evidenceIds", []))):
                raise ValueError("terminal action updates may only append evidence IDs")
        else:
            raise ValueError("unsupported action status transition")
        if fields - allowed:
            raise ValueError("action identity and scope fields are immutable")

    # Approval/consumption flags authorize exactly one linked transition. Evidence may be appended alongside it.
    if approval_gate:
        if transaction["append"]["actions"] or transaction["append"]["gates"]:
            raise ValueError("approval transaction cannot append actions or gates")
        gate = before_gates.get(approval_gate)
        action = next((item for item in before_actions.values() if item.get("gateId") == approval_gate), None)
        after_gate, after_action = after_gates.get(approval_gate), after_actions.get(action["id"]) if action else None
        pending_approval = (
            gate and action and after_gate and after_action
            and gate.get("state") == "pending" and after_gate.get("state") == "approved"
            and action.get("status") == "planned" and after_action.get("status") == "approved"
        )
        legacy_scope_reapproval = (
            gate and action and after_gate and after_action
            and gate.get("state") == "approved" and after_gate.get("state") == "approved"
            and action.get("status") == "approved" and after_action.get("status") == "approved"
            and gate.get("scope") is None and action.get("scope") is None
            and after_gate.get("scope") is not None and after_action.get("scope") == after_gate.get("scope")
            and after_action.get("verificationQuery") == after_gate["scope"].get("verificationQuery")
            and isinstance(gate.get("approvedAt"), str) and isinstance(after_gate.get("approvedAt"), str)
            and after_gate["approvedAt"] > gate["approvedAt"]
        )
        if (changed_gates != [approval_gate] or not action or changed_actions != [action["id"]]
                or not (pending_approval or legacy_scope_reapproval)):
            raise ValueError("record-user-approval requires one pending gate or fresh scope approval")
    elif consume_gate:
        if transaction["append"]["actions"] or transaction["append"]["gates"]:
            raise ValueError("consume transaction cannot append actions or gates")
        gate = before_gates.get(consume_gate)
        action = next((item for item in before_actions.values() if item.get("gateId") == consume_gate), None)
        after_gate, after_action = after_gates.get(consume_gate), after_actions.get(action["id"]) if action else None
        if (not gate or not action or changed_gates != [consume_gate] or changed_actions != [action["id"]]
                or gate.get("state") != "approved" or after_gate.get("state") != "consumed"
                or action.get("status") != "approved" or after_action.get("status") != "started"):
            raise ValueError("consume-gate requires one approved gate and linked approved action")
        if action.get("classification") == "external_mutation" and ("scope" not in after_action or "scope" not in after_gate):
            raise ValueError("legacy external mutations must be structurally scoped before start")
    elif changed_gates or any(before_actions[key].get("status") != after_actions[key].get("status") for key in changed_actions if before_actions[key].get("status") not in {"started", "outcome_unknown"} or after_actions[key].get("status") not in terminal_statuses):
        raise ValueError("status transitions require the matching approval/consume flag")

    appended_gates = {item.get("id"): item for item in transaction["append"]["gates"] if isinstance(item, dict)}
    for action in transaction["append"]["actions"]:
        if action.get("classification") == "external_mutation":
            gate = appended_gates.get(action.get("gateId"))
            if (action.get("status") != "planned" or not gate or gate.get("state") != "pending"
                    or action.get("target") != gate.get("target") or "scope" not in action or "scope" not in gate):
                raise ValueError("new external mutation requires one scoped planned action and pending matching gate")
    for gate in transaction["append"]["gates"]:
        linked = next((item for item in transaction["append"]["actions"] if isinstance(item, dict) and item.get("gateId") == gate.get("id") and item.get("classification") == "external_mutation"), None)
        if linked and ("scope" not in gate or linked.get("scope") != gate.get("scope")):
            raise ValueError("new external mutation gate and action scopes must match")

    errors = status_errors(candidate)
    if errors:
        raise ValueError("invalid STATUS candidate: " + "; ".join(errors[:3]))
    return candidate


def exact_transaction(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == {"append", "update"}
            and all(isinstance(value[group], dict) and set(value[group]) == {"actions", "gates", "evidence"}
                    and all(isinstance(value[group][kind], list) for kind in ("actions", "gates", "evidence"))
                    for group in ("append", "update")))


def status_write(args: argparse.Namespace) -> int:
    try:
        target = target_path(args.target)
        path = target / "STATUS.json"
        with status_write_lock(path):
            path = status_file_for_write(target)
            mode = path.lstat().st_mode
            before = path.read_bytes()
            if hashlib.sha256(before).hexdigest() != args.expect_sha256:
                raise ValueError("STATUS.json SHA-256 precondition failed")
            raw = sys.stdin.read() if args.transaction == "-" else Path(args.transaction).read_text(encoding="utf-8")
            transaction = json.loads(raw)
            current = json.loads(before)
            if secret_in(current):
                raise ValueError("STATUS.json contains possible secret")
            current_errors = status_errors(current)
            if current_errors:
                raise ValueError("invalid current STATUS.json: " + "; ".join(current_errors[:3]))
            candidate = apply_status_transaction(current, transaction, args.record_user_approval, args.consume_gate)
            digest = atomic_status(path, candidate, mode)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"GAP: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: STATUS.json written sha256={digest}; no vendor action executed")
    return 0


def coverage_analysis(target: Path, platform: str) -> dict[str, object]:
    path = target / "STATUS.json"
    base = {"command": "coverage", "readOnly": True, "platform": platform, "matrix": {}, "scopeBinding": {}, "unknownOutcomes": 0, "validationErrors": [], "limitations": ["Responsibility counts are not readiness or percentage scores.", "Coverage never executes vendors or infers vendor state."]}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {**base, "valid": False, "schemaVersion": None, "validationErrors": ["missing or invalid STATUS.json"]}
    errors = status_errors(data)
    if not isinstance(data, dict):
        return {**base, "valid": False, "schemaVersion": None, "validationErrors": errors}
    actions, gates, evidence = data.get("actions", []), data.get("gates", []), data.get("evidence", [])
    scoped = lambda item: platform == "shared" or item.get("target") in {platform, "shared"}
    external = [item for item in actions if isinstance(item, dict) and scoped(item) and item.get("classification") == "external_mutation"]
    linked = [(item, next((gate for gate in gates if isinstance(gate, dict) and gate.get("id") == item.get("gateId")), None)) for item in external]
    structured = sum(1 for action, gate in linked if gate and action.get("scope") is not None and gate.get("scope") is not None)
    legacy = sum(1 for action, gate in linked if gate and action.get("scope") is None and gate.get("scope") is None)
    unbound = len(external) - structured - legacy
    waits = sum(1 for name in ("ios", "android") if platform == "shared" or name == platform if isinstance(data.get("targets", {}).get(name), dict) and data["targets"][name].get("state") in {"SUBMITTED", "IN_REVIEW", "ACTION_REQUIRED"})
    return {**base, "valid": not errors, "schemaVersion": data.get("schemaVersion"), "validationErrors": errors, "matrix": {"terminal_managed": {"actions": sum(1 for item in actions if isinstance(item, dict) and scoped(item) and item.get("classification") in {"inspect", "local_mutation"})}, "terminal_guided": {"externalMutations": len(external), "manualOrApprovalGates": sum(1 for item in gates if isinstance(item, dict) and scoped(item) and item.get("class") in {"approval_required", "manual_execution", "approval_and_manual"})}, "vendor_readback": {"verificationQueries": sum(1 for item in external if bool(item.get("verificationQuery", "").strip())), "storeReadbackEvidence": sum(1 for item in evidence if isinstance(item, dict) and item.get("source") == "store_readback")}, "physical_review_wait": {"humanObservationEvidence": sum(1 for item in evidence if isinstance(item, dict) and item.get("source") == "human_observation"), "waitingTargets": waits}}, "scopeBinding": {"structured": structured, "legacy": legacy, "unbound": unbound}, "unknownOutcomes": sum(1 for item in external if item.get("status") == "outcome_unknown")}


def coverage(args: argparse.Namespace) -> int:
    report = coverage_analysis(target_path(args.target), args.platform)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"Coverage: valid={report['valid']}; unknown outcomes={report['unknownOutcomes']}; no vendor action executed.")
    return 0 if report["valid"] else 2


def preflight(args: argparse.Namespace) -> int:
    report = sanitize_report(preflight_analysis(target_path(args.target), args.platform))
    if args.json:
        print(json.dumps(report, sort_keys=True))
        return 0 if report["valid"] else 2
    lang = resolve_language(args)
    human = HUMAN[lang]
    target_name = Path(str(report["target"])).name or str(report["target"])
    print(human["preflight_header"].format(target=target_name, platform=platform_label(lang, report["platform"])))
    print(human["preflight_readonly"])
    if "error" in report:
        detail = human["status_missing"] if report["error"].startswith("missing STATUS.json") else human["status_invalid"]
        print(f"{human['gap']}: {detail}")
        return 2
    app = report.get("app") or {}
    print(human["app_line"].format(name=app.get("name") or human["unset"], bundle=app.get("bundleId") or human["none"], package=app.get("packageName") or human["none"]))
    targets = report.get("targets") or {}
    print(human["targets_line"].format(joined=target_names(lang, targets)))
    counts = report["counts"]
    print(human["counts_line"].format(**counts))
    next_state = report["next"]
    print(human.get("next_" + next_state["state"], "NEXT: " + next_state["state"]))
    iap = report["iapVersion"]
    print(human.get("iap_" + iap["status"], "IAP: " + iap["status"] + (": " + iap["detail"] if iap.get("detail") else "")))
    if report["validationErrors"]:
        for issue in report["validationErrors"]:
            print(human["validation_issue"].format(issue=issue))
        return 2
    print(human["preflight_pass"])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "bootstrap", "next-auth"):
        item = sub.add_parser(name)
        item.add_argument("--harness", required=True, choices=HARNESSES)
        item.add_argument("--target", required=True)
    sub.choices["doctor"].add_argument("--platform", choices=("ios", "android", "both"), default="both")
    sub.choices["doctor"].add_argument("--json", action="store_true")
    sub.choices["bootstrap"].add_argument("--platform", choices=("ios", "android", "both"), default="both")
    sub.choices["bootstrap"].add_argument("--apply", action="store_true")
    sub.choices["bootstrap"].add_argument("--approve", action="append", default=[])
    auth = sub.choices["next-auth"]
    auth.add_argument("--record", action="store_true")
    auth.add_argument("--approve-progress", action="store_true")
    auth.add_argument("--outcome", choices=("verified", "deferred", "not_needed"))
    auth.add_argument("--claim")
    auth.add_argument("--evidence-id")
    auth.add_argument("--limitation")
    onboard_parser = sub.add_parser("onboard")
    onboard_parser.add_argument("--target", required=True)
    onboard_parser.add_argument("--set", action="append", default=[])
    onboard_parser.add_argument("--interactive", action="store_true", help="prompt for missing fields only when stdin is a TTY")
    onboard_parser.add_argument("--approval-mode", choices=("strict",))
    onboard_parser.add_argument("--allow-batch-category", action="append", default=[])
    onboard_parser.add_argument("--acknowledge-plan", action="store_true", help="record non-authorizing acknowledgement after all decisions and read-backs")
    onboard_parser.add_argument("--approve-plan", action="store_true", help="deprecated alias for --acknowledge-plan; never authorizes a mutation")
    onboard_parser.add_argument("--check-scope", metavar="SCOPE", help="deprecated compatibility check; always returns future_intent_only")
    onboard_parser.add_argument("--show", action="store_true", help="show the sanitized resumable plan/status without writing or acknowledging")
    write_parser = sub.add_parser("status-write", help="atomically record an already-authorized STATUS transaction; never executes vendors")
    write_parser.add_argument("--target", required=True)
    write_parser.add_argument("--expect-sha256", required=True)
    write_parser.add_argument("--transaction", required=True)
    write_parser.add_argument("--record-user-approval", metavar="GATE_ID")
    write_parser.add_argument("--consume-gate", metavar="GATE_ID")
    coverage_parser = sub.add_parser("coverage", help="read-only responsibility coverage report; never executes vendors")
    coverage_parser.add_argument("--target", required=True)
    coverage_parser.add_argument("--platform", choices=("ios", "android", "shared"), required=True)
    coverage_parser.add_argument("--json", action="store_true")
    coverage_parser.add_argument("--language", choices=("auto", "tr", "en"), default="auto")
    preflight_parser = sub.add_parser("preflight", help="read-only inspection of target STATUS.json and next-state selection")
    preflight_parser.add_argument("--target", required=True)
    preflight_parser.add_argument("--platform", choices=("ios", "android", "shared"), default="shared")
    preflight_parser.add_argument("--json", action="store_true")
    preflight_parser.add_argument("--language", choices=("auto", "tr", "en"), default="auto", help="human output language: auto reads LC_ALL/LC_MESSAGES/LANG; JSON output is never localized")
    onboard_parser.add_argument("--json", action="store_true")
    onboard_parser.add_argument("--language", choices=("auto", "tr", "en"), default="auto", help="human output language: auto reads LC_ALL/LC_MESSAGES/LANG; JSON output is never localized")
    web_parser = sub.add_parser("onboard-web", help="serve the local, secret-free onboarding UI")
    web_parser.add_argument("--target", required=True)
    web_parser.add_argument("--port", type=int, default=0, choices=range(0, 65536))
    web_parser.add_argument("--no-open", action="store_true")
    sub.add_parser("validate")
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor(args)
    if args.command == "bootstrap":
        return bootstrap(args)
    if args.command == "next-auth":
        return next_auth(args)
    if args.command == "onboard":
        return onboard(args)
    if args.command == "status-write":
        return status_write(args)
    if args.command == "coverage":
        return coverage(args)
    if args.command == "preflight":
        return preflight(args)
    if args.command == "onboard-web":
        return onboard_web(args)
    return subprocess.run([sys.executable, str(SKILL / "scripts/validate_playbook.py")], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
