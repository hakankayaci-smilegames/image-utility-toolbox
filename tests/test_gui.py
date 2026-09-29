"""Masaüstü Grafik Arayüzü (GUI) Birim ve Entegrasyon Testleri."""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image
import pytest

# Qt'nin headless ortamda çalışması için offscreen platformunu zorunlu kıl
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import i18n
from image_toolbox.gui.main_window import MainWindow
from image_toolbox.gui.theme import apply_theme


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    apply_theme(app)
    return app


@pytest.fixture
def gui_window(qapp: QApplication) -> MainWindow:
    window = MainWindow()
    return window


def test_gui_initial_state(gui_window: MainWindow) -> None:
    # Başlangıçta görsel yüklü olmadığı için DropZone (indeks 0) aktif olmalı
    assert gui_window.left_stack.currentIndex() == 0
    assert gui_window.tab_widget.count() == 6
    assert gui_window.status_msg_label.text() != ""
    assert gui_window._original_context is None


def test_gui_load_image(gui_window: MainWindow, tmp_path: Path) -> None:
    # Test görseli oluştur
    test_img_path = tmp_path / "gui_test.png"
    Image.new("RGB", (320, 240), (255, 100, 50)).save(test_img_path)

    gui_window.load_image(str(test_img_path))

    # Yüklendikten sonra ImageViewer (indeks 1) aktif olmalı
    assert gui_window.left_stack.currentIndex() == 1
    assert gui_window._original_context is not None
    assert gui_window._original_context.size == (320, 240)
    assert gui_window.status_dim_label.text() == "320 × 240 px"

    # Sekmelerin context'i aldığını kontrol et
    assert gui_window.tab_compress._current_context is not None
    assert gui_window.tab_adjust._current_context is not None
    assert gui_window.tab_effects._current_context is not None
    assert gui_window.tab_watermark._current_context is not None
    assert gui_window.tab_analysis._current_context is not None


def test_gui_compressor_tab_action(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "gui_test_compress.jpg"
    Image.new("RGB", (200, 200), (0, 150, 255)).save(test_img_path, format="JPEG")
    gui_window.load_image(str(test_img_path))

    # Sıkıştırma parametrelerini ayarla ve tıkla
    gui_window.tab_compress.target_spin.setValue(10)  # 10 KB
    gui_window.tab_compress.fmt_combo.setCurrentText("WEBP")
    gui_window.tab_compress._on_compress_clicked()

    # Sonuç güncellenmiş olmalı
    res_ctx = gui_window._current_result_context
    assert res_ctx is not None
    assert len(res_ctx.to_bytes("WEBP")) <= 10 * 1024


def test_gui_effects_and_adjustments(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "gui_test_effects.png"
    Image.new("RGB", (200, 200), (128, 128, 128)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    # Sepia preset uygula
    gui_window.tab_effects._apply_preset("sepia")
    assert gui_window._current_result_context is not None
    assert "artistic" in gui_window._current_result_context.history

    # Döndürme uygula
    gui_window.tab_adjust._apply_transform(angle=90)
    assert "transform" in gui_window._current_result_context.history


def test_gui_language_switching(gui_window: MainWindow) -> None:
    # 1. Türkçe kontrolü
    i18n.set_language("tr")
    assert "Sıkıştırma" in gui_window.tab_widget.tabText(0)
    assert gui_window.tab_compress.target_label.text() == "Hedef Dosya Boyutu:"
    assert gui_window.tab_adjust.width_label.text() == "Genişlik:"
    assert gui_window.tab_effects.selector_group.title() == "Sanatsal Filtreler ve Efektler"
    assert gui_window.tab_watermark.text_group.title() == "Metin Filigranı"
    assert gui_window.tab_analysis.pal_group.title() == "Baskın Renk Paleti (K-Means)"
    assert gui_window.tab_batch.dir_group.title() == "Klasör Seçimi"

    # 2. İngilizceye geçiş
    i18n.set_language("en")
    assert "Compress" in gui_window.tab_widget.tabText(0)
    assert gui_window.tab_compress.target_label.text() == "Target File Size:"
    assert gui_window.tab_adjust.width_label.text() == "Width:"
    assert gui_window.tab_effects.selector_group.title() == "Artistic Filters & Effects"
    assert gui_window.tab_watermark.text_group.title() == "Text Watermark"
    assert gui_window.tab_analysis.pal_group.title() == "Dominant Color Palette (K-Means)"
    assert gui_window.tab_batch.dir_group.title() == "Directory Selection"

    # 3. Tekrar Türkçeye dön
    i18n.set_language("tr")
    assert "Sıkıştırma" in gui_window.tab_widget.tabText(0)
    assert gui_window.tab_compress.target_label.text() == "Hedef Dosya Boyutu:"


def test_canvas_interactive_navigation(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "canvas_test.png"
    Image.new("RGB", (600, 400), (80, 120, 160)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    viewer = gui_window.image_viewer
    init_zoom = viewer._zoom
    assert init_zoom > 0

    # Zoom In
    viewer.zoom_in()
    assert viewer._zoom > init_zoom

    # Zoom Out
    viewer.zoom_out()
    viewer.zoom_out()
    assert viewer._zoom < init_zoom * 1.25

    # 100% Reset
    viewer.reset_zoom_100()
    assert viewer._zoom == 1.0

    # Fit to window
    viewer.fit_to_window()
    assert viewer._auto_fit is True


def test_effects_contextual_pages_and_live_preview(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "effects_test.png"
    Image.new("RGB", (200, 200), (100, 150, 200)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    effects = gui_window.tab_effects

    # 1. Sepia seç ve slider değiştir
    effects._on_effect_selected(0)
    assert effects.stack.currentIndex() == 0
    effects.sepia_slider.setValue(80)
    effects._run_live_effect()
    assert gui_window._current_result_context is not None
    assert "artistic" in gui_window._current_result_context.history

    # 2. Vinyet seç ve slider değiştir
    effects._on_effect_selected(4)
    assert effects.stack.currentIndex() == 4
    effects.vig_op_slider.setValue(60)
    effects._run_live_effect()
    assert "vignette" in gui_window._current_result_context.history

    # 3. Keskinleştir seç
    effects._on_effect_selected(5)
    assert effects.stack.currentIndex() == 5
    effects._run_live_effect()
    assert "sharpness" in gui_window._current_result_context.history

    # 4. Efekti sıfırla
    effects._on_clear_clicked()
    assert len(gui_window._current_result_context.history) == 0


def test_adjustments_live_preview(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "adjust_test.png"
    Image.new("RGB", (200, 200), (120, 120, 120)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    adj = gui_window.tab_adjust

    # Parlaklık değiştir ve canlı çalıştır
    adj.bright_slider.setValue(25)
    adj._run_live_adjustments()
    assert gui_window._current_result_context is not None
    assert "exposure" in gui_window._current_result_context.history

    # Sıfırla
    adj._on_reset_sliders()
    assert adj.bright_slider.value() == 0
    assert len(gui_window._current_result_context.history) == 0


def test_gui_reset_and_close(gui_window: MainWindow, tmp_path: Path) -> None:
    test_img_path = tmp_path / "gui_test_reset.png"
    Image.new("RGB", (100, 100), (0, 0, 0)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    # Değişiklik yap
    gui_window.tab_effects._apply_preset("cyberpunk")
    assert len(gui_window._current_result_context.history) > 0

    # Orijinale sıfırla
    gui_window.action_reset_to_original()
    assert len(gui_window._current_result_context.history) == 0

    # Görseli kapat
    gui_window.action_close_image()
    assert gui_window.left_stack.currentIndex() == 0
    assert gui_window._original_context is None


def test_canvas_middle_click_pan(gui_window: MainWindow, tmp_path: Path) -> None:
    """Orta fare tuşu ile tuvalde gezinme (Pan) fonksiyonunu doğrular."""
    from PyQt6.QtCore import QPointF, Qt
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtWidgets import QApplication

    test_img_path = tmp_path / "pan_test.png"
    Image.new("RGB", (1600, 1200), (50, 100, 150)).save(test_img_path)
    gui_window.show()
    gui_window.resize(1000, 680)
    gui_window.load_image(str(test_img_path))

    viewer = gui_window.image_viewer
    scroll = viewer.res_scroll
    label = viewer.res_label

    # Zoom %100 yapıp layout ve scrollbar menzilini aç
    viewer.reset_zoom_100()
    QApplication.processEvents()

    h_bar = scroll.horizontalScrollBar()
    v_bar = scroll.verticalScrollBar()
    h_bar.setValue(100)
    v_bar.setValue(100)
    init_h = h_bar.value()

    # 1. Görsel etiketinin (ScaledImageLabel) üzerine orta fare tuşuyla bas
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(200, 200),
        QPointF(500, 500),
        Qt.MouseButton.MiddleButton,
        Qt.MouseButton.MiddleButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(label, press_event)
    assert scroll._is_panning is True

    # 2. Fareyi sola doğru 40 piksel sürükle (x: 500 -> 460) -> h_bar değeri 40 artmalı
    move_event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(160, 200),
        QPointF(460, 500),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.MiddleButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(label, move_event)
    assert h_bar.value() == init_h + 40

    # 3. Fareyi bırak
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(160, 200),
        QPointF(460, 500),
        Qt.MouseButton.MiddleButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(label, release_event)
    assert scroll._is_panning is False


def test_effect_commit_and_reset_isolation(gui_window: MainWindow, tmp_path: Path) -> None:
    """Efekt sabitleme ve sıfırlama izolasyonunu doğrular (Sepia sabitlenince Cyberpunk sıfırlansa da Sepia kalmalı)."""
    test_img_path = tmp_path / "effect_isolation.png"
    Image.new("RGB", (100, 100), (200, 150, 100)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    effects = gui_window.tab_effects

    # 1. Sepia uygula ve 'Efekti Sabitle'ye bas
    effects._apply_preset("sepia")
    assert "artistic" in gui_window._current_result_context.history
    effects._on_commit_clicked()

    # Undo yığınında 2 durum olmalı: [orijinal, sepia_sabitlenmiş]
    assert len(gui_window._undo_stack) == 2
    assert "artistic" in gui_window._committed_context.history

    # 2. Cyberpunk hazır ayarını seçip canlı önizle
    effects._apply_preset("cyberpunk")
    # Önizlemede 2 adet sanatsal efekt geçmişi var (Sepia + Cyberpunk)
    assert gui_window._current_result_context.history.count("artistic") == 2

    # 3. Beğenmeyip 'Efekti Sıfırla' düğmesine tıkla
    effects._on_clear_clicked()

    # Sepia KORUNMALI, yalnızca Cyberpunk önizlemesi sıfırlanmalı!
    assert gui_window._current_result_context.history.count("artistic") == 1
    assert gui_window._current_result_context.history == gui_window._committed_context.history


def test_global_undo_redo_stack(gui_window: MainWindow, tmp_path: Path) -> None:
    """Global Ctrl+Z ve Ctrl+Y / Undo-Redo yığınının eksiksiz çalıştığını doğrular."""
    test_img_path = tmp_path / "undo_test.png"
    Image.new("RGB", (100, 100), (120, 120, 120)).save(test_img_path)
    gui_window.load_image(str(test_img_path))

    assert len(gui_window._undo_stack) == 1
    assert len(gui_window._redo_stack) == 0
    assert gui_window.act_undo.isEnabled() is False
    assert gui_window.act_redo.isEnabled() is False

    # 1. Adım: Sepia uygula ve sabitle
    gui_window.tab_effects._apply_preset("sepia")
    gui_window.tab_effects._on_commit_clicked()
    assert len(gui_window._undo_stack) == 2
    assert gui_window.act_undo.isEnabled() is True

    # 2. Adım: Vinyet uygula ve sabitle
    gui_window.tab_effects._apply_vignette()
    gui_window.tab_effects._on_commit_clicked()
    assert len(gui_window._undo_stack) == 3
    assert "vignette" in gui_window._current_result_context.history

    # 3. Geri Al (Ctrl+Z): Vinyet geri alınmalı, Sepia kalmalı
    gui_window.undo()
    assert len(gui_window._undo_stack) == 2
    assert len(gui_window._redo_stack) == 1
    assert "vignette" not in gui_window._current_result_context.history
    assert "artistic" in gui_window._current_result_context.history
    assert gui_window.act_redo.isEnabled() is True

    # 4. Tekrar Geri Al (Ctrl+Z): Sepia da geri alınmalı, orijinal görsele dönmeli
    gui_window.undo()
    assert len(gui_window._undo_stack) == 1
    assert len(gui_window._redo_stack) == 2
    assert len(gui_window._current_result_context.history) == 0
    assert gui_window.act_undo.isEnabled() is False

    # 5. İleri Al (Ctrl+Y / Redo): Sepia tekrar gelmeli
    gui_window.redo()
    assert len(gui_window._undo_stack) == 2
    assert len(gui_window._redo_stack) == 1
    assert "artistic" in gui_window._current_result_context.history

    # 6. Tekrar İleri Al (Ctrl+Y / Redo): Vinyet tekrar gelmeli
    gui_window.redo()
    assert len(gui_window._undo_stack) == 3
    assert len(gui_window._redo_stack) == 0
    assert "vignette" in gui_window._current_result_context.history
    assert gui_window.act_redo.isEnabled() is False

