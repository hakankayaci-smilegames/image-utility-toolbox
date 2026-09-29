"""Toplu İşlem Motoru (Batch Processing Runner).

Klasördeki yüzlerce görseli paralel (ProcessPool/ThreadPool) olarak pipeline'dan geçirir.
Bozuk veya hatalı görseller süreci durdurmaz (Failure Isolation).
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Callable, List, Optional, Set, Union

from image_toolbox.core.context import ImageContext
from image_toolbox.core.pipeline import PipelineEngine


SUPPORTED_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"
}


@dataclass
class BatchItemResult:
    """Tek bir dosyanın toplu işlem sonucu."""
    input_path: Path
    output_path: Optional[Path]
    success: bool
    error: Optional[str] = None
    duration: float = 0.0


def _process_single_file(
    input_path: Path,
    output_path: Path,
    recipe_dict_or_path: Union[str, Path, list],
    save_format: Optional[str] = None,
) -> BatchItemResult:
    """Bağımsız süreçte çalışabilecek dosya işleme fonksiyonu."""
    start = time.perf_counter()
    try:
        pipeline = PipelineEngine.from_recipe(recipe_dict_or_path)
        ctx = ImageContext.from_file(input_path)
        res_ctx = pipeline.execute(ctx)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        res_ctx.save(output_path, format=save_format)
        duration = time.perf_counter() - start
        return BatchItemResult(
            input_path=input_path,
            output_path=output_path,
            success=True,
            duration=duration,
        )
    except Exception as e:
        duration = time.perf_counter() - start
        return BatchItemResult(
            input_path=input_path,
            output_path=output_path,
            success=False,
            error=str(e),
            duration=duration,
        )


class BatchProcessingRunner:
    """Paralel toplu işlem yöneticisi."""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = False,
    ) -> None:
        self.max_workers = max_workers
        self.use_processes = use_processes

    def run(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        pipeline: PipelineEngine,
        recursive: bool = True,
        preserve_hierarchy: bool = True,
        save_format: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, BatchItemResult], None]] = None,
    ) -> List[BatchItemResult]:
        """Klasördeki tüm görsellere boru hattını uygular."""
        in_dir = Path(input_dir)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Dosyaları topla
        pattern = "**/*" if recursive else "*"
        all_files = [
            f for f in in_dir.glob(pattern)
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        total = len(all_files)
        results: List[BatchItemResult] = []

        if total == 0:
            return results

        # 2. İş havuzunu başlat
        executor_cls = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        with executor_cls(max_workers=self.max_workers) as executor:
            future_to_file = {}

            for f in all_files:
                if preserve_hierarchy:
                    rel_path = f.relative_to(in_dir)
                    dest_path = out_dir / rel_path
                else:
                    dest_path = out_dir / f.name

                if save_format:
                    dest_path = dest_path.with_suffix(f".{save_format.lower()}")

                future = executor.submit(
                    self._execute_single_in_thread,
                    f,
                    dest_path,
                    pipeline,
                    save_format,
                )
                future_to_file[future] = f

            completed_count = 0
            for future in as_completed(future_to_file):
                item_res = future.result()
                results.append(item_res)
                completed_count += 1
                if progress_callback:
                    try:
                        progress_callback(completed_count, total, item_res)
                    except Exception:
                        pass

        return results

    @staticmethod
    def _execute_single_in_thread(
        input_path: Path,
        output_path: Path,
        pipeline: PipelineEngine,
        save_format: Optional[str],
    ) -> BatchItemResult:
        start = time.perf_counter()
        try:
            ctx = ImageContext.from_file(input_path)
            res_ctx = pipeline.execute(ctx)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            res_ctx.save(output_path, format=save_format)
            duration = time.perf_counter() - start
            return BatchItemResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                duration=duration,
            )
        except Exception as e:
            duration = time.perf_counter() - start
            return BatchItemResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                error=str(e),
                duration=duration,
            )
