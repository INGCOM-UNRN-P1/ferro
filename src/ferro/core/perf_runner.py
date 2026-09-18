"""Ejecutor de benchmarks y recolección de métricas de rendimiento en C."""

import math
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from ferro.core.cache_locality import MedicionCache, medir_localidad_cache
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

    return BenchmarkPoint(
        input_size_n=n,
        elapsed_time_ms=round(elapsed_ms, 3),
        timed_out=timed_out,
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


OPT_LEVELS_VALIDOS = ("-O0", "-O1", "-O2", "-O3", "-Os")


def _detectar_trabajo_eliminado(points: List[BenchmarkPoint]) -> List[str]:
    """Avisa cuando las instrucciones ejecutadas no crecen con N.

    Con `-O2` el compilador elimina un bucle sin efectos observables, y un O(N²)
    real se medía como sobrecosto de proceso y se clasificaba "O(N) o
    sublineal". El síntoma es exacto y no depende del ruido del reloj: si N se
    duplica o más y las instrucciones no aumentan, el trabajo que se quería
    medir no se está ejecutando (o el programa ignora N).
    """
    medidos = [p for p in points if p.instructions_est is not None and not p.timed_out]
    if len(medidos) < 2:
        return []
    menor = min(medidos, key=lambda p: p.input_size_n)
    mayor = max(medidos, key=lambda p: p.input_size_n)
    if mayor.input_size_n >= 2 * menor.input_size_n and mayor.instructions_est <= menor.instructions_est * 1.05:
        return [
            f"Las instrucciones ejecutadas casi no crecen con N ({menor.instructions_est:,} para "
            f"N={menor.input_size_n:,} y {mayor.instructions_est:,} para N={mayor.input_size_n:,}): "
            "el optimizador pudo eliminar el trabajo que querés medir (un bucle sin efectos observables) "
            "o el programa no lee N por stdin. Compilá con -O0 o hacé observable el resultado "
            "(variable `volatile`, printf)."
        ]
    return []


def _clasificar_exponente(k: float) -> str:
    if k >= 1.6:
        return "O(N^2) o superior"
    if k >= 1.15:
        return "O(N log N)"
    return "O(N) o sublineal"


def _estimar_complejidad(points: List[BenchmarkPoint]) -> str:
    """Clasifica por el exponente de crecimiento entre los dos mayores tamaños.

    Las instrucciones de Cachegrind son deterministas; el reloj de pared de un
    programa corto está dominado por el arranque del proceso (~10 ms) y hacía que
    un O(N^2) real se leyera como "O(N) o sublineal". Solo si no hay
    instrucciones medidas se recurre al tiempo.
    """
    for campo in ("instructions_est", "elapsed_time_ms"):
        serie = sorted(
            ((p.input_size_n, getattr(p, campo)) for p in points if getattr(p, campo)),
            key=lambda t: t[0],
        )
        if len(serie) < 2:
            continue
        (n1, v1), (n2, v2) = serie[-2], serie[-1]
        if n2 <= n1 or v1 <= 0:
            continue
        if n2 < 2 * n1 and len(serie) >= 3:
            n1, v1 = serie[0]
        if n2 < 2 * n1:
            continue
        return _clasificar_exponente(math.log(v2 / v1) / math.log(n2 / n1))
    return "O(N)"


def profile_algorithm(
    source_or_binary: Path,
    input_sizes: List[int],
    opt_level: str = "-O0",
) -> PerformanceProfile:
    """Perfilado a través de diferentes tamaños de entrada N."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        if source_or_binary.suffix == ".c":
            bin_path = tmp_path / "bench_app"
            daed_res = _compilar_con_daedalus(source_or_binary, bin_path, [opt_level])
            if daed_res is not None:
                ok, stderr = daed_res
                if not ok:
                    return PerformanceProfile(
                        target_name=source_or_binary.name,
                        target_file=str(source_or_binary),
                        passed=False,
                        theoretical_complexity_guess="Error de compilación",
                        cache_locality_assessment="N/A",
                        error_message=f"Fallo al compilar con daedalus ({opt_level}):\n{stderr}"
                    )
            else:
                comp = subprocess.run(
                    ["gcc", opt_level, str(source_or_binary), "-o", str(bin_path)],
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
                        error_message=f"Fallo al compilar con gcc {opt_level}:\n{comp.stderr}"
                    )
            target_bin = bin_path
        else:
            target_bin = source_or_binary

        points = []
        mediciones = []
        for n in input_sizes:
            pt = run_benchmark_for_size(target_bin, n)
            # Una sola corrida bajo Cachegrind por tamaño da las instrucciones
            # ejecutadas (exactas) y la tasa de fallos de caché. La entrada viaja
            # por stdin, igual que en el cronometraje.
            if pt.timed_out:
                medicion = MedicionCache(medido=False, detalle="el caso agotó el tiempo límite.")
            else:
                medicion = medir_localidad_cache(target_bin, stdin_texto=f"{n}\n", timeout_segundos=30.0)
            if medicion.medido and medicion.instrucciones is not None:
                pt.instructions_est = medicion.instrucciones
                pt.instrucciones_por_elemento = round(medicion.instrucciones / n, 2) if n > 0 else None
                pt.contadores = "instrucciones: Cachegrind (exactas); ciclos e IPC no medidos (requieren perf_event_open)"
            points.append(pt)
            mediciones.append(medicion)

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

        complexity = _estimar_complejidad(points)

        return PerformanceProfile(
            target_name=source_or_binary.name,
            target_file=str(source_or_binary),
            points=points,
            theoretical_complexity_guess=complexity,
            cache_locality_assessment=(
                mediciones[-1].evaluacion if mediciones else "No medido: no se indicó ningún tamaño de entrada."
            ),
            opt_level=opt_level,
            advertencias=_detectar_trabajo_eliminado(points),
            passed=True
        )
