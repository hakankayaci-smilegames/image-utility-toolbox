"""Image Utility Toolbox - Ana Masaüstü Arayüz Penceresi (Main Window)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from image_toolbox import __version__
from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _, i18n
from image_toolbox.gui.components import (
    DropZoneWidget,
    ImageViewerWidget,
    NotificationBadge,
)
from image_toolbox.gui.dialogs import AboutDialog, ShortcutsDialog
from image_toolbox.gui.tabs import (
    AdjustmentsTab,
    AnalysisTab,
    BatchTab,
    CompressorTab,
    EffectsTab,
    WatermarkTab,
)


class MainWindow(QMainWindow):
    """Modern, sekmeli ve yüksek performanslı masaüstü stüdyo ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Image Utility Toolbox v{__version__}")
        self.resize(1300, 840)
        self.setMinimumSize(1000, 680)

        self._original_context: Optional[ImageContext] = None
        self._committed_context: Optional[ImageContext] = None
        self._current_result_context: Optional[ImageContext] = None
        self._current_file_path: Optional[str] = None
        self._undo_stack: list[ImageContext] = []
        self._redo_stack: list[ImageContext] = []

        self._setup_ui()
        self._setup_menus()
        self._setup_status_bar()

        # Dil değişim dinleyicisi ekle
        i18n.add_listener(self._on_language_changed)

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        # Durum Bildirim Şeridi (Notification Banner)
        self.notification_badge = NotificationBadge(self)
        main_layout.addWidget(self.notification_badge)

        # Yatay Bölücü (Splitter: Sol Görsel Alanı, Sağ Kontrol Sekmeleri)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #334155; width: 4px; }")

        # Sol Alan: Stacked Widget (Karşılama Alanı <-> Görsel Görüntüleyici)
        self.left_stack = QStackedWidget()

        # 0: DropZone (Görsel yokken)
        self.drop_zone = DropZoneWidget()
        self.drop_zone.file_selected.connect(self.load_image)
        self.left_stack.addWidget(self.drop_zone)

        # 1: ImageViewer (Görsel yüklendiğinde)
        self.image_viewer = ImageViewerWidget()
        self.image_viewer.file_dropped.connect(self.load_image)
        self.left_stack.addWidget(self.image_viewer)

        self.left_stack.setCurrentIndex(0)
        self.splitter.addWidget(self.left_stack)

        # Sağ Alan: Sekmeli Kontrol Paneli (QTabWidget)
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumWidth(440)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # 6 Sekmeyi Oluştur
        self.tab_compress = CompressorTab()
        self.tab_adjust = AdjustmentsTab()
        self.tab_effects = EffectsTab()
        self.tab_watermark = WatermarkTab()
        self.tab_analysis = AnalysisTab()
        self.tab_batch = BatchTab()

        # Sinyalleri bağla
        self.tab_compress.apply_requested.connect(self._on_committed_updated)
        self.tab_adjust.apply_requested.connect(self._on_result_updated)
        self.tab_adjust.commit_requested.connect(self._on_committed_updated)
        self.tab_effects.apply_requested.connect(self._on_result_updated)
        self.tab_effects.commit_requested.connect(self._on_effect_committed)
        self.tab_watermark.apply_requested.connect(self._on_committed_updated)
        self.tab_analysis.apply_requested.connect(self._on_committed_updated)
        self.tab_analysis.status_requested.connect(self.show_notification)
        self.tab_batch.status_requested.connect(self.show_notification)

        self.tab_widget.addTab(self.tab_compress, _("tab_compress"))
        self.tab_widget.addTab(self.tab_adjust, _("tab_adjust"))
        self.tab_widget.addTab(self.tab_effects, _("tab_effects"))
        self.tab_widget.addTab(self.tab_watermark, _("tab_watermark"))
        self.tab_widget.addTab(self.tab_analysis, _("tab_analysis"))
        self.tab_widget.addTab(self.tab_batch, _("tab_batch"))

        self.splitter.addWidget(self.tab_widget)
        self.splitter.setSizes([760, 520])
        main_layout.addWidget(self.splitter, 1)

    def _setup_menus(self) -> None:
        mb = self.menuBar()
        mb.clear()

        # 1. Dosya Menüsü
        self.file_menu = mb.addMenu(_("menu_file"))

        self.act_open = QAction(_("action_open"), self)
        self.act_open.setShortcut(QKeySequence("Ctrl+O"))
        self.act_open.triggered.connect(self.action_open_file)
        self.file_menu.addAction(self.act_open)

        self.act_save = QAction(_("action_save_as"), self)
        self.act_save.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save.triggered.connect(self.action_save_file)
        self.file_menu.addAction(self.act_save)

        self.file_menu.addSeparator()

        self.act_close = QAction(_("action_close"), self)
        self.act_close.setShortcut(QKeySequence("Ctrl+W"))
        self.act_close.triggered.connect(self.action_close_image)
        self.file_menu.addAction(self.act_close)

        self.act_quit = QAction(_("action_quit"), self)
        self.act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_quit.triggered.connect(QApplication.instance().quit)
        self.file_menu.addAction(self.act_quit)

        # 2. Düzen Menüsü
        self.edit_menu = mb.addMenu(_("menu_edit"))

        self.act_undo = QAction(_("action_undo"), self)
        self.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.act_undo.triggered.connect(self.undo)
        self.act_undo.setEnabled(len(self._undo_stack) > 1)
        self.edit_menu.addAction(self.act_undo)

        self.act_redo = QAction(_("action_redo"), self)
        self.act_redo.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.act_redo.triggered.connect(self.redo)
        self.act_redo.setEnabled(len(self._redo_stack) > 0)
        self.edit_menu.addAction(self.act_redo)

        self.edit_menu.addSeparator()

        self.act_reset = QAction(_("action_reset"), self)
        self.act_reset.setShortcut(QKeySequence("Ctrl+R"))
        self.act_reset.triggered.connect(self.action_reset_to_original)
        self.edit_menu.addAction(self.act_reset)

        self.act_copy = QAction(_("action_copy"), self)
        self.act_copy.setShortcut(QKeySequence("Ctrl+C"))
        self.act_copy.triggered.connect(self.action_copy_image)
        self.edit_menu.addAction(self.act_copy)

        # 3. Görünüm Menüsü
        self.view_menu = mb.addMenu(_("menu_view"))

        self.act_zoom_in = QAction(_("action_zoom_in"), self)
        self.act_zoom_in.setShortcut(QKeySequence("Ctrl++"))
        self.act_zoom_in.triggered.connect(self.image_viewer.zoom_in)
        self.view_menu.addAction(self.act_zoom_in)

        self.act_zoom_out = QAction(_("action_zoom_out"), self)
        self.act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        self.act_zoom_out.triggered.connect(self.image_viewer.zoom_out)
        self.view_menu.addAction(self.act_zoom_out)

        self.act_fit = QAction(_("action_fit"), self)
        self.act_fit.setShortcut(QKeySequence("Ctrl+0"))
        self.act_fit.triggered.connect(self.image_viewer.fit_to_window)
        self.view_menu.addAction(self.act_fit)

        # 4. Dil Menüsü
        self.lang_menu = mb.addMenu(_("menu_language"))
        lang_group = QActionGroup(self)

        self.act_lang_tr = QAction("Türkçe", self, checkable=True)
        self.act_lang_tr.setChecked(i18n.current_lang == "tr")
        self.act_lang_tr.triggered.connect(lambda: i18n.set_language("tr"))
        lang_group.addAction(self.act_lang_tr)
        self.lang_menu.addAction(self.act_lang_tr)

        self.act_lang_en = QAction("English", self, checkable=True)
        self.act_lang_en.setChecked(i18n.current_lang == "en")
        self.act_lang_en.triggered.connect(lambda: i18n.set_language("en"))
        lang_group.addAction(self.act_lang_en)
        self.lang_menu.addAction(self.act_lang_en)

        # 5. Yardım Menüsü
        self.help_menu = mb.addMenu(_("menu_help"))

        self.act_shortcuts = QAction(_("action_shortcuts"), self)
        self.act_shortcuts.triggered.connect(lambda: ShortcutsDialog(self).exec())
        self.help_menu.addAction(self.act_shortcuts)

        self.act_about = QAction(_("action_about"), self)
        self.act_about.triggered.connect(lambda: AboutDialog(self).exec())
        self.help_menu.addAction(self.act_about)

    def _setup_status_bar(self) -> None:
        sb = self.statusBar()

        self.status_msg_label = QLabel(_("status_ready"))
        self.status_msg_label.setStyleSheet("color: #F8FAFC; font-weight: 500;")
        sb.addWidget(self.status_msg_label, 1)

        self.status_dim_label = QLabel("")
        sb.addPermanentWidget(self.status_dim_label)

        self.status_size_label = QLabel("")
        sb.addPermanentWidget(self.status_size_label)

        self.status_format_label = QLabel("")
        sb.addPermanentWidget(self.status_format_label)

        self.status_progress = QProgressBar()
        self.status_progress.setFixedSize(120, 14)
        self.status_progress.setVisible(False)
        sb.addPermanentWidget(self.status_progress)

    def load_image(self, file_path: str) -> None:
        """Görseli dosyadan açarak tüm arayüze dağıtır."""
        try:
            ctx = ImageContext.from_file(file_path)
            self._original_context = ctx
            self._committed_context = ctx.clone()
            self._current_result_context = ctx.clone()
            self._current_file_path = file_path
            self._undo_stack = [ctx.clone()]
            self._redo_stack = []

            # Görsel görüntüleyiciye bağlamları ver ve yığıt ekranını değiştir
            self.image_viewer.set_contexts(self._original_context, self._current_result_context)
            self.left_stack.setCurrentIndex(1)
            self.image_viewer.fit_to_window()

            # Sekmelere bağlamı gönder ve durum çubuğunu güncelle
            self._update_all_contexts(self._committed_context)
            self._update_status_info(self._committed_context)
            self._update_undo_redo_actions()

            size_kb = Path(file_path).stat().st_size / 1024.0
            self.status_msg_label.setText(
                _("status_image_loaded", name=Path(file_path).name, width=ctx.width, height=ctx.height, size_kb=size_kb)
            )
            self.show_notification(f"Görsel başarıyla açıldı: {Path(file_path).name}", "success")
        except Exception as e:
            self.show_notification(f"Görsel açılırken hata: {e}", "error")

    def push_history_state(self, new_context: ImageContext, message: str = "") -> None:
        """Yeni bir işlemi geri alma (undo) yığınına kaydeder ve tüm sekmelere yayar."""
        self._committed_context = new_context.clone()
        self._current_result_context = new_context.clone()
        self._undo_stack.append(new_context.clone())
        if len(self._undo_stack) > 30:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

        self._update_all_contexts(self._committed_context)
        self.image_viewer.update_result(self._committed_context)
        self._update_status_info(self._committed_context)
        self._update_undo_redo_actions()
        if message:
            self.show_notification(message, "success")

    def undo(self) -> None:
        """Son işlemi veya aktif önizlemeyi geri alır (Ctrl+Z)."""
        # Aktif sabitlenmemiş bir canlı önizleme varsa önce onu sıfırla
        if (
            self._committed_context is not None
            and self._current_result_context is not None
            and len(self._undo_stack) >= 1
            and self._current_result_context.history != self._committed_context.history
        ):
            self._current_result_context = self._committed_context.clone()
            self.image_viewer.update_result(self._current_result_context)
            self._update_status_info(self._current_result_context)
            self.tab_effects._live_timer.stop()
            self.tab_adjust._live_timer.stop()
            self.show_notification(_("status_effect_cleared"), "info")
            return

        if len(self._undo_stack) <= 1:
            self.show_notification(_("status_no_more_undo"), "info")
            return

        current_state = self._undo_stack.pop()
        self._redo_stack.append(current_state)
        prev_state = self._undo_stack[-1].clone()

        self._committed_context = prev_state.clone()
        self._current_result_context = prev_state.clone()
        self._update_all_contexts(self._committed_context)
        self.image_viewer.update_result(self._committed_context)
        self._update_status_info(self._committed_context)
        self._update_undo_redo_actions()
        remaining = len(self._undo_stack) - 1
        self.show_notification(f"{_('status_undo')} (Adım: {remaining})", "info")

    def redo(self) -> None:
        """Geri alınan işlemi ileri alır (Ctrl+Y / Ctrl+Shift+Z)."""
        if not self._redo_stack:
            self.show_notification(_("status_no_more_redo"), "info")
            return

        next_state = self._redo_stack.pop()
        self._undo_stack.append(next_state.clone())

        self._committed_context = next_state.clone()
        self._current_result_context = next_state.clone()
        self._update_all_contexts(self._committed_context)
        self.image_viewer.update_result(self._committed_context)
        self._update_status_info(self._committed_context)
        self._update_undo_redo_actions()
        remaining = len(self._undo_stack) - 1
        self.show_notification(f"{_('status_redo')} (Adım: {remaining})", "info")

    def _update_all_contexts(self, ctx: Optional[ImageContext]) -> None:
        if ctx is None:
            return
        self.tab_compress.set_context(ctx)
        self.tab_adjust.set_context(ctx)
        self.tab_effects.set_context(ctx)
        self.tab_watermark.set_context(ctx)
        self.tab_analysis.set_context(ctx)

    def _update_status_info(self, ctx: Optional[ImageContext]) -> None:
        if ctx is None:
            return
        self.status_dim_label.setText(f"{ctx.width} × {ctx.height} px")
        raw_b = len(ctx.to_bytes(ctx.source_format))
        self.status_size_label.setText(f"{raw_b / 1024.0:.1f} KB")
        self.status_format_label.setText(f"{ctx.source_format}")

    def _update_undo_redo_actions(self) -> None:
        if hasattr(self, "act_undo"):
            self.act_undo.setEnabled(len(self._undo_stack) > 1)
        if hasattr(self, "act_redo"):
            self.act_redo.setEnabled(len(self._redo_stack) > 0)

    def action_open_file(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            _("dialog_open_title"),
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*)",
        )
        if path:
            self.load_image(path)

    def action_save_file(self) -> None:
        if self._current_result_context is None:
            self.show_notification("Kaydedilecek işlenmiş görsel bulunamadı.", "warning")
            return

        default_name = "output.webp"
        if self._current_file_path:
            p = Path(self._current_file_path)
            default_name = f"{p.stem}_processed.webp"

        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("dialog_save_title"),
            default_name,
            "WebP Image (*.webp);;JPEG Image (*.jpg *.jpeg);;PNG Image (*.png);;All Files (*)",
        )
        if save_path:
            try:
                ext = Path(save_path).suffix.lstrip(".").upper() or "WEBP"
                self._current_result_context.save(save_path, format=ext)
                self.show_notification(_("status_saved", path=Path(save_path).name), "success")
            except Exception as e:
                self.show_notification(f"Kayıt hatası: {e}", "error")

    def action_reset_to_original(self) -> None:
        if self._original_context is None:
            return
        self.push_history_state(self._original_context.clone(), _("status_reset"))

    def action_close_image(self) -> None:
        self._original_context = None
        self._committed_context = None
        self._current_result_context = None
        self._current_file_path = None
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_undo_redo_actions()
        self.left_stack.setCurrentIndex(0)
        self.status_dim_label.setText("")
        self.status_size_label.setText("")
        self.status_format_label.setText("")
        self.status_msg_label.setText(_("status_ready"))

    def action_copy_image(self) -> None:
        if self._current_result_context is None:
            return
        pix = self.image_viewer.res_label.pixmap()
        if pix:
            QApplication.clipboard().setPixmap(pix)
            self.show_notification("Görsel panoya kopyalandı!", "info")

    def _on_result_updated(self, new_context: ImageContext) -> None:
        """Canlı önizleme güncellemesi (Geri alma yığınını şişirmez)."""
        self._current_result_context = new_context
        self.image_viewer.update_result(new_context)
        self._update_status_info(new_context)
        if self._committed_context is not None and new_context.history == self._committed_context.history:
            self.show_notification(_("status_effect_cleared"), "info")
        else:
            op_name = new_context.history[-1] if new_context.history else "İşlem"
            self.show_notification(f"'{op_name}' önizleniyor...", "info")

    def _on_committed_updated(self, new_context: ImageContext) -> None:
        """Kalıcı işlem güncellemesi (Geri alma yığınına eklenir)."""
        op_name = new_context.history[-1] if new_context.history else "İşlem"
        self.push_history_state(new_context, f"'{op_name}' uygulandı. (Geri almak için Ctrl+Z)")

    def _on_effect_committed(self, new_context: ImageContext) -> None:
        """Efekt sabitleme (Geri alma yığınına eklenir)."""
        self.push_history_state(new_context, _("status_effect_committed"))

    def show_notification(self, text: str, msg_type: str = "success") -> None:
        self.notification_badge.show_message(text, msg_type)
        self.status_msg_label.setText(text)

    def _on_language_changed(self, lang: str) -> None:
        """Dil değiştiğinde tüm başlıkları ve arayüz metinlerini anında günceller."""
        self._setup_menus()
        self.drop_zone.retranslate()
        self.image_viewer.retranslate()
        self.tab_compress.retranslate()
        self.tab_adjust.retranslate()
        self.tab_effects.retranslate()
        self.tab_watermark.retranslate()
        self.tab_analysis.retranslate()
        self.tab_batch.retranslate()
        self.tab_widget.setTabText(0, _("tab_compress"))
        self.tab_widget.setTabText(1, _("tab_adjust"))
        self.tab_widget.setTabText(2, _("tab_effects"))
        self.tab_widget.setTabText(3, _("tab_watermark"))
        self.tab_widget.setTabText(4, _("tab_analysis"))
        self.tab_widget.setTabText(5, _("tab_batch"))
        msg = "Dil değiştirildi: Türkçe" if lang == "tr" else "Language switched: English"
        self.show_notification(msg, "info")
