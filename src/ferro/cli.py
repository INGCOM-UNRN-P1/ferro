"""CLI principal de FERRO."""

import json
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ferro.core.models import PerformanceProfile
from ferro.core.perf_runner import profile_algorithm

app = typer.Typer(
    name="ferro",
    help="Perfilador de rendimiento algorítmico y hardware counters en C",
    add_completion=True
)
console = Console()


@app.command()
def profile(
    target: Path = typer.Argument(..., help="Archivo .c o binario a perfilar", exists=True),
    inputs_str: str = typer.Option("1000,10000,50000", "--inputs", "-i", help="Lista de tamaños de entrada N separados por coma"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado")
):
    """Mide tiempo de ejecución, ciclos estimados y evalúa complejidad empírica vs teórica."""
    sizes = [int(s.strip()) for s in inputs_str.split(",") if s.strip()]
    profile_data = profile_algorithm(target, sizes)

    if json_output:
        print(json.dumps(profile_data.model_dump(), indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Perfil de Rendimiento Algorítmico ({target.name})", show_header=True, header_style="bold magenta")
    table.add_column("Input N", style="cyan", justify="right")
    table.add_column("Tiempo (ms)", style="yellow", justify="right")
    table.add_column("Ciclos CPU Est.", style="white", justify="right")
    table.add_column("Instrucciones Est.", style="dim", justify="right")
    table.add_column("Ciclos / Elemento", style="bold green", justify="right")

    for pt in profile_data.points:
        table.add_row(
            f"{pt.input_size_n:,}",
            f"{pt.elapsed_time_ms:.3f} ms",
            f"{pt.cpu_cycles_est:,}",
            f"{pt.instructions_est:,}",
            f"{pt.cycles_per_element:.2f}"
        )

    console.print(table)
    console.print(Panel(
        f"[bold]Complejidad Empírica Estimada:[/bold] [bold green]{profile_data.theoretical_complexity_guess}[/bold green]\n"
        f"[bold]Localidad de Memoria y Caché:[/bold] {profile_data.cache_locality_assessment}",
        title="[bold cyan]FERRO Performance Assessment[/bold cyan]"
    ))


@app.command()
def version():
    """Muestra la versión de FERRO."""
    from ferro import __version__
    console.print(f"[bold cyan]FERRO[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
