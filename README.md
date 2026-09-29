# Image Utility Toolbox 🎨

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/PyQt6-Creative_Studio-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6 GUI" />
  <img src="https://img.shields.io/badge/Android-SDK_34_(Android_14)-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android" />
  <img src="https://img.shields.io/badge/Tests-57_Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/i18n-TR_%7C_EN-blueviolet?style=for-the-badge" alt="Localization" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>Modüler, yüksek performanslı, bellek dostu ve arayüzden bağımsız (headless) görüntü işleme motoru, modern masaüstü stüdyosu (PyQt6) ve 60 FPS canlı önizlemeli Android mobil uygulaması.</b>
  <br />
  <i>Modular, high-performance headless image processing engine, modern desktop creative studio (PyQt6), and 60 FPS real-time Android mobile application.</i>
</p>

---

## 📑 İçindekiler / Table of Contents

- [Genel Bakış / Overview](#-genel-bakış--overview)
- [Mimari Katmanlar / Architectural Pillars](#-mimari-katmanlar--architectural-pillars)
  - [1. Masaüstü Stüdyosu (PyQt6 GUI)](#1-masaüstü-stüdyosu-pyqt6-gui)
  - [2. Mobil Stüdyo (Android Native & Canvas)](#2-mobil-stüdyo-android-native--canvas)
  - [3. Çekirdek Motor ve Komut Satırı (CLI & API)](#3-çekirdek-motor-ve-komut-satırı-cli--api)
- [22 Cerrahi Operasyon / Operations Catalog](#-22-cerrahi-operasyon--operations-catalog)
- [Kurulum ve Çalıştırma / Installation & Usage](#-kurulum-ve-çalıştırma--installation--usage)
  - [Masaüstü Arayüzünü Başlatma (GUI)](#masaüstü-arayüzünü-başlatma-gui)
  - [Komut Satırı Kullanımı (CLI)](#komut-satırı-kullanımı-cli)
  - [Python SDK Kullanımı](#python-sdk-kullanımı)
  - [Android APK Derleme ve Yükleme](#android-apk-derleme-ve-yükleme)
- [Test ve Doğrulama / Testing](#-test-ve-doğrulama--testing)
- [Çift Dilli Yerelleştirme / Bilingual Localization](#-çift-dilli-yerelleştirme--bilingual-localization)
- [Lisans / License](#-lisans--license)

---

## 🌟 Genel Bakış / Overview

**Image Utility Toolbox**, profesyonel görüntü düzenleme gereksinimlerini tek bir çatı altında toplayan hibrit bir ekosistemdir.
Çekirdek görüntü işleme mantığı grafik arayüzlerden tamamen izole edilmiştir (**headless architecture**); böylece aynı operasyonlar terminalde (CLI), Python kodlarında, masaüstü Qt stüdyosunda ve Android mobil uygulamasında birebir aynı algoritmik hassasiyetle çalışır.

### Temel Prensipler
* **Sıfır Disk I/O & Lazy Synchronization:** Bellek içi `ImageContext`, PIL ve OpenCV (NumPy uint8) veri temsillerini yalnızca ihtiyaç duyulduğu an dönüştürür; boru hattındaki ara adımlar diske yazılmaz.
* **Akıllı Hedef Boyut Sıkıştırma (Target Size Compressor):** İkili Arama (**Binary Search**) ile 6-8 iterasyonda istenen dosya boyutunu (KB/MB) kalite kaybını minimize ederek yakalar. Sınırın aşıldığı durumlarda kademeli Lanczos çözünürlük düşürme fallback'i devreye girer.
* **60 FPS Canlı Önizleme:** Hem masaüstünde hem mobil ortamda kaydırıcılar (sliders) hareket ettirilirken donanım yenileme hızıyla senkronize (`requestAnimationFrame` & 256-girdili LUT) çalışır; sıfır takılma ile anlık geri bildirim sunar.
* **Darkroom Creative Studio Tasarımı:** Nötr kömür/grafit ve çinko paleti (`#121214`, `#18181B`, `#27272A`, `#EDEDEF`) ve kobalt mavi (`#2563EB`) aksanlarıyla dikkat dağıtmayan stüdyo deneyimi.

---

## 🏛️ Mimari Katmanlar / Architectural Pillars

### 1. Masaüstü Stüdyosu (PyQt6 GUI)
* **Photoshop Tarzı Kanvas Gezinimi:** Orta tuş sürükleme (Middle-Click pan), `Space + Sol Tık` veya serbest sol tık pan; global koordinat tabanlı (`event.globalPosition()`) sıfır titremeli kaydırma.
* **İmleç Odaklı Yakınlaştırma (Focal Zoom):** Fare tekerleği ile imlecin baktığı piksel noktası merkez alınarak yumuşak zoom in/out (%5 - %2000). Çift tıklama ile ekrana sığdırma (Fit to Window).
* **Bölünmüş Karşılaştırma Modu (Split View):** Orijinal ve işlenmiş görsellerin yan yana piksel düzeyinde senkron kaydırılarak karşılaştırılması.
* **RAM Tabanlı Geri/İleri Alma (Undo/Redo Stack):** `Ctrl+Z` / `Ctrl+Y` ile 30 adım geçmiş desteği; önizleme halindeki efektleri geri alırken sabitlenmiş önceki çalışmaları koruyan çift katmanlı izolasyon.
* **6 Odaklanmış Sekme:** Sıkıştırma, Ayarlar, Efektler, Filigran, Analiz ve Toplu İşlem.

### 2. Mobil Stüdyo (Android Native & Canvas)
* **Android 14 (SDK 34) & Kotlin Entegrasyonu:** `MainActivity.kt` ve `WebAppInterface.kt` üzerinden MediaStore (`Pictures/ImageToolbox`), FileProvider dosya paylaşımı ve SAF (Storage Access Framework) fotoğraf seçicileri.
* **Proxy Preview Mimarisi:** Mobil ekran viewport'u için devasa 4K görseller doğrudan ana iş parçacığına sokulmaz; 1200px Retina önizleme proxy'si üzerinde 60 FPS akıcılıkla canlı işleme yapılır. "Sabitle" veya "Kaydet" dendiğinde ana 4K master görsel tam çözünürlükle dönüştürülür.
* **256 Elemanlı LUT (Lookup Table) Hızlandırması:** Parlaklık, kontrast ve Kelvin sıcaklık dönüşümleri V8 motorunda 1 milisaniyenin altında tamamlanır.
* **Çoklu Dokunmatik Jestler:** İki parmakla kıstırma (Pinch-to-zoom), iki parmakla pan, çift dokunarak sığdırma ve dokunmatik split-handle karşılaştırması.

### 3. Çekirdek Motor ve Komut Satırı (CLI & API)
* **`image-box` Terminal Aracı:** `typer` + `rich` ile modern, renkli ve çift dilli terminal arayüzü.
* **PipelineEngine:** Operasyonları akıcı zincirleme (`.add(...)`) ve deklaratif JSON tariflerinden boru hattı kurma (`from_recipe`).
* **Hata İzolasyonlu Toplu İşlemci (Batch Runner):** `ProcessPoolExecutor` / `ThreadPoolExecutor` ile klasördeki yüzlerce görseli çökmelere karşı korumalı işleme.

---

## 🔬 22 Cerrahi Operasyon / Operations Catalog

| # | Operasyon | Modül | Açıklama |
|---|-----------|-------|----------|
| 1 | **Resize** | `resize.py` | En-boy oranını koruyarak fit, fill, pad, exact ve scale boyutlandırma. |
| 2 | **Crop** | `crop.py` | 1:1, 16:9, 4:3, 9:16 ve serbest koordinatlı akıllı kırpma. |
| 3 | **Transform** | `transform.py` | 90°/180°/270° serbest döndürme, yatay/dikey ayna, EXIF auto-orient. |
| 4 | **Color Balance** | `color_balance.py` | 1500K-15000K Kelvin renk sıcaklığı ve yeşil-macenta tint ayarı. |
| 5 | **Exposure** | `exposure.py` | Gamma eğrisi, doğrusal parlaklık, kontrast ve EV pozlama durakları. |
| 6 | **Vibrance** | `vibrance.py` | Ten renklerini koruyan akıllı doygunluk ve klasik satürasyon. |
| 7 | **Sharpness** | `sharpness.py` | Unsharp Masking ve High-Pass tabanlı berraklık/keskinlik. |
| 8 | **Blur** | `blur.py` | Gaussian Blur, Box Blur, Motion Blur ve Tilt-Shift minyatür odak. |
| 9 | **Denoise** | `denoise.py` | Fast Non-Local Means ve Bilateral kenar koruyucu gürültü giderme. |
| 10 | **Vignette** | `vignette.py` | Yarıçap, yumuşaklık, opaklık ve renk kontrollü köşe karartma. |
| 11 | **Watermark** | `watermark.py` | 9 çapa noktalı TTF metin ve şeffaf PNG logo filigran motoru. |
| 12 | **Borders** | `borders.py` | Düz çerçeve, Polaroid imza boşluklu çerçeve, alfa kanallı yuvarlak köşeler. |
| 13 | **Converter** | `converter.py` | PNG, JPEG, WebP, BMP, TIFF, ICO kayıplı/kayıpsız format dönüştürücü. |
| 14 | **EXIF Tool** | `exif_tool.py` | EXIF okuma, JSON dışa aktarma, GPS sterilizasyonu ve tam temizlik. |
| 15 | **Artistic** | `artistic.py` | Sepia, Vintage film grain, Cyanotype ve Cyberpunk neon renk dönüşümü. |
| 16 | **Edge & Sketch**| `edge_sketch.py` | Sobel, Canny kenar çıkarma ve kurşun kalem eskiz efekti. |
| 17 | **Solarize** | `solarize.py` | Renk kanalı tersleme (invert) ve eşikli solarizasyon. |
| 18 | **Histogram** | `histogram.py` | Luminance kanalı CLAHE ve histogram eşitleme. |
| 19 | **Palette** | `palette.py` | OpenCV K-Means ile en baskın 5 rengi HEX/RGB ve yüzdelerle çıkarma. |
| 20 | **Threshold** | `threshold.py` | Otsu algoritması, adaptif Gauss ve sabit binarizasyon. |
| 21 | **Channels** | `channels.py` | RGB/RGBA/HSV kanallarını ayrıştırma, manipüle etme ve birleştirme. |
| 22 | **Compressor** | `compressor.py` | İkili aramalı hedef boyutlu akıllı sıkıştırma adaptörü. |

---

## 🚀 Kurulum ve Çalıştırma / Installation & Usage

### Sistem Gereksinimleri
* **Python:** 3.11 veya üzeri
* **İşletim Sistemi:** Linux (CachyOS/Ubuntu/Fedora), macOS, Windows
* **Android (Mobil için):** Android 7.0+ (API 24+), Android SDK 34, JDK 17

### 1. Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/hakankayaci-smilegames/image-utility-toolbox.git
cd image-utility-toolbox

# Sanal ortamı oluşturun ve geliştirici modunda yükleyin
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Masaüstü Arayüzünü Başlatma (GUI)

```bash
# Bash betiği ile:
./run_gui.sh

# Veya doğrudan CLI üzerinden:
image-box gui
```

### 3. Komut Satırı Kullanımı (CLI)

```bash
# 1. Hedef dosya boyutlu akıllı sıkıştırma (350 KB WebP)
image-box compress input.jpg output.webp --target 350kb --format webp --strip-exif

# 2. En-boy oranı korumalı boyutlandırma
image-box resize input.png output.png --width 1920 --height 1080 --mode fit

# 3. Sağ alt köşeye %70 şeffaflıkla filigran ekleme
image-box watermark input.jpg output.jpg --text "© 2026 Studio" --anchor bottom-right --opacity 0.7

# 4. Baskın 5 renk paletini ve EXIF metaverilerini JSON olarak inceleme
image-box inspect photo.jpg --palette 5 --json

# 5. Klasördeki tüm fotoğrafları paralel işleme (Batch)
image-box batch ./raw_photos/ ./optimized/ recipe.json --workers 8
```

### 4. Python SDK Kullanımı

```python
from image_toolbox import ImageContext, PipelineEngine
from image_toolbox.operations import (
    ResizeOperation,
    ColorBalanceOperation,
    VignetteOperation,
    TargetSizeCompressorOperation,
)

# Görseli belleğe yükle (Sıfır disk I/O)
ctx = ImageContext.from_file("input.jpg")

# Boru hattını oluştur ve fluent zincirle
pipeline = (
    PipelineEngine()
    .add(ResizeOperation(width=1920, height=1080, mode="fit"))
    .add(ColorBalanceOperation(kelvin=6000.0))
    .add(VignetteOperation(radius=0.75, opacity=0.6))
    .add(TargetSizeCompressorOperation(target_size="400kb", format="WEBP"))
)

# Yürüt ve diske kaydet
result_ctx = pipeline.execute(ctx)
result_ctx.save("output.webp")

print(f"Başarılı! Çözünürlük: {result_ctx.size}, Format: {result_ctx.source_format}")
```

### 5. Android APK Derleme ve Yükleme

Android projesi `android/` dizini altında Gradle 8.7 ve Android SDK 34 ile derlenecek şekilde yapılandırılmıştır.

```bash
# Android dizinine geçin ve debug APK'yı derleyin
cd android
gradle assembleDebug

# Cihazınıza veya emülatöre tek komutla kurun
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

---

## 🧪 Test ve Doğrulama / Testing

Proje genelinde bellek sızıntısı, ikili arama yakınsaması, GUI durumları ve operasyon sınırlarını denetleyen **57 adet kapsamlı birim testi** bulunmaktadır.

```bash
pytest -v
```

```text
============================== 57 passed in 3.78s ==============================
```

---

## 🌐 Çift Dilli Yerelleştirme / Bilingual Localization

Image Utility Toolbox, ilk günden itibaren **Türkçe** ve **İngilizce** dil desteğine sahiptir.
* **CLI:** Sistem yerelini otomatik algılar; `--lang tr` veya `--lang en` parametresiyle dinamik olarak değiştirilebilir.
* **Masaüstü & Mobil:** Menüden tek tıkla dil değişimi yapılır ve tüm arayüz, durum şeritleri ve bildirimler anında tercüme edilir.

---

## 📄 Lisans / License

Bu proje [MIT Lisansı](LICENSE) kapsamında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.

Copyright © 2026 **Hakan Kayacı**.
