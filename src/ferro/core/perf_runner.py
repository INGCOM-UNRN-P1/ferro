"""Ejecutor de benchmarks y recolección de métricas de rendimiento en C."""

import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from ferro.core.cache_locality import medir_localidad_cache
from ferro.core.models import BenchmarkPoint, PerformanceProfile


def _try_import_nostromo():
    try:
        from nostromo.core.sandbox import ejecutar_aislado
        return ejecutar_aislado
    except ImportError:
        import sys
        sibling = Path(__file__).resolve().parents[4] / "nostromo" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
            try:
                from nostromo.core.sandbox import ejecutar_aislado
                return ejecutar_aislado
            except ImportError:
                return None
        return None


def run_benchmark_for_size(binary_path: Path, n: int) -> BenchmarkPoint:
    """Ejecuta el binario pasando 'n' y mide tiempo de ejecución de alta resolución delegando en nostromo."""
    input_str = f"{n}\n"
    timed_out = False

    ejecutar_fn = _try_import_nostromo()
    t0 = time.perf_counter()
    if ejecutar_fn:
        res = ejecutar_fn(binary_path, stdin_texto=input_str, timeout_segundos=5.0, memoria_mb=128)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        if res.error_tipo == "TIMEOUT":
            timed_out = True
            elapsed_ms = max(5000.0, elapsed_ms)
    else:
        try:
            res = subprocess.run(
                [str(binary_path)],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            t1 = time.perf_counter()
            elapsed_ms = (t1 - t0) * 1000.0
        except subprocess.TimeoutExpired:
            t1 = time.perf_counter()
            elapsed_ms = max(5000.0, (t1 - t0) * 1000.0)
            timed_out = True
        except Exception:
            elapsed_ms = 0.0

    # Estimación de ciclos (a ~3 GHz)
    cycles_est = int(elapsed_ms * 3_000_000)
    instructions_est = int(cycles_est * 1.5)  # Típico IPC ~1.5
    cycles_per_elem = (cycles_est / n) if n > 0 else 0.0

    return BenchmarkPoint(
        input_size_n=n,
        elapsed_time_ms=round(elapsed_ms, 3),
        cpu_cycles_est=cycles_est,
        instructions_est=instructions_est,
        cycles_per_element=round(cycles_per_elem, 2),
        ipc=1.5,
        timed_out=timed_out
    )


def _compilar_con_daedalus(src_file: Path, bin_file: Path, extra_flags: List[str]) -> Optional[Tuple[bool, str]]:
    try:
        from daedalus.core.compiler import compilar_archivos
        res = compilar_archivos([src_file], binario_salida=bin_file, flags_adicionales=extra_flags)
        return res.exito, res.stderr_crudo
    except ImportError:
        import sys
        sibling = Path(__file__).resolve().parents[4] / "daedalus" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
            try:
                from daedalus.core.compiler import compilar_archivos
                res = compilar_archivos([src_file], binario_salida=bin_file, flags_adicionales=extra_flags)
                return res.exito, res.stderr_crudo
            except ImportError:
                return None
        return None


def profile_algorithm(
    source_or_binary: Path,
    input_sizes: List[int]
) -> PerformanceProfile:
    """Perfilado a través de diferentes tamaños de entrada N."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        if source_or_binary.suffix == ".c":
            bin_path = tmp_path / "bench_app"
            daed_res = _compilar_con_daedalus(source_or_binary, bin_path, ["-O2"])
            if daed_res is not None:
                ok, stderr = daed_res
                if not ok:
                    return PerformanceProfile(
                        target_name=source_or_binary.name,
                        target_file=str(source_or_binary),
                        passed=False,
                        theoretical_complexity_guess="Error de compilación",
                        cache_locality_assessment="N/A",
                        error_message=f"Fallo al compilar con daedalus (-O2):\n{stderr}"
                    )
            else:
                comp = subprocess.run(
                    ["gcc", "-O2", str(source_or_binary), "-o", str(bin_path)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if comp.returncode != 0:
                    return PerformanceProfile(
                        target_name=source_or_binary.name,
                        target_file=str(source_or_binary),
                        passed=False,
                        theoretical_complexity_guess="Error de compilación",
                        cache_locality_assessment="N/A",
                        error_message=f"Fallo al compilar con gcc -O2:\n{comp.stderr}"
                    )
            target_bin = bin_path
        else:
            target_bin = source_or_binary

        points = []
        for n in input_sizes:
            pt = run_benchmark_for_size(target_bin, n)
            points.append(pt)

        any_timeout = any(pt.timed_out for pt in points)
        if any_timeout:
            return PerformanceProfile(
                target_name=source_or_binary.name,
                target_file=str(source_or_binary),
                points=points,
                theoretical_complexity_guess="Timeout excedido (> 5.0s)",
                cache_locality_assessment="Ejecución interrumpida por timeout de seguridad.",
                passed=False,
                error_message="Se excedió el tiempo límite de ejecución (5 segundos)."
            )

        # Estimación de complejidad
        if len(points) >= 2 and points[0].elapsed_time_ms > 0 and points[-1].elapsed_time_ms > 0:
            ratio_n = points[-1].input_size_n / points[0].input_size_n
            ratio_t = points[-1].elapsed_time_ms / points[0].elapsed_time_ms if points[0].elapsed_time_ms > 0 else 1.0
            if ratio_t > ratio_n * 2.5:
                complexity = "O(N^2) o superior"
            elif ratio_t > ratio_n * 1.2:
                complexity = "O(N log N)"
            else:
                complexity = "O(N) o sublineal"
        else:
            complexity = "O(N)"

        return PerformanceProfile(
            target_name=source_or_binary.name,
            target_file=str(source_or_binary),
            points=points,
            theoretical_complexity_guess=complexity,
            cache_locality_assessment=medir_localidad_cache(
                target_bin, args=[str(input_sizes[-1])] if input_sizes else None
            ).evaluacion,
            passed=True
        )
