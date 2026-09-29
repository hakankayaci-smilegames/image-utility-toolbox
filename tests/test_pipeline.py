"""PipelineEngine Birim Testleri."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import OperationError, ValidationError
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.operations.resize import ResizeOperation
from image_toolbox.operations.vignette import VignetteOperation


def test_pipeline_chaining_and_execution(rgb_context: ImageContext) -> None:
    pipeline = PipelineEngine()
    pipeline.add(ResizeOperation(width=100, height=80, mode="fit"))
    pipeline.add(VignetteOperation(radius=0.5, opacity=0.8))

    assert len(pipeline) == 2
    res = pipeline.execute(rgb_context)

    # 200x200 görsel 100x80 içine sığdırılınca 80x80 olmalı
    assert res.size == (80, 80)
    assert "resize" in res.history
    assert "vignette" in res.history


def test_pipeline_hooks(rgb_context: ImageContext) -> None:
    pre_called = []
    post_called = []

    pipeline = PipelineEngine()
    pipeline.add_pre_hook(lambda op, ctx: pre_called.append(op.name))
    pipeline.add_post_hook(lambda op, ctx, dur: post_called.append((op.name, dur)))
    pipeline.add(ResizeOperation(width=150, mode="fit"))

    pipeline.execute(rgb_context)
    assert pre_called == ["resize"]
    assert len(post_called) == 1
    assert post_called[0][0] == "resize"
    assert post_called[0][1] >= 0.0


def test_pipeline_from_recipe(rgb_context: ImageContext, tmp_path: Path) -> None:
    recipe_data = [
        {"op": "resize", "width": 120, "height": 120, "mode": "fit"},
        {"op": "artistic", "preset": "sepia", "intensity": 0.9},
    ]
    recipe_file = tmp_path / "recipe.json"
    recipe_file.write_text(json.dumps(recipe_data))

    pipeline = PipelineEngine.from_recipe(recipe_file)
    assert len(pipeline) == 2

    res = pipeline.execute(rgb_context)
    assert res.size == (120, 120)
    assert "resize" in res.history
    assert "artistic" in res.history


def test_pipeline_invalid_recipe_raises() -> None:
    with pytest.raises(ValidationError):
        PipelineEngine.from_recipe([{"invalid": "no_op_name"}])

    with pytest.raises(ValidationError):
        PipelineEngine.from_recipe([{"op": "non_existent_op_12345"}])
