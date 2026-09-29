"""Toplu İşlem Sekmesi (Batch Processing Runner Tab)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.i18n import _
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.operations import (
    ArtisticPresetsOperation,
    ExifToolOperation,
    FormatConverterOperation,
    ResizeOperation,
    TargetSizeCompressorOperation,
)
from image_toolbox.services.batch_runner import BatchProcessingRunner


class BatchWorkerThread(QThread):
    """Arayüzü dondurmadan arka planda çalışan toplu işlem iş parçacığı."""

    progress = pyqtSignal(int, int, str, bool, float)
    finished_batch = pyqtSignal(int, int, float)

    def __init__(self, in_dir: Path, out_dir: Path, pipeline: PipelineEngine, workers: int) -> None:
        super().__init__()
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.pipeline = pipeline
        self.workers = workers

    def run(self) -> None:
        runner = BatchProcessingRunner(max_workers=self.workers)

        def on_item_done(completed: int, total: int, item_res) -> None:
            self.progress.emit(
                completed,
                total,
                item_res.input_path.name,
                item_res.success,
                item_res.duration,
            )

        results = runner.run(
            input_dir=self.in_dir,
            output_dir=self.out_dir,
            pipeline=self.pipeline,
            progress_callback=on_item_done,
        )

        success_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)
        total_time = sum(r.duration for r in results)
        self.finished_batch.emit(success_count, failed_count, total_time)


class BatchTab(QWidget):
    """Klasör bazlı paralel toplu görsel işleme sekmesi."""

    status_requested = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker_thread: Optional[BatchWorkerThread] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Klasör Seçim Grubu
        self.dir_group = QGroupBox(_("group_batch_dirs"))
        dir_layout = QGridLayout(self.dir_group)
        dir_layout.setSpacing(8)

        # Kaynak Klasör
        self.in_dir_lbl = QLabel(_("label_in_dir"))
        dir_layout.addWidget(self.in_dir_lbl, 0, 0)
        self.in_dir_edit = QLineEdit()
        self.in_dir_edit.setPlaceholderText("...")
        dir_layout.addWidget(self.in_dir_edit, 0, 1)
        self.in_browse_btn = QPushButton(_("btn_browse"))
        self.in_browse_btn.clicked.connect(self._browse_in_dir)
        dir_layout.addWidget(self.in_browse_btn, 0, 2)

        # Hedef Klasör
        self.out_dir_lbl = QLabel(_("label_out_dir"))
        dir_layout.addWidget(self.out_dir_lbl, 1, 0)
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setPlaceholderText("...")
        dir_layout.addWidget(self.out_dir_edit, 1, 1)
        self.out_browse_btn = QPushButton(_("btn_browse"))
        self.out_browse_btn.clicked.connect(self._browse_out_dir)
        dir_layout.addWidget(self.out_browse_btn, 1, 2)

        layout.addWidget(self.dir_group)

        # 2. İşlem Seçimi ve Ayarlar
        self.op_group = QGroupBox(_("group_batch_op"))
        op_layout = QGridLayout(self.op_group)
        op_layout.setSpacing(10)

        self.op_label = QLabel(_("label_operation"))
        op_layout.addWidget(self.op_label, 0, 0)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Akıllı Sıkıştırma (WebP 350 KB)",
            "WebP Formatına Dönüştür (Kalite %85)",
            "En-Boy Oranlı Boyutlandır (1920x1080 Fit)",
            "Tüm EXIF ve Kişisel Bilgileri Sil",
            "Sanatsal Vintage Film Efekti",
        ])
        op_layout.addWidget(self.preset_combo, 0, 1)

        self.workers_lbl = QLabel(_("label_workers"))
        op_layout.addWidget(self.workers_lbl, 1, 0)
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(4)
        op_layout.addWidget(self.workers_spin, 1, 1)

        layout.addWidget(self.op_group)

        # 3. Başlat Butonu ve İlerleme
        self.start_btn = QPushButton(_("btn_run_batch"))
        self.start_btn.setProperty("primary", True)
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start_batch)
        layout.addWidget(self.start_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 4. Canlı İşlem Günlüğü Tablosu
        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels([_("header_file"), _("header_status"), _("header_duration")])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.log_table, 1)

    def _browse_in_dir(self) -> None:
        p = QFileDialog.getExistingDirectory(self, _("dialog_batch_in_title"))
        if p:
            self.in_dir_edit.setText(p)

    def _browse_out_dir(self) -> None:
        p = QFileDialog.getExistingDirectory(self, _("dialog_batch_out_title"))
        if p:
            self.out_dir_edit.setText(p)

    def _start_batch(self) -> None:
        in_p = Path(self.in_dir_edit.text().strip())
        out_p = Path(self.out_dir_edit.text().strip())

        if not in_p.exists() or not in_p.is_dir():
            self.status_requested.emit("Lütfen geçerli bir kaynak klasör seçin.", "error")
            return
        if not out_p:
            out_p = in_p / "processed"
            self.out_dir_edit.setText(str(out_p))

        # Pipeline hazırla
        idx = self.preset_combo.currentIndex()
        pipeline = PipelineEngine()
        if idx == 0:
            pipeline.add(TargetSizeCompressorOperation(target_size="350kb", format="WEBP"))
        elif idx == 1:
            pipeline.add(FormatConverterOperation(format="WEBP", quality=85))
        elif idx == 2:
            pipeline.add(ResizeOperation(width=1920, height=1080, mode="fit"))
        elif idx == 3:
            pipeline.add(ExifToolOperation(action="strip_all"))
        elif idx == 4:
            pipeline.add(ArtisticPresetsOperation(preset="vintage", intensity=1.0))

        self.start_btn.setEnabled(False)
        self.log_table.setRowCount(0)
        self.progress_bar.setValue(0)

        self._worker_thread = BatchWorkerThread(in_p, out_p, pipeline, self.workers_spin.value())
        self._worker_thread.progress.connect(self._on_item_progress)
        self._worker_thread.finished_batch.connect(self._on_batch_finished)
        self._worker_thread.start()

    def _on_item_progress(self, completed: int, total: int, filename: str, success: bool, duration: float) -> None:
        pct = int(completed / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)

        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        self.log_table.setItem(row, 0, QTableWidgetItem(filename))
        status_item = QTableWidgetItem("Başarılı" if success else "Hata")
        status_item.setForeground(Qt.GlobalColor.green if success else Qt.GlobalColor.red)
        self.log_table.setItem(row, 1, status_item)
        self.log_table.setItem(row, 2, QTableWidgetItem(f"{duration:.2f}s"))
        self.log_table.scrollToBottom()

    def _on_batch_finished(self, successes: int, failures: int, total_time: float) -> None:
        self.start_btn.setEnabled(True)
        self.status_requested.emit(
            f"Toplu işlem bitti: {successes} başarılı, {failures} hatalı ({total_time:.2f}s)",
            "success" if failures == 0 else "warning",
        )

    def retranslate(self) -> None:
        self.dir_group.setTitle(_("group_batch_dirs"))
        self.in_dir_lbl.setText(_("label_in_dir"))
        self.out_dir_lbl.setText(_("label_out_dir"))
        self.in_browse_btn.setText(_("btn_browse"))
        self.out_browse_btn.setText(_("btn_browse"))
        self.op_group.setTitle(_("group_batch_op"))
        self.op_label.setText(_("label_operation"))
        self.workers_lbl.setText(_("label_workers"))
        self.start_btn.setText(_("btn_run_batch"))
        self.log_table.setHorizontalHeaderLabels([_("header_file"), _("header_status"), _("header_duration")])

