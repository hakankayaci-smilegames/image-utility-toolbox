"""Typer ve Rich Tabanlı Modern CLI Arayüzü (image-box)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import typer

from image_toolbox import __version__
from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import i18n
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.core.registry import registry
from image_toolbox.operations.resize import ResizeOperation
from image_toolbox.operations.watermark import WatermarkOperation
from image_toolbox.services.batch_runner import BatchProcessingRunner
from image_toolbox.services.compressor_service import TargetSizeCompressorService

app = typer.Typer(
    name="image-box",
    help="Image Utility Toolbox - Headless, high-performance image processing engine.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]Image Utility Toolbox[/bold cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    lang: str = typer.Option(
        "tr",
        "--lang",
        "-l",
        help="Language / Dil seçimi (tr, en).",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Versiyonu gösterir.",
    ),
) -> None:
    """Image Utility Toolbox - Komut Satırı Motoru."""
    i18n.set_language(lang)


@app.command("compress")
def compress_cmd(
    input_file: Path = typer.Argument(..., help="Giriş görsel dosyası", exists=True),
    output_file: Path = typer.Argument(..., help="Çıktı görsel dosyası"),
    target: str = typer.Option("500kb", "--target", "-t", help="Hedef dosya boyutu (örn: 350kb, 1.2mb)"),
    format: str = typer.Option("WEBP", "--format", "-f", help="Çıktı formatı (WEBP veya JPEG)"),
    strip_exif: bool = typer.Option(True, "--strip-exif/--keep-exif", help="EXIF verisini temizle"),
    min_quality: int = typer.Option(40, "--min-quality", help="Düşüş öncesi en düşük kalite"),
) -> None:
    """Görseli ikili arama ve akıllı çözünürlük düşüşü ile hedef dosya boyutuna sıkıştırır."""
    with console.status(f"[bold green]Sıkıştırılıyor: {input_file.name} -> {target}..."):
        ctx = ImageContext.from_file(input_file)
        service = TargetSizeCompressorService(
            min_quality=min_quality,
            strip_metadata=strip_exif,
        )
        res_ctx = service.compress(ctx, target_size=target, format=format)
        res_ctx.save(output_file, format=format)

    meta = res_ctx.metadata.get("compression", {})
    final_kb = meta.get("final_bytes", 0) / 1024.0
    dim = meta.get("final_dimensions", res_ctx.size)

    console.print(
        f"[bold green]✓[/bold green] "
        + i18n.get(
            "cli_compress_success",
            size_kb=final_kb,
            quality=meta.get("final_quality", "-"),
            width=dim[0],
            height=dim[1],
            iterations=meta.get("iterations", 0),
        )
    )


@app.command("resize")
def resize_cmd(
    input_file: Path = typer.Argument(..., help="Giriş görsel dosyası", exists=True),
    output_file: Path = typer.Argument(..., help="Çıktı görsel dosyası"),
    width: Optional[int] = typer.Option(None, "--width", "-w", help="Hedef genişlik"),
    height: Optional[int] = typer.Option(None, "--height", "-h", help="Hedef yükseklik"),
    scale: Optional[float] = typer.Option(None, "--scale", "-s", help="Ölçekleme oranı (örn: 0.5)"),
    mode: str = typer.Option("fit", "--mode", "-m", help="Resize modu (fit, fill, pad, exact)"),
) -> None:
    """En-boy oranını koruyarak veya serbest boyutlandırır."""
    ctx = ImageContext.from_file(input_file)
    op = ResizeOperation(width=width, height=height, scale=scale, mode=mode)
    res_ctx = op.apply(ctx)
    res_ctx.save(output_file)
    console.print(f"[bold green]✓[/bold green] Boyutlandırıldı: {ctx.size} -> {res_ctx.size}")


@app.command("watermark")
def watermark_cmd(
    input_file: Path = typer.Argument(..., help="Giriş görsel dosyası", exists=True),
    output_file: Path = typer.Argument(..., help="Çıktı görsel dosyası"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Filigran metni"),
    logo: Optional[Path] = typer.Option(None, "--logo", help="PNG logo dosyası", exists=True),
    anchor: str = typer.Option("bottom-right", "--anchor", "-a", help="Konum (bottom-right, center, vb.)"),
    opacity: float = typer.Option(0.7, "--opacity", "-o", help="Opaklık (0.0 - 1.0)"),
) -> None:
    """Görsele metin veya logo filigranı ekler."""
    ctx = ImageContext.from_file(input_file)
    op = WatermarkOperation(text=text, logo_path=logo, anchor=anchor, opacity=opacity)
    res_ctx = op.apply(ctx)
    res_ctx.save(output_file)
    console.print(f"[bold green]✓[/bold green] Filigran başarıyla eklendi: {output_file.name}")


@app.command("inspect")
def inspect_cmd(
    input_file: Path = typer.Argument(..., help="İncelenecek görsel dosyası", exists=True),
    palette: int = typer.Option(5, "--palette", "-p", help="Baskın renk sayısı"),
    as_json: bool = typer.Option(False, "--json", help="JSON formatında çıktı"),
) -> None:
    """Görsel boyutunu, EXIF verilerini ve K-Means baskın renk paletini inceler."""
    ctx = ImageContext.from_file(input_file)

    # 1. Palet operasyonunu çalıştır
    pal_op = registry.create("palette", k=palette)
    pal_op.apply(ctx)

    # 2. EXIF operasyonunu çalıştır
    exif_op = registry.create("exif", action="inspect")
    exif_op.apply(ctx)

    summary_data = {
        "file": str(input_file),
        "dimensions": {"width": ctx.width, "height": ctx.height},
        "has_alpha": ctx.has_alpha,
        "format": ctx.source_format,
        "palette": ctx.metadata.get("palette", []),
        "exif": ctx.metadata.get("exif_data", {}),
    }

    if as_json:
        console.print(json.dumps(summary_data, indent=2, ensure_ascii=False))
        return

    console.print(f"\n[bold cyan]── Görsel Detayları: {input_file.name} ──[/bold cyan]")
    console.print(f"Çözünürlük : {ctx.width}x{ctx.height}")
    console.print(f"Format     : {ctx.source_format}")
    console.print(f"Alfa Kanalı: {'Var' if ctx.has_alpha else 'Yok'}")

    pal_items = ctx.metadata.get("palette", [])
    if pal_items:
        console.print(f"\n[bold yellow]{i18n.get('palette_header', k=len(pal_items))}[/bold yellow]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("HEX")
        table.add_column("RGB")
        table.add_column("Yüzde")

        for item in pal_items:
            table.add_row(
                f"[bold]{item['hex']}[/bold]",
                str(item["rgb"]),
                f"%{item['percentage']}",
            )
        console.print(table)


@app.command("pipeline")
def pipeline_cmd(
    input_file: Path = typer.Argument(..., help="Giriş görsel dosyası", exists=True),
    output_file: Path = typer.Argument(..., help="Çıktı görsel dosyası"),
    recipe: Path = typer.Argument(..., help="JSON tarif dosyası", exists=True),
) -> None:
    """JSON tarifinden dinamik boru hattını yükler ve tek bir görsel üzerinde çalıştırır."""
    with console.status(f"[bold blue]Pipeline çalıştırılıyor..."):
        engine = PipelineEngine.from_recipe(recipe)
        engine.execute_file(input_file, output_file)
    console.print(f"[bold green]✓[/bold green] Boru hattı tamamlandı ({len(engine)} adım) -> {output_file.name}")


@app.command("batch")
def batch_cmd(
    input_dir: Path = typer.Argument(..., help="Giriş klasörü", exists=True, file_okay=False),
    output_dir: Path = typer.Argument(..., help="Çıktı klasörü", file_okay=False),
    recipe: Path = typer.Argument(..., help="JSON tarif dosyası", exists=True),
    workers: Optional[int] = typer.Option(None, "--workers", "-w", help="İş parçacığı sayısı"),
    preserve_hierarchy: bool = typer.Option(True, "--preserve-hierarchy/--flatten", help="Klasör ağacını koru"),
) -> None:
    """Bir klasördeki tüm görsellere paralel olarak boru hattını uygular."""
    engine = PipelineEngine.from_recipe(recipe)
    runner = BatchProcessingRunner(max_workers=workers)

    console.print(f"[bold cyan]Klasör taranıyor: {input_dir}[/bold cyan]")
    with console.status("[bold green]Toplu işlem devam ediyor..."):
        results = runner.run(
            input_dir=input_dir,
            output_dir=output_dir,
            pipeline=engine,
            preserve_hierarchy=preserve_hierarchy,
        )

    success_count = sum(1 for r in results if r.success)
    failed_count = sum(1 for r in results if not r.success)
    total_time = sum(r.duration for r in results)

    console.print(
        f"[bold green]✓[/bold green] "
        + i18n.get(
            "cli_batch_summary",
            success=success_count,
            failed=failed_count,
            duration=total_time,
        )
    )
    if failed_count > 0:
        for r in results:
            if not r.success:
                console.print(f"  [bold red]✗[/bold red] {r.input_path.name}: {r.error}")


@app.command("list-ops")
def list_ops_cmd() -> None:
    """Sistemde kayıtlı 22 modüler operasyonu listeler."""
    ops = registry.list_operations()
    table = Table(title=f"Kayıtlı Operasyonlar ({len(ops)})", show_header=True)
    table.add_column("Komut / Adı", style="bold cyan")
    table.add_column("Kategori", style="yellow")
    table.add_column("Sınıf", style="green")
    table.add_column("Açıklama")

    for name, info in ops.items():
        table.add_row(name, info["category"], info["class"], info["description"])

    console.print(table)


@app.command("gui")
def gui_cmd(
    input_file: Optional[Path] = typer.Argument(None, help="Açılacak başlangıç görsel dosyası"),
) -> None:
    """Modern masaüstü grafik arayüzünü (GUI) başlatır."""
    try:
        from image_toolbox.gui import launch_gui
        init_p = str(input_file) if input_file else None
        launch_gui(init_p)
    except ImportError as e:
        console.print(f"[bold red]Hata:[/bold red] GUI başlatılamadı. PyQt6 kurulu mu? ({e})")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
