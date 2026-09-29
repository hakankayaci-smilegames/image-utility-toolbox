"""Boru Hattı Yürütme Motoru (Pipeline Engine).

Birden fazla operasyonu sıralı şekilde zincirleyerek tek veya toplu görseller üzerinde çalıştırır.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Union

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import OperationError, ValidationError
from image_toolbox.core.registry import registry


class PipelineEngine:
    """Operasyonları sıralı zincirleyen ve yürüten çekirdek motor."""

    def __init__(self, operations: Optional[List[BaseOperation]] = None) -> None:
        self.operations: List[BaseOperation] = list(operations) if operations else []
        self._pre_hooks: List[Callable[[BaseOperation, ImageContext], None]] = []
        self._post_hooks: List[Callable[[BaseOperation, ImageContext, float], None]] = []

    def add(self, operation: BaseOperation) -> PipelineEngine:
        """Boru hattına yeni bir operasyon ekler (Fluent API)."""
        if not isinstance(operation, BaseOperation):
            raise TypeError("Eklenecek operasyon BaseOperation türevi olmalıdır.")
        self.operations.append(operation)
        return self

    def clear(self) -> PipelineEngine:
        """Boru hattındaki tüm operasyonları temizler."""
        self.operations.clear()
        return self

    def add_pre_hook(self, hook: Callable[[BaseOperation, ImageContext], None]) -> PipelineEngine:
        """Operasyon başlamadan önce çalışacak geri çağırma (hook) ekler."""
        self._pre_hooks.append(hook)
        return self

    def add_post_hook(self, hook: Callable[[BaseOperation, ImageContext, float], None]) -> PipelineEngine:
        """Operasyon tamamlandıktan sonra (operasyon, context, süre) çalışacak hook ekler."""
        self._post_hooks.append(hook)
        return self

    def execute(self, context: ImageContext) -> ImageContext:
        """Boru hattındaki tüm operasyonları sırayla context üzerine uygular."""
        current_ctx = context
        for op in self.operations:
            for pre_hook in self._pre_hooks:
                try:
                    pre_hook(op, current_ctx)
                except Exception:
                    pass

            start_time = time.perf_counter()
            try:
                current_ctx = op.apply(current_ctx)
            except Exception as e:
                raise OperationError(f"Operasyon yürütme hatası ({op.name}): {e}") from e
            duration = time.perf_counter() - start_time

            for post_hook in self._post_hooks:
                try:
                    post_hook(op, current_ctx, duration)
                except Exception:
                    pass

        return current_ctx

    def execute_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        save_format: Optional[str] = None,
        **save_kwargs: Any,
    ) -> ImageContext:
        """Görseli dosyadan yükler, pipeline'ı çalıştırır ve istenirse çıktı yoluna kaydeder."""
        ctx = ImageContext.from_file(input_path)
        result_ctx = self.execute(ctx)
        if output_path is not None:
            result_ctx.save(output_path, format=save_format, **save_kwargs)
        return result_ctx

    @classmethod
    def from_recipe(cls, recipe: Union[List[Dict[str, Any]], str, Path]) -> PipelineEngine:
        """Deklaratif bir liste veya JSON dosyasından otomatik pipeline oluşturur.
        
        Örnek Tarif:
        [
            {"op": "resize", "width": 800, "mode": "fit"},
            {"op": "vignette", "feather": 0.4}
        ]
        """
        engine = cls()
        items: List[Dict[str, Any]]

        if isinstance(recipe, (str, Path)):
            recipe_path = Path(recipe)
            if recipe_path.exists():
                content = recipe_path.read_text(encoding="utf-8")
                items = json.loads(content)
            else:
                items = json.loads(str(recipe))
        elif isinstance(recipe, list):
            items = recipe
        else:
            raise ValidationError("Recipe bir liste, JSON string veya dosya yolu olmalıdır.")

        for item in items:
            if not isinstance(item, dict):
                raise ValidationError(f"Geçersiz tarif adımı: {item}")
            op_name = item.get("op") or item.get("operation")
            if not op_name:
                raise ValidationError(f"Tarif adımında 'op' veya 'operation' anahtarı bulunamadı: {item}")

            params = {k: v for k, v in item.items() if k not in ("op", "operation")}
            op_instance = registry.create(str(op_name), **params)
            engine.add(op_instance)

        return engine

    def __len__(self) -> int:
        return len(self.operations)

    def __repr__(self) -> str:
        steps = " -> ".join(op.name for op in self.operations)
        return f"<PipelineEngine [{steps or 'Empty'}]>"
