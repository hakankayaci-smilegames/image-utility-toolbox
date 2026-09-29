"""CLI Komutları Birim Testleri."""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image
from typer.testing import CliRunner
import pytest

from image_toolbox.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Image Utility Toolbox" in result.stdout


def test_cli_list_ops() -> None:
    result = runner.invoke(app, ["list-ops"])
    assert result.exit_code == 0
    assert "resize" in result.stdout
    assert "compress" in result.stdout
    assert "palette" in result.stdout


def test_cli_resize(tmp_path: Path) -> None:
    in_file = tmp_path / "in.png"
    out_file = tmp_path / "out.png"
    img = Image.new("RGB", (200, 200), (255, 0, 0))
    img.save(in_file)

    result = runner.invoke(app, ["resize", str(in_file), str(out_file), "--width", "80", "--mode", "fit"])
    assert result.exit_code == 0
    assert out_file.exists()
    saved = Image.open(out_file)
    assert saved.size == (80, 80)


def test_cli_compress(tmp_path: Path) -> None:
    in_file = tmp_path / "in.jpg"
    out_file = tmp_path / "out.webp"
    img = Image.new("RGB", (300, 300), (0, 128, 255))
    img.save(in_file, format="JPEG", quality=95)

    result = runner.invoke(
        app,
        ["compress", str(in_file), str(out_file), "--target", "15kb", "--format", "WEBP"],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    assert out_file.stat().st_size <= 15 * 1024


def test_cli_inspect_json(tmp_path: Path) -> None:
    in_file = tmp_path / "inspect.png"
    img = Image.new("RGB", (100, 100), (50, 150, 250))
    img.save(in_file)

    result = runner.invoke(app, ["inspect", str(in_file), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["dimensions"]["width"] == 100
    assert len(data["palette"]) > 0
