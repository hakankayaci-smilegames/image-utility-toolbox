/**
 * Image Utility Toolbox - Çift Dilli Yerelleştirme (Bilingual Localization - TR/EN)
 */
const MESSAGES = {
    tr: {
        app_title: "Image Utility Toolbox",
        menu_file: "Dosya",
        menu_edit: "Düzen",
        menu_view: "Görünüm",
        menu_language: "Dil",
        menu_help: "Yardım",
        action_open: "Görsel Aç...",
        action_save_as: "Galeriye Kaydet",
        action_share: "Paylaş",
        action_close: "Görseli Kapat",
        action_reset: "Orijinale Sıfırla",
        action_copy: "Panoya Kopyala",
        action_zoom_in: "Yakınlaştır",
        action_zoom_out: "Uzaklaştır",
        action_fit: "Pencereye Sığdır",
        action_split: "Karşılaştırma Modu",
        action_about: "Hakkında",
        action_shortcuts: "Kısayollar",
        
        tab_compress: "Sıkıştırma",
        tab_adjust: "Ayarlar",
        tab_effects: "Efektler",
        tab_watermark: "Filigran",
        tab_analysis: "Analiz",
        tab_batch: "Toplu İşlem",

        drop_zone_title: "Fotoğraf Seç veya Buraya Bırak",
        drop_zone_sub: "PNG, JPG, WebP, BMP desteklenir",
        btn_open_photo: "Galeriden Fotoğraf Seç",
        btn_apply: "Uygula",
        btn_save: "Kaydet",
        btn_reset: "Sıfırla",
        btn_commit: "Efekti Sabitle",
        btn_clear: "Efekti Sıfırla",

        target_size_label: "Hedef Dosya Boyutu:",
        output_format_label: "Çıktı Formatı:",
        fast_mode_check: "Hızlı Arama Modu",
        fallback_downscale_check: "Çözünürlük Düşürmeye İzin Ver (Lanczos)",
        strip_metadata_check: "EXIF ve Metaveriyi Temizle",
        btn_run_compress: "Hedef Boyut Sıkıştırmayı Çalıştır",
        label_orig_size: "Orijinal Boyut:",
        label_compressed_size: "Sıkıştırılmış Boyut:",
        label_savings: "Tasarruf:",
        label_iterations: "İterasyon:",

        group_geom: "Boyutlandırma ve Kırpma",
        label_width: "Genişlik (px):",
        label_height: "Yükseklik (px):",
        check_lock_ratio: "En-Boy Oranını Koru",
        label_crop_ratio: "Kırpma Oranı:",
        btn_apply_crop: "Kırp",
        btn_rot_left: "90° Sola",
        btn_rot_right: "90° Sağa",
        btn_rot_180: "180° Çevir",
        btn_flip_h: "Yatay Aynala",
        btn_flip_v: "Dikey Aynala",
        label_free_rot: "Serbest Döndürme Açısı:",
        
        group_tone: "Pozlama ve Renk Ayarları",
        label_brightness: "Parlaklık:",
        label_contrast: "Kontrast:",
        label_temp: "Renk Sıcaklığı (Kelvin):",
        label_vibrance: "Canlılık (Vibrance):",
        btn_apply_adjust: "Ayarları Sabitle",
        btn_reset_adjust: "Sürgüleri Sıfırla",

        group_presets: "Sanatsal Filtreler ve Efektler",
        effect_sepia: "Sepia",
        effect_vintage: "Vintage",
        effect_cyanotype: "Cyanotype",
        effect_cyberpunk: "Cyberpunk",
        effect_vignette: "Vinyet",
        effect_sharpness: "Keskinleştir",
        effect_blur: "Bulanıklık",
        effect_denoise: "Gürültü Gider",
        effect_sketch: "Eskiz / Kenar",
        effect_clahe: "CLAHE Kontrast",
        effect_threshold: "Eşikleme",
        effect_borders: "Çerçeveler",

        label_intensity: "Yoğunluk:",
        label_grain: "Gren Miktarı:",
        label_radius: "Yarıçap:",
        label_softness: "Yumuşaklık:",
        label_opacity: "Opaklık:",
        label_color: "Renk:",
        label_amount: "Şiddet:",
        label_clarity: "Netlik (Clarity):",
        label_blur_mode: "Bulanıklık Modu:",
        label_tilt_shift: "Minyatür Odak (Tilt-Shift):",
        label_border_style: "Çerçeve Stili:",
        label_border_width: "Çerçeve Kalınlığı:",
        label_corner_radius: "Köşe Yarıçapı:",

        group_watermark_text: "Metin Filigranı",
        group_watermark_logo: "Logo Filigranı",
        label_wm_text: "Filigran Metni:",
        label_font_size: "Yazı Boyutu:",
        label_logo_scale: "Logo Ölçeği:",
        btn_choose_logo: "Logo Görseli Seç...",
        label_anchor: "Konum (9 Çapa Noktası):",
        btn_apply_watermark: "Filigranı Ekle",

        group_palette: "Baskın Renk Paleti (K-Means 5)",
        btn_extract_palette: "Renk Paletini Çıkar",
        group_exif: "EXIF Metaverileri",
        btn_inspect_exif: "EXIF Bilgilerini Oku",
        btn_strip_gps: "GPS Konumunu Temizle",
        btn_strip_all: "Tüm EXIF'i Sil",

        group_batch: "Toplu Görsel İşleme",
        btn_select_batch: "Çoklu Fotoğraf Seç...",
        btn_start_batch: "Toplu İşlemi Başlat",
        batch_recipe_label: "Uygulanacak İşlem:",
        recipe_compress_500: "Hedef 500 KB WebP Sıkıştırma",
        recipe_resize_1920: "Max 1920px Boyutlandırma",
        recipe_strip_exif: "Tüm EXIF'i Temizleme",

        status_ready: "Hazır",
        status_image_loaded: "Görsel yüklendi: {name} ({width}x{height} px)",
        status_saved: "Galeriye başarıyla kaydedildi!",
        status_reset: "Orijinal durumuna geri dönüldü.",
        copied_hex: "Kopyalandı: {hex}",
        about_title: "Image Utility Toolbox Mobile",
        about_desc: "Yüksek performanslı görüntü işleme ve sıkıştırma stüdyosu.\nPython mimarisi temel alınarak Android için optimize edilmiştir.",
        shortcuts_title: "Dokunmatik Kısayollar",
        shortcuts_desc: "• Çift parmak: Yakınlaştırma ve Pan\n• Çift dokunma: Ekrana Sığdır\n• Bölünmüş mod: Orijinal ve işlenmiş halini kaydırıcı ile kıyasla"
    },
    en: {
        app_title: "Image Utility Toolbox",
        menu_file: "File",
        menu_edit: "Edit",
        menu_view: "View",
        menu_language: "Language",
        menu_help: "Help",
        action_open: "Open Image...",
        action_save_as: "Save to Gallery",
        action_share: "Share",
        action_close: "Close Image",
        action_reset: "Reset to Original",
        action_copy: "Copy to Clipboard",
        action_zoom_in: "Zoom In",
        action_zoom_out: "Zoom Out",
        action_fit: "Fit to Screen",
        action_split: "Split Compare Mode",
        action_about: "About",
        action_shortcuts: "Touch Shortcuts",

        tab_compress: "Compress",
        tab_adjust: "Adjust",
        tab_effects: "Effects",
        tab_watermark: "Watermark",
        tab_analysis: "Analysis",
        tab_batch: "Batch",

        drop_zone_title: "Choose a Photo or Drop Here",
        drop_zone_sub: "Supports PNG, JPG, WebP, BMP",
        btn_open_photo: "Choose Photo from Gallery",
        btn_apply: "Apply",
        btn_save: "Save",
        btn_reset: "Reset",
        btn_commit: "Freeze Effect",
        btn_clear: "Reset Effect",

        target_size_label: "Target File Size:",
        output_format_label: "Output Format:",
        fast_mode_check: "Fast Search Mode",
        fallback_downscale_check: "Allow Fallback Downscaling (Lanczos)",
        strip_metadata_check: "Strip EXIF & Metadata",
        btn_run_compress: "Run Target Size Compression",
        label_orig_size: "Original Size:",
        label_compressed_size: "Compressed Size:",
        label_savings: "Savings:",
        label_iterations: "Iterations:",

        group_geom: "Resize & Crop",
        label_width: "Width (px):",
        label_height: "Height (px):",
        check_lock_ratio: "Preserve Aspect Ratio",
        label_crop_ratio: "Crop Ratio:",
        btn_apply_crop: "Crop",
        btn_rot_left: "90° Left",
        btn_rot_right: "90° Right",
        btn_rot_180: "Rotate 180°",
        btn_flip_h: "Flip Horizontal",
        btn_flip_v: "Flip Vertical",
        label_free_rot: "Free Rotation Angle:",

        group_tone: "Exposure & Color Tone",
        label_brightness: "Brightness:",
        label_contrast: "Contrast:",
        label_temp: "Color Temp (Kelvin):",
        label_vibrance: "Vibrance:",
        btn_apply_adjust: "Freeze Adjustments",
        btn_reset_adjust: "Reset Sliders",

        group_presets: "Artistic Filters & Effects",
        effect_sepia: "Sepia",
        effect_vintage: "Vintage",
        effect_cyanotype: "Cyanotype",
        effect_cyberpunk: "Cyberpunk",
        effect_vignette: "Vignette",
        effect_sharpness: "Sharpness",
        effect_blur: "Blur Suite",
        effect_denoise: "Denoise",
        effect_sketch: "Sketch / Edges",
        effect_clahe: "CLAHE Contrast",
        effect_threshold: "Threshold",
        effect_borders: "Borders",

        label_intensity: "Intensity:",
        label_grain: "Grain Amount:",
        label_radius: "Radius:",
        label_softness: "Softness:",
        label_opacity: "Opacity:",
        label_color: "Color:",
        label_amount: "Amount:",
        label_clarity: "Clarity:",
        label_blur_mode: "Blur Mode:",
        label_tilt_shift: "Tilt-Shift Miniature:",
        label_border_style: "Border Style:",
        label_border_width: "Border Width:",
        label_corner_radius: "Corner Radius:",

        group_watermark_text: "Text Watermark",
        group_watermark_logo: "Logo Watermark",
        label_wm_text: "Watermark Text:",
        label_font_size: "Font Size:",
        label_logo_scale: "Logo Scale:",
        btn_choose_logo: "Select Logo Image...",
        label_anchor: "Position (9 Anchor Points):",
        btn_apply_watermark: "Apply Watermark",

        group_palette: "Dominant Color Palette (K-Means 5)",
        btn_extract_palette: "Extract Palette",
        group_exif: "EXIF Metadata",
        btn_inspect_exif: "Read EXIF",
        btn_strip_gps: "Strip GPS Location",
        btn_strip_all: "Strip All EXIF Data",

        group_batch: "Batch Image Processing",
        btn_select_batch: "Select Multiple Photos...",
        btn_start_batch: "Start Batch Processing",
        batch_recipe_label: "Applied Recipe:",
        recipe_compress_500: "Target 500 KB WebP Compression",
        recipe_resize_1920: "Max 1920px Resize",
        recipe_strip_exif: "Strip All EXIF",

        status_ready: "Ready",
        status_image_loaded: "Image loaded: {name} ({width}x{height} px)",
        status_saved: "Successfully saved to Gallery!",
        status_reset: "Reverted to original image.",
        copied_hex: "Copied: {hex}",
        about_title: "Image Utility Toolbox Mobile",
        about_desc: "High-performance image processing and compression studio.\nOptimized for Android with Python core algorithm parity.",
        shortcuts_title: "Touch Shortcuts",
        shortcuts_desc: "• Two fingers: Pinch-to-zoom & Pan\n• Double tap: Fit to screen\n• Split mode: Compare original and result with interactive divider"
    }
};

class I18nManager {
    constructor() {
        this.currentLang = 'tr';
        this.listeners = [];
    }

    setLanguage(lang) {
        this.currentLang = (lang === 'en') ? 'en' : 'tr';
        document.documentElement.lang = this.currentLang;
        this.updateDOM();
        this.listeners.forEach(cb => cb(this.currentLang));
    }

    t(key, params = {}) {
        let text = (MESSAGES[this.currentLang] && MESSAGES[this.currentLang][key]) ||
                   (MESSAGES['en'] && MESSAGES['en'][key]) || key;
        for (const [k, v] of Object.entries(params)) {
            text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
        }
        return text;
    }

    updateDOM() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key);
        });
    }

    addListener(cb) {
        this.listeners.push(cb);
    }
}

const i18n = new I18nManager();
