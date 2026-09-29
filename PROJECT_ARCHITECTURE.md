# Image Utility Toolbox - Proje Mimarisi (Architecture Documentation)

## 1. Genel Bakış ve Hedefler
Image Utility Toolbox, yüksek performanslı, bağımsız (headless), modüler ve arayüzden bağımsız çalışan bir görüntü işleme motoru ile modern masaüstü stüdyo grafik arayüzüdür (GUI).
Servis odaklı mimarisi sayesinde çekirdek motor; CLI, Python API ve PyQt6 masaüstü GUI tarafından gevşek bağlı (loosely-coupled) olarak tüketilir.

## 2. Mimari Katmanlar

### 2.1 Çekirdek Katman (`src/image_toolbox/core/`)
- `context.py` (`ImageContext`):
  - PIL ve NumPy (OpenCV RGB/RGBA uint8) veri temsillerini yönetir.
  - **Lazy Synchronization:** Dönüşümler yalnızca ihtiyaç anında yapılır. Bir temsil güncellendiğinde diğeri dirty işaretlenir.
  - EXIF, ICC renk profili, kaynak format ve işlem geçmişini (history audit trail) barındırır.
  - Bellek içi byte dönüşümü (`to_bytes`) ile ara adımlarda sıfır disk I/O garantisi sunar.
- `base.py` (`BaseOperation`):
  - Command / Strategy deseni uygulayan soyut temel sınıf.
  - `validate()` ile parametre denetimi (tip ve aralık kontrolleri).
  - `apply(context: ImageContext) -> ImageContext` ile mutasyon veya yeni bağlam üretimi.
- `pipeline.py` (`PipelineEngine`):
  - Operasyonları sıralı zincirleme (fluent chaining).
  - Hook desteği (`pre_hooks`, `post_hooks` ile süre ve bellek profilleme).
  - Deklaratif JSON/YAML tarifinden (`from_recipe`) dinamik boru hattı oluşturma.
- `registry.py` (`OperationRegistry`):
  - Tüm operasyonların isim ve alias ile kaydedildiği, dinamik arama ve keşif mekanizması.
- `exceptions.py`:
  - `ToolboxError`, `ValidationError`, `OperationError`, `TargetSizeUnreachableError`, `CorruptImageError`.
- `i18n.py`:
  - Türkçe ve İngilizce çift dilli yerelleştirme yöneticisi ve dinamik dil dinleyicileri.

### 2.2 Operasyonlar Katmanı (`src/image_toolbox/operations/`)
22 adet bağımsız operasyon:
1. `resize.py`: Aspect-Ratio Preserved Resizing (fit, fill, pad, exact, scale).
2. `crop.py`: Smart & Ratio Cropping (1:1, 16:9, 4:3, 9:16, custom koordinatlar).
3. `transform.py`: Serbest döndürme, 90/180/270 derece, dikey/yatay flip, EXIF auto-orient.
4. `color_balance.py`: Kelvin cinsinden sıcaklık kaydırma (1500K-15000K) ve yeşil-macenta tint.
5. `exposure.py`: Gamma eğrisi, doğrusal parlaklık, kontrast ve EV pozlama durakları.
6. `vibrance.py`: Ten renklerini (skin-tones) koruyan akıllı doygunluk ve klasik satürasyon.
7. `sharpness.py`: Unsharp Masking ve High-Pass tabanlı clarity/keskinlik.
8. `blur.py`: Gaussian Blur, Box Blur, Motion Blur ve Tilt-Shift (minyatür odak).
9. `denoise.py`: Fast Non-Local Means ve Bilateral kenar koruyucu gürültü giderme.
10. `vignette.py`: Köşe karartma (yarıçap, yumuşaklık, opaklık, renk).
11. `watermark.py`: 9 çapa noktalı TTF metin filigranı ve şeffaf PNG logo bindirme.
12. `borders.py`: Düz çerçeve, Polaroid imza boşluklu çerçeve, alfa kanallı yuvarlak köşeler.
13. `converter.py`: PNG, JPEG, WebP, BMP, TIFF, ICO kayıplı/kayıpsız format dönüştürücü.
14. `exif_tool.py`: EXIF okuma, JSON dışa aktarma, GPS/kişisel veri temizleme veya tam silme.
15. `artistic.py`: Sepia, Vintage/Film Grain, Cyanotype, Cyberpunk/Neon renk kaydırma.
16. `edge_sketch.py`: Sobel, Canny kenar çıkarma ve kurşun kalem eskiz efekti.
17. `solarize.py`: Renk kanalı tersleme (invert) ve eşikli solarizasyon.
18. `histogram.py`: Renk uzayını bozmayan Luminance kanalı CLAHE ve histogram eşitleme.
19. `palette.py`: OpenCV K-Means ile en baskın 5 rengi yüzdeleri, RGB ve HEX ile çıkarma.
20. `threshold.py`: Otsu algoritması, adaptif Gauss ve sabit eşikleme ile binarizasyon.
21. `channels.py`: RGB/RGBA/HSV kanallarını ayrıştırma, manipüle etme ve birleştirme.
22. `compressor.py`: Hedef boyutlu akıllı sıkıştırma operasyon adaptörü.

### 2.3 Servis Katmanı (`src/image_toolbox/services/`)
- `compressor_service.py` (`TargetSizeCompressorService`):
  - Amiral gemisi akıllı sıkıştırma motoru.
  - İkili arama (Binary Search) ile 6-8 iterasyonda hedef dosya boyutuna (KB/MB) ulaşma.
  - Kademeli çözünürlük düşüşü (Fallback Lanczos downscaling) stratejisi.
  - EXIF strip desteği ve WebP / JPEG / MozJPEG uyumluluğu.
- `batch_runner.py` (`BatchProcessingRunner`):
  - Paralel işleme (`ProcessPoolExecutor` / `ThreadPoolExecutor`).
  - Hata izolasyonu (bozuk görsel tüm süreci çökertmez).
  - Klasör hiyerarşisi koruma ve olay dinleyici (progress hooks).

### 2.4 CLI Katmanı (`src/image_toolbox/cli/`)
- `typer` + `rich` tabanlı terminal arayüzü (`image-box`).
- Çift dilli (`--lang tr|en` veya sistem yereli) çıktı desteği.
- Komutlar: `compress`, `resize`, `watermark`, `inspect`, `pipeline`, `batch`, `gui`, `list-ops`.

### 2.5 Masaüstü Grafik Arayüzü (GUI) Katmanı (`src/image_toolbox/gui/`)
- `theme.py`:
  - Profesyonel Darkroom / Creative Studio nötr kömür/grafit ve çinko paleti (`#121214`, `#18181B`, `#27272A`, `#EDEDEF` ve kobalt mavi `#2563EB`/`#3B82F6` vurgusu).
  - Sıfır yapay zeka moru/laciverti ve sıfır emoji kuralı.
- `main_window.py` (`MainWindow`):
  - Menü çubuğu (Dosya, Düzen, Görünüm, Dil, Yardım) ve kısayol tuşları (`Ctrl+O`, `Ctrl+S`, `Ctrl+R`, `Ctrl+Q` vb.).
  - Güvenli dosya diyalogları (Python gettext `_` değişken çakışması önlenmiş tuple çözümleme).
  - Sol alanda dinamik yığıt: Görsel yokken `DropZoneWidget` (sürükle-bırak karşılama alanı, minimal CANVAS rozeti), görsel açıldığında `ImageViewerWidget`:
    - **Photoshop Tarzı Kanvas Gezinimi (`InteractiveCanvasScrollArea`):** `viewport()` ve görsel etiketine kurulan `eventFilter` ile orta tuş sürükleme (Middle-Click pan), `Space + Sol Tık` veya serbest sol tık pan; global koordinat tabanlı (`event.globalPosition().toPoint()`) sıfır titremeli kaydırma. Açık ve kapalı tutma el imleçleri (`OpenHandCursor`/`ClosedHandCursor`).
    - **İmleç Odaklı Yakınlaştırma:** Fare tekerleği ile imlecin baktığı piksel noktası merkez alınarak yumuşak zoom in/out (`zoom_requested(factor, center_pos)`). Çift tıklama ile ekrana sığdırma (Fit to Window).
    - **Senkronize Bölünmüş Görünüm (Split Mode):** Orijinal ve işlenmiş görsellerin yan yana karşılaştırılmasında paralel ve senkronize kaydırma/pan senkronizasyonu.
  - **Global Geri / İleri Al Motoru (Global Undo / Redo Stack):**
    - RAM tabanlı `_undo_stack` ve `_redo_stack` (30 adım geçmiş).
    - Sabitlenen her işlem (`Ctrl+Z` / `Ctrl+Y` / `Ctrl+Shift+Z` kısayolları ve Düzen menüsü eylemleriyle) geri veya ileri alınabilir.
    - Canlı önizleme halindeki uncommitted efektler geri alındığında öncelikle önizleme iptal edilir; sabitlenmiş önceki efektler (`_committed_context`) kesinlikle korunur.
  - Sağ alanda sekmeli kontrol paneli (`QTabWidget`):
    - **Sıkıştırma (CompressorTab)**: Hedef boyutlu ikili arama ve çözünürlük düşüşü, canlı tasarruf çubuğu.
    - **Ayarlar (AdjustmentsTab)**: Boyutlandırma, kırpma, 90/180/270 döndürme, ayna, 25ms gecikmeli canlı (live debounced) parlaklık/kontrast/Kelvin sıcaklık/vibrance ton kaydırıcıları, sıfırlama ve sabitleme (`commit_requested`).
    - **Efektler (EffectsTab)**: Bağlamsal parametre paneli (`QStackedWidget`). Her efekt seçildiğinde yalnızca o efekte ait parametre kontrolleri açılır (Sepia yoğunluk, Vintage gren, Cyanotype, Cyberpunk, Vinyet yarıçap/yumuşaklık/opaklık/renk, Keskinlik/Clarity, Bulanıklık modları/açı, CLAHE kontrast, Eskiz türleri, Çerçeveler). Canlı anlık önizleme, Efekti Sıfırla (aktif önizlemeyi geri alır, önceki sabitlenmiş efektleri korur) ve Efekti Sabitle (`commit_requested`) işlevleri.
    - **Filigran (WatermarkTab)**: 9 çapa noktalı metin ve şeffaf PNG logo bindirme.
    - **Analiz (AnalysisTab)**: K-Means 5 baskın renk paleti çıkarıcı (HEX kopyalama) ve EXIF inceleme/sterilizasyon.
    - **Toplu İşlem (BatchTab)**: Klasör bazlı çok iş parçacıklı paralel işleme, ilerleme çubuğu ve canlı işlem tablosu.
  - **Çift Dilli Yerelleştirme (i18n):** Menü, durum şeridi, tüm sekmeler, parametre slider etiketleri ve diyaloglar tek tıkla anında ve eksiksiz dinamik çeviri (`retranslate()`).
  - Üstte engellemesiz durum bildirim şeridi (`NotificationBadge`).
  - Altta durum çubuğu (`QStatusBar`: piksel boyutu, dosya boyutu, format, zoom yüzdesi, durum mesajı).
- `dialogs/`:
  - `about_dialog.py` (Hakkında penceresi), `shortcuts_dialog.py` (Kısayollar rehberi).

### 2.6 Android Mobil Stüdyo Katmanı (`android/`)
- **Hibrit Donanım Hızlandırmalı Mimari:**
  - Android SDK 34 (Android 14) + Gradle 8.7 + AGP 8.3.2 + Kotlin 1.9.22 tabanlı yerel kapsayıcı (`com.imagetoolbox.app`).
  - `MainActivity.kt`: Hardware-accelerated WebView, SAF (Storage Access Framework) tekli ve çoklu fotoğraf seçiciler (`ActivityResultContracts.GetContent` / `GetMultipleContents`), harici görsel paylaşım intent alıcısı (`ACTION_SEND`).
  - `WebAppInterface.kt`: JavascriptInterface köprüsü üzerinden Android MediaStore (`Pictures/ImageToolbox`), FileProvider güvenli dosya paylaşımı, sistem panosu entegrasyonu ve Toast bildirimleri.
  - `engine.js`: Masaüstü Python çekirdeği ile 100% algoritmik eşdeğerlikte çalışan saf istemci görüntü motoru: 22 operasyon, OpenCV denkliğinde K-Means 5-renk kümeleme, ikili aramalı (Binary Search) ve Lanczos çözünürlük düşüşlü (downscaling) hedef dosya boyutlu sıkıştırıcı. 256 elemanlı LUT (Lookup Table) ile 1 milisaniye mertebesinde anlık pozlama/kontrast/Kelvin renk hesaplaması.
  - `app.js` & `index.html` & `style.css`: Masaüstü Darkroom Creative Studio tasarım diliyle birebir örtüşen arayüz, 6 sekme (Sıkıştırma, Ayarlar, Efektler, Filigran, Analiz, Toplu İşlem), çoklu dokunmatik kıstırma-yakınlaştırma (pinch-to-zoom 5% - 2000%), iki parmaklı kaydırma (pan), çift dokunmayla sığdırma (fit), etkileşimli bölünmüş karşılaştırma kolu (Split View) ve durum şeridi.
  - **PC Seviyesinde Akıcı 60 FPS Canlı Önizleme Motoru:**
    - **Proxy Preview Mimarisi:** Mobil ekran viewport'u (400px) için 33 MB'lık devasa 4K ana görsel doğrudan döngüye sokulmaz; Retina netliğinde 1200px önizleme proxy'si üzerinde 60 FPS akıcılıkla canlı işleme yapılır.
    - **requestAnimationFrame Throttling:** Dokunmatik sürgü hareketlerinde `clearTimeout` gecikmesi/açlığı kaldırıldı; donanım ekran yenileme hızıyla (60Hz/120Hz) birebir senkron, sıfır takılmalı ve anında tepki veren RAF boru hattı kuruldu.
    - **Master Full-Resolution Commit:** "Sabitle" veya "Kaydet" dendiğinde tüm işlemler arka planda 4K ana görsel üzerinde tam çözünürlükle icra edilir.
  - `i18n.js`: Masaüstü sözlüğüyle tam senkron Türkçe ve İngilizce çift dilli yerelleştirme.
- **Derleme Çıktıları:**
  - `android/app/build/outputs/apk/debug/app-debug.apk` (5.6 MB bağımsız imzalı APK paketi)
  - `dist/ImageUtilityToolbox-debug.apk` (doğrudan dağıtım ve test kopyası)

### 2.7 CI/CD ve Çok Platformlu Dağıtım Katmanı (`.github/workflows/`)
- **CI Test Suite (`ci.yml`):**
  - Her `push` ve `pull_request` anında Ubuntu, Windows ve macOS üzerinde Python 3.11 & 3.12 matrix testleri.
  - Headless offscreen (`QT_QPA_PLATFORM=offscreen`) ile 57 birim/GUI testinin otomatik doğrulanması.
  - Ubuntu üzerinde Android Gradle debug derleme (`./gradlew assembleDebug`) testi.
- **Çok Platformlu Sürüm Dağıtımı (`release.yml`):**
  - Sürüm etiketleri (`v*` tag push) veya GitHub Actions sekmesinden tek tıkla manuel tetikleme (`workflow_dispatch`).
  - `launcher.py` ve `assets/` (ikon, .desktop, AppRun) altyapısı kullanılarak:
    1. **Linux (AppImage & .tar.gz):** PyInstaller derlemesi + `appimagetool` ile her dağıtımda çift tıklamayla çalışan `ImageToolbox-Linux-x86_64.AppImage` ve taşınabilir `.tar.gz`.
    2. **Windows (.zip):** PyInstaller `--onedir --windowed` ve native `assets/icon.ico` ile paketlenmiş `ImageToolbox-Windows-x64.zip`.
    3. **macOS (.zip):** PyInstaller ile oluşturulmuş `ImageToolbox.app` paketini içeren `ImageToolbox-macOS.zip`.
    4. **Android APK:** Gradle ile derlenmiş `ImageUtilityToolbox-debug.apk`.
- **GitHub Release Entegrasyonu:** `softprops/action-gh-release@v2` ile 4 platformun çıktıları derlenip otomatik sürüm notlarıyla birlikte Release olarak yayınlanır.

## 3. Test ve Doğrulama Stratejisi
- `pytest` ile 100% bağımsız sentetik veri testleri.
- `test_context.py`: Bellek sızıntısı ve kopyalama maliyeti testleri.
- `test_compressor.py`: İkili arama yakınsama ve fallback testleri.
- `test_operations.py`: 22 operasyonun girdi/çıktı sınır testleri.
- `test_batch.py`: Klasör bazlı paralel işleme ve hata izolasyonu testleri.
- `test_cli.py`: Typer komut satırı arayüzü testleri.
- `test_gui.py`: PyQt6 offscreen GUI durum, yükleme, sıkıştırma, efekt parametreleri ve canlı önizleme, kanvas pan/zoom gezinimi, orta tuş sürükleme (MiddleButton Pan), efekt sabitleme & sıfırlama izolasyonu, global Ctrl+Z/Ctrl+Y geri alma yığını, dil değişimi ve sıfırlama testleri.
- Toplam **57 test**, 0 hata ile doğrulanmıştır.
