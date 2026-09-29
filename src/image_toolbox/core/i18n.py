"""Çift Dilli Yerelleştirme (Bilingual Localization - TR/EN)."""

from __future__ import annotations

import os
from typing import Dict


MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        # Core & CLI
        "err_invalid_param": "Invalid parameter '{param}': {reason}",
        "err_target_unreachable": "Could not compress image to target size {target_bytes} bytes. Lowest reached: {reached_bytes} bytes at dimensions {width}x{height}.",
        "err_corrupt_image": "Unable to decode image from source: {reason}",
        "err_operation_failed": "Operation '{op}' failed: {reason}",
        "cli_compress_success": "Successfully compressed image to {size_kb:.2f} KB (Quality: {quality}, Dimensions: {width}x{height}) in {iterations} iterations.",
        "cli_batch_summary": "Batch processing complete: {success} succeeded, {failed} failed in {duration:.2f}s.",
        "cli_pipeline_running": "Executing pipeline with {count} operations...",
        "palette_header": "Dominant Color Palette (Top {k}):",
        "exif_empty": "No EXIF metadata found in image.",
        "exif_sanitized": "EXIF metadata successfully sanitized.",
        
        # GUI Menus
        "menu_file": "File",
        "menu_edit": "Edit",
        "menu_view": "View",
        "menu_tools": "Tools",
        "menu_language": "Language",
        "menu_help": "Help",
        "action_open": "Open Image...",
        "action_save_as": "Save As...",
        "action_close": "Close Image",
        "action_quit": "Exit",
        "action_undo": "Undo",
        "action_redo": "Redo",
        "action_reset": "Reset to Original",
        "action_copy": "Copy to Clipboard",
        "action_zoom_in": "Zoom In",
        "action_zoom_out": "Zoom Out",
        "action_fit": "Fit to Window",
        "action_about": "About Image Utility Toolbox",
        "action_shortcuts": "Keyboard Shortcuts",
        
        # GUI Tabs
        "tab_compress": "Compress",
        "tab_adjust": "Adjust",
        "tab_effects": "Effects",
        "tab_watermark": "Watermark",
        "tab_analysis": "Analysis",
        "tab_batch": "Batch",

        # GUI Buttons & Labels
        "btn_open": "Open Image",
        "btn_apply": "Apply",
        "btn_save": "Save Image",
        "btn_reset": "Reset",
        "btn_choose_logo": "Select Logo...",
        "btn_run_batch": "Start Batch Processing",
        "view_original": "Original",
        "view_result": "Result",
        "view_split": "Compare",
        "drop_zone_title": "Drag & Drop Image Here",
        "drop_zone_sub": "Supports PNG, JPG, WebP, BMP, TIFF (or click Open Image)",
        
        # GUI Status & Feedback
        "status_ready": "Ready",
        "status_image_loaded": "Loaded: {name} ({width}x{height} px, {size_kb:.1f} KB)",
        "status_processing": "Processing: {op}...",
        "status_success": "Operation '{op}' completed in {duration:.2f}s",
        "status_saved": "Image saved successfully: {path}",
        "status_reset": "Reverted back to original image.",
        "status_undo": "Action undone.",
        "status_redo": "Action redone.",
        "status_no_more_undo": "No more actions to undo.",
        "status_no_more_redo": "No more actions to redo.",
        "status_effect_committed": "Effect committed. (Ctrl+Z to undo)",
        "status_effect_cleared": "Effect preview reset.",
        "status_compress_done": "Compressed to {size_kb:.1f} KB (Target: {target}, Quality: {quality}, Saved: %{saved:.1f})",
        
        # Dialogs
        "dialog_open_title": "Select an Image",
        "dialog_save_title": "Save Processed Image",
        "dialog_logo_title": "Select Logo Image (PNG)",
        "dialog_batch_in_title": "Select Input Directory",
        "dialog_batch_out_title": "Select Output Directory",
        "about_text": "<h3>Image Utility Toolbox</h3><p>High-performance, modular image processing engine and desktop studio.</p><p>Built with Python, PyQt6, Pillow, OpenCV & NumPy.</p>",

        # Compressor Tab
        "target_size_label": "Target File Size:",
        "output_format_label": "Output Format:",
        "strip_metadata_check": "Strip EXIF and metadata (smaller file)",
        "min_quality_label": "Minimum Quality Threshold (Before Fallback): {val}",
        "btn_run_compress": "Run Target Size Compression",
        "compress_report_title": "Compression Results Report",
        "label_orig_size": "Original Size: {val}",
        "label_compressed_size": "Compressed Size: {val}",
        "label_quality_found": "Optimal Quality Found: {val}",
        "label_iterations": "Binary Search Iterations: {val}",
        "label_downscale": "Resolution Status: {val}",
        "label_savings": "Savings: {val}%",

        # Adjustments Tab
        "group_geom": "Resize and Crop",
        "label_width": "Width:",
        "label_height": "Height:",
        "check_lock_ratio": "Preserve Aspect Ratio",
        "label_resize_mode": "Resize Mode:",
        "mode_fit": "Fit (Keep Aspect)",
        "mode_fill": "Fill (Crop to Fit)",
        "mode_pad": "Pad (Canvas Fill)",
        "mode_exact": "Exact (Stretch)",
        "group_transform": "Rotate and Flip",
        "btn_rot_left": "90° Left",
        "btn_rot_right": "90° Right",
        "btn_flip_h": "Flip Horizontal",
        "btn_flip_v": "Flip Vertical",
        "group_tone": "Exposure and Tone",
        "label_brightness": "Brightness: {val}",
        "label_contrast": "Contrast: {val}x",
        "label_temp": "Color Temperature: {val}K",
        "label_vibrance": "Smart Vibrance: {val}",
        "btn_apply_adjust": "Apply Adjustments",
        "btn_reset_adjust": "Reset Tone Sliders",

        # Effects Tab
        "group_presets": "Artistic Filters & Effects",
        "effect_sepia": "Sepia",
        "effect_vintage": "Vintage Grain",
        "effect_cyanotype": "Cyanotype",
        "effect_cyberpunk": "Cyberpunk",
        "effect_vignette": "Vignette",
        "effect_sharpness": "Sharpness",
        "effect_blur": "Blur Suite",
        "effect_clahe": "CLAHE Contrast",
        "effect_sketch": "Sketch / Edges",
        "effect_borders": "Borders",
        "group_effect_params": "Selected Effect Controls",
        "label_intensity": "Intensity: {val}%",
        "label_grain": "Grain Amount: {val}%",
        "label_radius": "Radius: {val}",
        "label_feather": "Feather: {val}%",
        "label_opacity": "Opacity: {val}%",
        "label_amount": "Amount: {val}x",
        "label_clarity": "Clarity: {val}",
        "label_blur_mode": "Blur Type:",
        "label_blur_radius": "Blur Radius: {val} px",
        "label_motion_angle": "Motion Angle: {val}°",
        "label_clip_limit": "Clip Limit: {val}",
        "label_grid_size": "Grid Size: {val}x{val}",
        "label_sketch_mode": "Sketch Mode:",
        "label_border_mode": "Border Style:",
        "label_border_width": "Border Width: {val} px",
        "label_corner_radius": "Corner Radius: {val} px",
        "btn_commit_effect": "Bake / Commit Effect",
        "btn_clear_effect": "Revert to Base",

        # Watermark Tab
        "group_watermark_text": "Text Watermark",
        "group_watermark_logo": "PNG Logo Overlay (Optional)",
        "no_logo_selected": "No logo selected",
        "group_anchor": "Position (9 Anchor Points)",
        "anchor_tl": "Top Left",
        "anchor_tc": "Top Center",
        "anchor_tr": "Top Right",
        "anchor_cl": "Center Left",
        "anchor_c": "Center",
        "anchor_cr": "Center Right",
        "anchor_bl": "Bottom Left",
        "anchor_bc": "Bottom Center",
        "anchor_br": "Bottom Right",
        "group_appearance": "Appearance and Opacity",
        "label_wm_opacity": "Opacity: {val}%",
        "btn_apply_watermark": "Apply Watermark",

        # Analysis Tab
        "group_palette": "Dominant Color Palette (K-Means)",
        "label_k_count": "Color Count (K):",
        "btn_extract_palette": "Extract Palette",
        "copied_hex": "Copied: {hex}",
        "group_exif": "EXIF Metadata and Privacy",
        "btn_inspect_exif": "Read EXIF",
        "btn_strip_gps": "Strip GPS Data",
        "btn_strip_all": "Strip All EXIF Data",
        "header_tag": "Tag",
        "header_val": "Value",

        # Batch Tab
        "group_batch_dirs": "Directory Selection",
        "label_in_dir": "Source Folder:",
        "label_out_dir": "Target Folder:",
        "btn_browse": "Browse...",
        "group_batch_op": "Batch Processing Operation",
        "label_operation": "Applied Operation:",
        "label_workers": "Worker Threads:",
        "group_log": "Processing Log",
        "header_file": "File",
        "header_status": "Status",
        "header_duration": "Duration",
        "status_success_text": "Success",
        "status_error_text": "Error",
    },
    "tr": {
        # Core & CLI
        "err_invalid_param": "'{param}' parametresi geçersiz: {reason}",
        "err_target_unreachable": "Görsel hedef boyut olan {target_bytes} byte değerine sıkıştırılamadı. En düşük ulaşılan: {reached_bytes} byte ({width}x{height} çözünürlükte).",
        "err_corrupt_image": "Görsel kaynaktan okunamadı/bozuk: {reason}",
        "err_operation_failed": "'{op}' operasyonu uygulanamadı: {reason}",
        "cli_compress_success": "Görsel başarıyla {size_kb:.2f} KB boyutuna sıkıştırıldı (Kalite: {quality}, Çözünürlük: {width}x{height}, İterasyon: {iterations}).",
        "cli_batch_summary": "Toplu işlem tamamlandı: {success} başarılı, {failed} hatalı (Süre: {duration:.2f}s).",
        "cli_pipeline_running": "{count} adımdan oluşan boru hattı çalıştırılıyor...",
        "palette_header": "Baskın Renk Paleti (İlk {k}):",
        "exif_empty": "Görselde EXIF metaverisi bulunamadı.",
        "exif_sanitized": "EXIF metaverisi başarıyla temizlendi/sterilize edildi.",
        
        # GUI Menus
        "menu_file": "Dosya",
        "menu_edit": "Düzen",
        "menu_view": "Görünüm",
        "menu_tools": "Araçlar",
        "menu_language": "Dil (Language)",
        "menu_help": "Yardım",
        "action_open": "Görsel Aç...",
        "action_save_as": "Farklı Kaydet...",
        "action_close": "Görseli Kapat",
        "action_quit": "Çıkış",
        "action_undo": "Geri Al",
        "action_redo": "İleri Al",
        "action_reset": "Orijinale Sıfırla",
        "action_copy": "Panoya Kopyala",
        "action_zoom_in": "Yakınlaştır",
        "action_zoom_out": "Uzaklaştır",
        "action_fit": "Pencereye Sığdır",
        "action_about": "Image Utility Toolbox Hakkında",
        "action_shortcuts": "Klavye Kısayolları",

        # GUI Tabs
        "tab_compress": "Sıkıştırma",
        "tab_adjust": "Ayarlar",
        "tab_effects": "Efektler",
        "tab_watermark": "Filigran",
        "tab_analysis": "Analiz",
        "tab_batch": "Toplu İşlem",

        # GUI Buttons & Labels
        "btn_open": "Görsel Aç",
        "btn_apply": "Uygula",
        "btn_save": "Görseli Kaydet",
        "btn_reset": "Sıfırla",
        "btn_choose_logo": "Logo Seç...",
        "btn_run_batch": "Toplu İşlemi Başlat",
        "view_original": "Orijinal",
        "view_result": "Sonuç",
        "view_split": "Karşılaştır",
        "drop_zone_title": "Görseli Buraya Sürükleyip Bırakın",
        "drop_zone_sub": "PNG, JPG, WebP, BMP, TIFF desteklenir (veya Görsel Aç'a tıklayın)",

        # GUI Status & Feedback
        "status_ready": "Hazır",
        "status_image_loaded": "Yüklendi: {name} ({width}x{height} px, {size_kb:.1f} KB)",
        "status_processing": "İşleniyor: {op}...",
        "status_success": "'{op}' işlemi {duration:.2f} saniyede tamamlandı",
        "status_saved": "Görsel başarıyla kaydedildi: {path}",
        "status_reset": "Orijinal görsel durumuna dönüldü.",
        "status_undo": "İşlem geri alındı.",
        "status_redo": "İşlem ileri alındı.",
        "status_no_more_undo": "Geri alınacak başka işlem yok.",
        "status_no_more_redo": "İleri alınacak başka işlem yok.",
        "status_effect_committed": "Efekt sabitlendi. (Geri almak için Ctrl+Z)",
        "status_effect_cleared": "Efekt önizlemesi sıfırlandı.",
        "status_compress_done": "{size_kb:.1f} KB boyutuna sıkıştırıldı (Hedef: {target}, Kalite: {quality}, Tasarruf: %{saved:.1f})",

        # Dialogs
        "dialog_open_title": "Görsel Dosyası Seç",
        "dialog_save_title": "İşlenen Görseli Kaydet",
        "dialog_logo_title": "Logo Görseli Seç (PNG)",
        "dialog_batch_in_title": "Kaynak Klasörü Seç",
        "dialog_batch_out_title": "Hedef Klasörü Seç",
        "about_text": "<h3>Image Utility Toolbox</h3><p>Yüksek performanslı, modüler görüntü işleme motoru ve masaüstü stüdyosu.</p><p>Python, PyQt6, Pillow, OpenCV & NumPy ile inşa edildi.</p>",

        # Compressor Tab
        "target_size_label": "Hedef Dosya Boyutu:",
        "output_format_label": "Çıktı Formatı:",
        "strip_metadata_check": "EXIF ve Metaverileri Temizle (Daha Küçük Dosya)",
        "min_quality_label": "Minimum Kalite Eşiği (Düşüş Öncesi): {val}",
        "btn_run_compress": "Hedef Boyut Sıkıştırmayı Çalıştır",
        "compress_report_title": "Sıkıştırma Sonuç Raporu",
        "label_orig_size": "Orijinal Boyut: {val}",
        "label_compressed_size": "Sıkıştırılmış Boyut: {val}",
        "label_quality_found": "Tespit Edilen En İyi Kalite: {val}",
        "label_iterations": "İkili Arama İterasyonu: {val}",
        "label_downscale": "Çözünürlük Durumu: {val}",
        "label_savings": "Tasarruf: %{val}",

        # Adjustments Tab
        "group_geom": "Boyutlandırma ve Kırpma",
        "label_width": "Genişlik:",
        "label_height": "Yükseklik:",
        "check_lock_ratio": "En-Boy Oranını Koru",
        "label_resize_mode": "Boyutlandırma Modu:",
        "mode_fit": "Fit (Sığdır)",
        "mode_fill": "Fill (Doldur & Kırp)",
        "mode_pad": "Pad (Tuval Doldur)",
        "mode_exact": "Exact (Zorla)",
        "group_transform": "Döndürme ve Aynalama",
        "btn_rot_left": "90° Sola",
        "btn_rot_right": "90° Sağa",
        "btn_flip_h": "Yatay Çevir",
        "btn_flip_v": "Dikey Çevir",
        "group_tone": "Pozlama ve Ton Ayarları",
        "label_brightness": "Parlaklık: {val}",
        "label_contrast": "Kontrast: {val}x",
        "label_temp": "Renk Sıcaklığı: {val}K",
        "label_vibrance": "Akıllı Vibrance: {val}",
        "btn_apply_adjust": "Ayarları Uygula",
        "btn_reset_adjust": "Sürgüleri Sıfırla",

        # Effects Tab
        "group_presets": "Sanatsal Filtreler ve Efektler",
        "effect_sepia": "Sepia",
        "effect_vintage": "Vintage Grain",
        "effect_cyanotype": "Cyanotype",
        "effect_cyberpunk": "Cyberpunk",
        "effect_vignette": "Vinyet",
        "effect_sharpness": "Keskinleştir",
        "effect_blur": "Bulanıklık",
        "effect_clahe": "CLAHE Kontrast",
        "effect_sketch": "Kurşun Kalem Eskiz",
        "effect_borders": "Çerçeveler",
        "group_effect_params": "Seçili Efekt Ayarları",
        "label_intensity": "Yoğunluk: %{val}",
        "label_grain": "Gren Miktarı: %{val}",
        "label_radius": "Yarıçap: {val}",
        "label_feather": "Yumuşaklık: %{val}",
        "label_opacity": "Opaklık: %{val}",
        "label_amount": "Miktar: {val}x",
        "label_clarity": "Netlik (Clarity): {val}",
        "label_blur_mode": "Bulanıklık Türü:",
        "label_blur_radius": "Bulanıklık Yarıçapı: {val} px",
        "label_motion_angle": "Hareket Açısı: {val}°",
        "label_clip_limit": "Eşik Sınırı (Clip): {val}",
        "label_grid_size": "Izgara Boyutu: {val}x{val}",
        "label_sketch_mode": "Eskiz Modu:",
        "label_border_mode": "Çerçeve Stili:",
        "label_border_width": "Çerçeve Kalınlığı: {val} px",
        "label_corner_radius": "Köşe Yarıçapı: {val} px",
        "btn_commit_effect": "Efekti Sabitle",
        "btn_clear_effect": "Efekti Sıfırla",

        # Watermark Tab
        "group_watermark_text": "Metin Filigranı",
        "group_watermark_logo": "PNG / Şeffaf Logo Filigranı (İsteğe Bağlı)",
        "no_logo_selected": "Seçilen logo yok",
        "group_anchor": "Konum (9 Çapa Noktası)",
        "anchor_tl": "Sol Üst",
        "anchor_tc": "Orta Üst",
        "anchor_tr": "Sağ Üst",
        "anchor_cl": "Sol Orta",
        "anchor_c": "Merkez",
        "anchor_cr": "Sağ Orta",
        "anchor_bl": "Sol Alt",
        "anchor_bc": "Orta Alt",
        "anchor_br": "Sağ Alt",
        "group_appearance": "Görünüm Ayarları",
        "label_wm_opacity": "Opaklık: %{val}",
        "btn_apply_watermark": "Filigranı Ekle",

        # Analysis Tab
        "group_palette": "Baskın Renk Paleti (K-Means)",
        "label_k_count": "Renk Sayısı (K):",
        "btn_extract_palette": "Renk Paletini Çıkar",
        "copied_hex": "Kopyalandı: {hex}",
        "group_exif": "EXIF Metaverileri ve Güvenlik",
        "btn_inspect_exif": "EXIF Oku",
        "btn_strip_gps": "GPS Bilgisini Temizle",
        "btn_strip_all": "Tüm EXIF Verisini Sil",
        "header_tag": "Etiket (Tag)",
        "header_val": "Değer (Value)",

        # Batch Tab
        "group_batch_dirs": "Klasör Seçimi",
        "label_in_dir": "Kaynak Klasör:",
        "label_out_dir": "Hedef Klasör:",
        "btn_browse": "Gözat...",
        "group_batch_op": "Toplu İşlem Operasyonu",
        "label_operation": "Uygulanacak İşlem:",
        "label_workers": "İş Parçacığı Sayısı:",
        "group_log": "İşlem Günlüğü",
        "header_file": "Dosya",
        "header_status": "Durum",
        "header_duration": "Süre",
        "status_success_text": "Başarılı",
        "status_error_text": "Hata",
    },
}


class I18n:
    """Yerelleştirme yöneticisi."""

    def __init__(self, default_lang: str = "tr") -> None:
        env_lang = os.environ.get("IMAGE_TOOLBOX_LANG", default_lang).lower()
        self.current_lang = "tr" if env_lang.startswith("tr") else "en"
        self._listeners = []

    def add_listener(self, callback) -> None:
        """Dil değiştiğinde tetiklenecek dinleyici ekler."""
        self._listeners.append(callback)

    def set_language(self, lang: str) -> None:
        normalized = lang.lower()
        new_lang = "tr" if normalized.startswith("tr") else "en"
        if new_lang != self.current_lang:
            self.current_lang = new_lang
            for cb in self._listeners:
                try:
                    cb(self.current_lang)
                except Exception:
                    pass

    def get(self, key: str, **kwargs: object) -> str:
        lang_dict = MESSAGES.get(self.current_lang, MESSAGES["en"])
        template = lang_dict.get(key) or MESSAGES["en"].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template


# Tekil global örnek
i18n = I18n()
_ = i18n.get
