"""Görsel Görüntüleyici ve İnteraktif Tuval Bileşeni (Interactive Canvas & Image Viewer).

Photoshop standartlarında fare ile serbest pan/gezinti (orta tuş veya sol tık sürükleme),
imleç odaklı pürüzsüz fare tekerleği yakınlaştırma (cursor-centered zoom),
çift tıklamayla pencereye sığdırma ve bölünmüş modda senkronize gezinti.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
from PIL import Image
from PyQt6.QtCore import QEvent, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import (
    QCursor,
    QDragEnterEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPixmap,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _


def pil_to_pixmap(pil_img: Image.Image) -> QPixmap:
    """PIL Image nesnesini yüksek verimle QPixmap'e dönüştürür."""
    bio = io.BytesIO()
    # Hızlı ve kayıpsız PNG formatında RAM buffer'a yaz
    pil_img.save(bio, format="PNG")
    data = bio.getvalue()
    pix = QPixmap()
    pix.loadFromData(data)
    return pix


class ScaledImageLabel(QLabel):
    """Piksel orantısını koruyan ve zoom destekleyen görsel etiketi."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._pixmap: Optional[QPixmap] = None
        self._scale: float = 1.0

    def set_pixmap(self, pix: QPixmap) -> None:
        self._pixmap = pix
        self.update_display()

    def set_zoom(self, scale: float) -> None:
        self._scale = max(0.02, min(50.0, scale))
        self.update_display()

    def update_display(self) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            self.clear()
            self.setFixedSize(0, 0)
            return
        target_w = max(1, int(self._pixmap.width() * self._scale))
        target_h = max(1, int(self._pixmap.height() * self._scale))
        scaled = self._pixmap.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)
        self.setFixedSize(target_w, target_h)


class InteractiveCanvasScrollArea(QScrollArea):
    """Photoshop benzeri tuval gezintisi (Pan, Move, Zoom, Space-drag) sunan kaydırma alanı."""

    zoom_requested = pyqtSignal(float, QPoint)  # (factor, mouse_pos)
    pan_changed = pyqtSignal(int, int)          # (h_value, v_value)
    double_click_reset = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

        self._is_panning = False
        self._pan_origin_global: Optional[QPoint] = None
        self._pan_button: Optional[Qt.MouseButton] = None
        self._space_down = False

    def setWidget(self, widget: Optional[QWidget]) -> None:
        super().setWidget(widget)
        if widget is not None:
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

    def eventFilter(self, watched, event: QEvent) -> bool:
        etype = event.type()
        if etype == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
            if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
                self._is_panning = True
                self._pan_button = event.button()
                self._pan_origin_global = event.globalPosition().toPoint()
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                if self.widget():
                    self.widget().setCursor(Qt.CursorShape.ClosedHandCursor)
                return True

        elif etype == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            if self._is_panning and self._pan_origin_global is not None:
                cur = event.globalPosition().toPoint()
                delta = cur - self._pan_origin_global
                self._pan_origin_global = cur
                h_bar = self.horizontalScrollBar()
                v_bar = self.verticalScrollBar()
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
                self.pan_changed.emit(h_bar.value(), v_bar.value())
                return True

        elif etype == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
            if self._is_panning and event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
                self._is_panning = False
                self._pan_origin_global = None
                self._pan_button = None
                cursor = Qt.CursorShape.OpenHandCursor if self._space_down else Qt.CursorShape.ArrowCursor
                self.viewport().setCursor(cursor)
                if self.widget():
                    self.widget().setCursor(cursor)
                return True

        elif etype == QEvent.Type.MouseButtonDblClick and isinstance(event, QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                self.double_click_reset.emit()
                return True

        elif etype == QEvent.Type.Wheel and isinstance(event, QWheelEvent):
            delta = event.angleDelta().y()
            if delta != 0:
                factor = 1.15 if delta > 0 else (1.0 / 1.15)
                viewport_pos = self.viewport().mapFromGlobal(event.globalPosition().toPoint())
                self.zoom_requested.emit(factor, viewport_pos)
                return True

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._is_panning = True
            self._pan_button = event.button()
            self._pan_origin_global = event.globalPosition().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            if self.widget():
                self.widget().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning and self._pan_origin_global is not None:
            cur = event.globalPosition().toPoint()
            delta = cur - self._pan_origin_global
            self._pan_origin_global = cur
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            self.pan_changed.emit(h_bar.value(), v_bar.value())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._is_panning and event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._is_panning = False
            self._pan_origin_global = None
            self._pan_button = None
            cursor = Qt.CursorShape.OpenHandCursor if self._space_down else Qt.CursorShape.ArrowCursor
            self.viewport().setCursor(cursor)
            if self.widget():
                self.widget().setCursor(cursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta != 0:
            factor = 1.15 if delta > 0 else (1.0 / 1.15)
            self.zoom_requested.emit(factor, event.position().toPoint())
            event.accept()
            return
        super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_click_reset.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down = True
            if not self._is_panning:
                self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
                if self.widget():
                    self.widget().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down = False
            if not self._is_panning:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                if self.widget():
                    self.widget().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)


class ImageViewerWidget(QWidget):
    """Görselleri gösteren, yakınlaştıran ve orijinal/sonuç karşılaştırması sunan bileşen."""

    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._orig_context: Optional[ImageContext] = None
        self._res_context: Optional[ImageContext] = None
        self._orig_pixmap: Optional[QPixmap] = None
        self._res_pixmap: Optional[QPixmap] = None
        self._zoom: float = 1.0
        self._auto_fit: bool = True
        self._syncing_scroll: bool = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Üst Araç Çubuğu (Görünüm Modları ve Zoom)
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 6px;")
        toolbar.setFixedHeight(40)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(6)

        # Karşılaştırma butonları grubu
        self.btn_group = QButtonGroup(self)
        self.orig_btn = QPushButton(_("view_original"))
        self.orig_btn.setCheckable(True)
        self.res_btn = QPushButton(_("view_result"))
        self.res_btn.setCheckable(True)
        self.res_btn.setChecked(True)
        self.split_btn = QPushButton(_("view_split"))
        self.split_btn.setCheckable(True)

        for btn in (self.orig_btn, self.res_btn, self.split_btn):
            btn.setFixedHeight(26)
            self.btn_group.addButton(btn)
            tb_layout.addWidget(btn)

        self.orig_btn.clicked.connect(self._on_view_mode_changed)
        self.res_btn.clicked.connect(self._on_view_mode_changed)
        self.split_btn.clicked.connect(self._on_view_mode_changed)

        tb_layout.addStretch(1)

        # Zoom Kontrolleri
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(28, 26)
        self.zoom_out_btn.setToolTip(_("action_zoom_out"))
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        tb_layout.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #A1A1AA; font-weight: 600; min-width: 54px; text-align: center;")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_label.setToolTip("100% / Fit")
        self.zoom_label.mousePressEvent = lambda e: self.reset_zoom_100()
        tb_layout.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(28, 26)
        self.zoom_in_btn.setToolTip(_("action_zoom_in"))
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        tb_layout.addWidget(self.zoom_in_btn)

        self.fit_btn = QPushButton("Fit")
        self.fit_btn.setFixedSize(40, 26)
        self.fit_btn.setToolTip(_("action_fit"))
        self.fit_btn.clicked.connect(self.fit_to_window)
        tb_layout.addWidget(self.fit_btn)

        main_layout.addWidget(toolbar)

        # Görsel Alanı (Tekli Görünüm ve Splitter Görünüm)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #27272A; width: 2px; }")

        # Sol/Orijinal Tuval
        self.orig_scroll = InteractiveCanvasScrollArea()
        self.orig_scroll.setStyleSheet("background-color: #0E0E10; border: 1px solid #27272A; border-radius: 6px;")
        self.orig_label = ScaledImageLabel()
        self.orig_scroll.setWidget(self.orig_label)

        # Sağ/Sonuç Tuval
        self.res_scroll = InteractiveCanvasScrollArea()
        self.res_scroll.setStyleSheet("background-color: #0E0E10; border: 1px solid #27272A; border-radius: 6px;")
        self.res_label = ScaledImageLabel()
        self.res_scroll.setWidget(self.res_label)

        # İnteraktif Sinyal Bağlantıları (Photoshop-like Zoom & Pan)
        self.orig_scroll.zoom_requested.connect(
            lambda factor, pos: self._on_interactive_zoom(factor, pos, self.orig_scroll)
        )
        self.res_scroll.zoom_requested.connect(
            lambda factor, pos: self._on_interactive_zoom(factor, pos, self.res_scroll)
        )
        self.orig_scroll.double_click_reset.connect(self.fit_to_window)
        self.res_scroll.double_click_reset.connect(self.fit_to_window)

        # Bölünmüş mod senkronize kaydırma
        self.orig_scroll.pan_changed.connect(
            lambda h, v: self._sync_scroll(self.orig_scroll, self.res_scroll, h, v)
        )
        self.res_scroll.pan_changed.connect(
            lambda h, v: self._sync_scroll(self.res_scroll, self.orig_scroll, h, v)
        )

        self.splitter.addWidget(self.orig_scroll)
        self.splitter.addWidget(self.res_scroll)
        main_layout.addWidget(self.splitter, 1)

        self._on_view_mode_changed()

    def _sync_scroll(self, source: InteractiveCanvasScrollArea, target: InteractiveCanvasScrollArea, h: int, v: int) -> None:
        """Bölünmüş modda her iki tuvalin kaydırma pozisyonunu senkronize eder."""
        if not self.split_btn.isChecked() or self._syncing_scroll:
            return
        self._syncing_scroll = True
        target.horizontalScrollBar().setValue(h)
        target.verticalScrollBar().setValue(v)
        self._syncing_scroll = False

    def _on_interactive_zoom(self, factor: float, mouse_pos: QPoint, source_scroll: InteractiveCanvasScrollArea) -> None:
        """İmleç odaklı yakınlaştırma (Cursor-centered smooth zoom)."""
        old_zoom = self._zoom
        new_zoom = max(0.02, min(50.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-4:
            return
        self._auto_fit = False

        h_bar = source_scroll.horizontalScrollBar()
        v_bar = source_scroll.verticalScrollBar()

        # İmlecin tuval içeriğindeki mutlak koordinatı
        vx = mouse_pos.x()
        vy = mouse_pos.y()
        cx = h_bar.value() + vx
        cy = v_bar.value() + vy

        # Yeni zoomu uygula
        ratio = new_zoom / old_zoom
        self._zoom = new_zoom
        self._apply_zoom()

        # Yeni kaydırma pozisyonunu imlecin altındaki piksel sabit kalacak şekilde ayarla
        new_h = int(cx * ratio - vx)
        new_v = int(cy * ratio - vy)
        h_bar.setValue(new_h)
        v_bar.setValue(new_v)

        # Karşı tarafa da senkronize et
        other_scroll = self.res_scroll if source_scroll == self.orig_scroll else self.orig_scroll
        if self.split_btn.isChecked():
            other_scroll.horizontalScrollBar().setValue(new_h)
            other_scroll.verticalScrollBar().setValue(new_v)

    def set_contexts(self, original: Optional[ImageContext], result: Optional[ImageContext] = None) -> None:
        """Görsel bağlamlarını günceller ve pikselleri hazırlar."""
        self._orig_context = original
        self._res_context = result or original

        if self._orig_context is not None:
            self._orig_pixmap = pil_to_pixmap(self._orig_context.pil_image)
            self.orig_label.set_pixmap(self._orig_pixmap)

        if self._res_context is not None:
            self._res_pixmap = pil_to_pixmap(self._res_context.pil_image)
            self.res_label.set_pixmap(self._res_pixmap)

        self.fit_to_window()

    def update_result(self, result: ImageContext) -> None:
        """Sadece işlenmiş sonucu günceller (Canlı önizleme için optimize edilmiştir)."""
        self._res_context = result
        self._res_pixmap = pil_to_pixmap(result.pil_image)
        self.res_label.set_pixmap(self._res_pixmap)
        # Zoomu ve konumu bozmadan yalnızca pikselleri tazele
        self.res_label.set_zoom(self._zoom)

    def _on_view_mode_changed(self) -> None:
        if self.orig_btn.isChecked():
            self.orig_scroll.setVisible(True)
            self.res_scroll.setVisible(False)
        elif self.res_btn.isChecked():
            self.orig_scroll.setVisible(False)
            self.res_scroll.setVisible(True)
        elif self.split_btn.isChecked():
            self.orig_scroll.setVisible(True)
            self.res_scroll.setVisible(True)
            self.splitter.setSizes([self.width() // 2, self.width() // 2])

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.fit_to_window()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if getattr(self, "_auto_fit", True):
            self.fit_to_window()

    def zoom_in(self) -> None:
        center = QPoint(self.res_scroll.viewport().width() // 2, self.res_scroll.viewport().height() // 2)
        active_scroll = self.orig_scroll if self.orig_btn.isChecked() else self.res_scroll
        self._on_interactive_zoom(1.25, center, active_scroll)

    def zoom_out(self) -> None:
        center = QPoint(self.res_scroll.viewport().width() // 2, self.res_scroll.viewport().height() // 2)
        active_scroll = self.orig_scroll if self.orig_btn.isChecked() else self.res_scroll
        self._on_interactive_zoom(1.0 / 1.25, center, active_scroll)

    def reset_zoom_100(self) -> None:
        self._auto_fit = False
        self._zoom = 1.0
        self._apply_zoom()

    def fit_to_window(self) -> None:
        self._auto_fit = True
        target_pix = self._res_pixmap or self._orig_pixmap
        if target_pix is not None and not target_pix.isNull():
            active_scroll = self.orig_scroll if self.orig_btn.isChecked() else self.res_scroll
            avail_w = max(100, active_scroll.viewport().width() - 20)
            avail_h = max(100, active_scroll.viewport().height() - 20)
            img_w = target_pix.width()
            img_h = target_pix.height()
            if img_w > 0 and img_h > 0:
                self._zoom = min(avail_w / img_w, avail_h / img_h, 1.0)
                self._apply_zoom()

    def _apply_zoom(self) -> None:
        self.orig_label.set_zoom(self._zoom)
        self.res_label.set_zoom(self._zoom)
        self.update_zoom_label()

    def update_zoom_label(self) -> None:
        pct = int(self._zoom * 100)
        self.zoom_label.setText(f"{pct}%")

    def retranslate(self) -> None:
        self.orig_btn.setText(_("view_original"))
        self.res_btn.setText(_("view_result"))
        self.split_btn.setText(_("view_split"))
        self.fit_btn.setToolTip(_("action_fit"))
        self.zoom_in_btn.setToolTip(_("action_zoom_in"))
        self.zoom_out_btn.setToolTip(_("action_zoom_out"))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ext = Path(urls[0].toLocalFile()).suffix.lower()
                if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.file_dropped.emit(urls[0].toLocalFile())
            event.acceptProposedAction()
