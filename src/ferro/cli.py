"""CLI principal de FERRO."""

import json
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ferro.core.models import PerformanceProfile
from ferro.core.perf_runner import OPT_LEVELS_VALIDOS, profile_algorithm

app = typer.Typer(
    name="ferro",
    help="Perfilador de rendimiento algorítmico y hardware counters en C",
    add_completion=True
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        from ferro import __version__
        typer.echo(f"ferro {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Muestra la versión de ferro y sale.",
        callback=_version_callback, is_eager=True,
    ),
) -> None:
    """Perfilador de rendimiento algorítmico y hardware counters en C."""


def _parsear_tamanios(texto: str) -> List[int]:
    """`--inputs "100,1000"` -> [100, 1000]; un valor no numérico es un error de uso, no un ValueError crudo."""
    try:
        tamanios = [int(t.strip()) for t in texto.split(",") if t.strip()]
    except ValueError:
        err_console.print(f"[red]--inputs inválido:[/red] '{texto}'. Se esperan enteros separados por coma, p. ej. 1000,10000.")
        raise typer.Exit(code=2)
    if not tamanios or any(t <= 0 for t in tamanios):
        err_console.print("[red]--inputs inválido:[/red] indicá al menos un tamaño N y todos deben ser mayores que cero.")
        raise typer.Exit(code=2)
    return tamanios


def _validar_opt(opt: str) -> None:
    if opt not in OPT_LEVELS_VALIDOS:
        err_console.print(f"[red]--opt inválido:[/red] {opt}. Valores admitidos: {', '.join(OPT_LEVELS_VALIDOS)}.")
        raise typer.Exit(code=2)


def _fmt_entero(valor) -> str:
    """Un contador no medido se muestra como N/D, nunca como una cifra."""
    return f"{valor:,}" if valor is not None else "N/D"


def _fmt_decimal(valor) -> str:
    return f"{valor:.2f}" if valor is not None else "N/D"


def generar_seccion_markdown(profile_data: PerformanceProfile) -> str:
    """Genera sección de auditoría de rendimiento y complejidad para Dredd."""
    target_name = Path(profile_data.target_file or profile_data.target_name).name
    lines = ["## Perfilado de Rendimiento y Complejidad (Ferro)\n"]
    lines.append(f"- **Archivo analizado:** `{target_name}`")
    lines.append(f"- **Complejidad empírica estimada:** `{profile_data.theoretical_complexity_guess}`")
    lines.append(f"- **Evaluación de caché/localidad:** {profile_data.cache_locality_assessment}\n")
    for aviso in profile_data.advertencias:
        lines.append(f"> [!WARNING]\n> {aviso}\n")
    if not profile_data.passed:
        lines.append(f"> [!CAUTION]\n> **Fallo en Perfilado:** {profile_data.error_message or 'Error en ejecución'}\n")
    if profile_data.points:
        lines.append("| Input N | Tiempo (ms) | Instrucciones (Cachegrind) | Instrucciones / Elemento |")
        lines.append("| :---: | :---: | :---: | :---: |")
        for pt in profile_data.points:
            lines.append(
                f"| {pt.input_size_n:,} | {pt.elapsed_time_ms:.3f} ms | {_fmt_entero(pt.instructions_est)} "
                f"| {_fmt_decimal(pt.instrucciones_por_elemento)} |"
            )
        lines.append("")
    return "\n".join(lines)


@app.command("profile")
@app.command("check")
def profile(
    target: Path = typer.Argument(..., help="Archivo .c o binario a perfilar", exists=True),
    inputs_str: str = typer.Option("1000,10000,50000", "--inputs", "-i", help="Lista de tamaños de entrada N separados por coma"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
    opt: str = typer.Option("-O0", "--opt", help="Nivel de optimización al compilar un .c (-O0, -O1, -O2, -O3, -Os). Con -O2 un bucle sin efectos observables se elimina y no se mide."),
):
    """Mide tiempo de ejecución e instrucciones ejecutadas, y evalúa la complejidad empírica."""
    _validar_opt(opt)
    sizes = _parsear_tamanios(inputs_str)
    profile_data = profile_algorithm(target, sizes, opt_level=opt)

    if output_md:
        md_text = generar_seccion_markdown(profile_data)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Sección Markdown generada en:[/bold green] {output_md}")
        raise typer.Exit(code=0 if profile_data.passed else 1)

    if json_output:
        print(json.dumps(profile_data.model_dump(), indent=2, ensure_ascii=False))
        if not profile_data.passed:
            raise typer.Exit(code=1)
        return

    if not profile_data.passed:
        console.print(Panel(
            f"[bold red]❌ Error de Rendimiento o Ejecución:[/bold red]\n{profile_data.error_message or profile_data.theoretical_complexity_guess}",
            title="[bold red]FERRO Error[/bold red]"
        ))
        raise typer.Exit(code=1)

    table = Table(title=f"Perfil de Rendimiento Algorítmico ({target.name})", show_header=True, header_style="bold magenta")
    table.add_column("Input N", style="cyan", justify="right")
    table.add_column("Tiempo (ms)", style="yellow", justify="right")
    table.add_column("Instrucciones (Cachegrind)", style="white", justify="right")
    table.add_column("Instrucciones / Elemento", style="bold green", justify="right")

    for pt in profile_data.points:
        table.add_row(
            f"{pt.input_size_n:,}",
            f"{pt.elapsed_time_ms:.3f} ms",
            _fmt_entero(pt.instructions_est),
            _fmt_decimal(pt.instrucciones_por_elemento),
        )

    console.print(table)
    avisos = "".join(f"\n[bold yellow]⚠ {a}[/bold yellow]" for a in profile_data.advertencias)
    console.print(Panel(
        f"[bold]Complejidad Empírica Estimada:[/bold] [bold green]{profile_data.theoretical_complexity_guess}[/bold green]\n"
        f"[bold]Localidad de Memoria y Caché:[/bold] {profile_data.cache_locality_assessment}"
        f"{avisos}",
        title="[bold cyan]FERRO Performance Assessment[/bold cyan]"
    ))


@app.command("report")
def report_cmd(
    target: Path = typer.Argument(..., help="Archivo .c o binario a perfilar", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    inputs_str: str = typer.Option("1000,10000,50000", "--inputs", "-i", help="Lista de tamaños de entrada N"),
    opt: str = typer.Option("-O0", "--opt", help="Nivel de optimización al compilar un .c (-O0, -O1, -O2, -O3, -Os)."),
):
    """Genera directamente la sección de reporte Markdown de FERRO para Dredd."""
    _validar_opt(opt)
    sizes = _parsear_tamanios(inputs_str)
    profile_data = profile_algorithm(target, sizes, opt_level=opt)
    md_content = generar_seccion_markdown(profile_data)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)
    raise typer.Exit(code=0 if profile_data.passed else 1)


@app.command("doctor")
def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir diagnóstico en formato JSON estructurado."),
) -> None:
    """Verifica el estado del entorno de perfilado de rendimiento FERRO (Python, GCC, perf/time)."""
    import shutil
    import sys
    diagnostico = []

    py_ok = sys.version_info >= (3, 10)
    diagnostico.append({
        "componente": "Python Runtime",
        "estado": "OK" if py_ok else "ERROR",
        "requerido": True,
        "detalle": f"Python {sys.version.split()[0]}",
    })

    gcc_path = shutil.which("gcc")
    diagnostico.append({
        "componente": "Compilador GCC",
        "estado": "OK" if gcc_path else "ERROR",
        "requerido": True,
        "detalle": gcc_path or "No encontrado (requerido para compilar fuentes .c a perfilar)",
    })

    perf_path = shutil.which("perf")
    diagnostico.append({
        "componente": "Herramienta Linux perf",
        "estado": "OK" if perf_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": perf_path or "No encontrado (se utilizará emulación y rusage)",
    })

    todo_ok = py_ok and bool(gcc_path)

    if json_output:
        import json
        payload = {
            "schema_version": "1.0.0",
            "herramienta": "ferro",
            "ok": todo_ok,
            "componentes": diagnostico,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if todo_ok else 1)

    tabla = Table(title="🏥 Diagnóstico del Entorno FERRO (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle")

    for c in diagnostico:
        color = "bold green" if c["estado"] == "OK" else ("bold yellow" if c["estado"] == "ADVERTENCIA" else "bold red")
        simbolo = "✓" if c["estado"] == "OK" else ("⚠️" if c["estado"] == "ADVERTENCIA" else "✗")
        tabla.add_row(c["componente"], f"[{color}]{simbolo} {c['estado']}[/{color}]", c["detalle"])

    console.print(tabla)
    if not todo_ok:
        console.print("\n[bold red]Instalá gcc (`sudo apt install gcc` o equivalente).[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Muestra la versión de FERRO."""
    from ferro import __version__
    console.print(f"[bold cyan]FERRO[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
