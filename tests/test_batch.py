"""BatchProcessingRunner Birim Testleri."""

from __future__ import annotations

from pathlib import Path
from PIL import Image
import pytest

from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.operations.resize import ResizeOperation
from image_toolbox.services.batch_runner import BatchProcessingRunner


def test_batch_runner_success_and_hierarchy(tmp_path: Path) -> None:
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    sub_dir = in_dir / "nested"
    sub_dir.mkdir(parents=True, exist_ok=True)

    # 3 adet geçerli görsel üret
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    img.save(in_dir / "img1.jpg")
    img.save(in_dir / "img2.png")
    img.save(sub_dir / "img3.jpg")

    pipeline = PipelineEngine()
    pipeline.add(ResizeOperation(width=50, mode="fit"))

    runner = BatchProcessingRunner(max_workers=2)
    results = runner.run(in_dir, out_dir, pipeline=pipeline, preserve_hierarchy=True)

    assert len(results) == 3
    assert all(r.success for r in results)

    # Dosya hiyerarşisi korunmuş olmalı
    assert (out_dir / "img1.jpg").exists()
    assert (out_dir / "img2.png").exists()
    assert (out_dir / "nested" / "img3.jpg").exists()

    # Boyutların 50x50 olduğunu doğrula
    out_img = Image.open(out_dir / "img1.jpg")
    assert out_img.size == (50, 50)


def test_batch_runner_failure_isolation(tmp_path: Path) -> None:
    in_dir = tmp_path / "input_corrupt"
    out_dir = tmp_path / "output_corrupt"
    in_dir.mkdir(parents=True, exist_ok=True)

    # 1 adet geçerli görsel, 1 adet bozuk dosya
    img = Image.new("RGB", (100, 100), (0, 255, 0))
    img.save(in_dir / "valid.jpg")
    (in_dir / "corrupt.jpg").write_bytes(b"INVALID_IMAGE_BYTES")

    pipeline = PipelineEngine()
    pipeline.add(ResizeOperation(width=50, mode="fit"))

    runner = BatchProcessingRunner(max_workers=2)
    results = runner.run(in_dir, out_dir, pipeline=pipeline)

    assert len(results) == 2
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].input_path.name == "corrupt.jpg"
    assert (out_dir / "valid.jpg").exists()
