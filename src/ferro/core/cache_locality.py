"""Medición real de localidad de caché con Cachegrind.

Antes este dato era una cadena constante: cualquier programa —recorriera un
arreglo por filas o saltara por columnas— recibía el mismo veredicto
("Patrón de acceso lineal continuo con baja tasa de cache misses").

Se usa `valgrind --tool=cachegrind` en lugar de `perf` porque es determinista,
no depende de contadores de hardware ni de `perf_event_paranoid`, y ya es
parte del herramental de la cátedra. Si no está disponible, se dice que no se
midió en vez de afirmar un patrón.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# "D1  miss rate:    4.2%" / "LLd miss rate:  0.1%"
_TASA_D1 = re.compile(r"D1\s+miss rate:\s*([\d.]+)%")
_TASA_LLD = re.compile(r"LLd\s+miss rate:\s*([\d.]+)%")
# "I   refs:      852,954": instrucciones realmente ejecutadas, exactas y deterministas.
_INSTRUCCIONES = re.compile(r"\bI\s+refs:\s+([\d,]+)")

# Umbrales de tasa de fallos de D1 para traducir el número a una lectura
# pedagógica. Por encima de ~10 % el patrón de acceso domina el tiempo de
# ejecución y vale la pena mirarlo antes que el algoritmo.
UMBRAL_BUENA = 2.0
UMBRAL_REGULAR = 10.0


@dataclass
class MedicionCache:
    """Resultado de medir la localidad de caché de una ejecución."""
    medido: bool
    tasa_fallos_d1: Optional[float] = None
    tasa_fallos_lld: Optional[float] = None
    instrucciones: Optional[int] = None
    detalle: str = ""

    @property
    def evaluacion(self) -> str:
        if not self.medido:
            return f"No medido: {self.detalle}"
        if self.tasa_fallos_d1 is None:
            return "No medido: Cachegrind no informó la tasa de fallos de D1."
        if self.tasa_fallos_d1 < UMBRAL_BUENA:
            lectura = "buena localidad espacial"
        elif self.tasa_fallos_d1 < UMBRAL_REGULAR:
            lectura = "localidad intermedia"
        else:
            lectura = "localidad pobre: el patrón de acceso domina el tiempo de ejecución"
        return (
            f"Cachegrind: {self.tasa_fallos_d1:.1f} % de fallos en D1 "
            f"y {self.tasa_fallos_lld:.1f} % en LLd — {lectura}."
            if self.tasa_fallos_lld is not None
            else f"Cachegrind: {self.tasa_fallos_d1:.1f} % de fallos en D1 — {lectura}."
        )


def medir_localidad_cache(
    binario: Path,
    args: Optional[List[str]] = None,
    timeout_segundos: float = 60.0,
    stdin_texto: str = "",
) -> MedicionCache:
    """Ejecuta el binario bajo Cachegrind y devuelve las tasas de fallo reales.

    `stdin_texto` es la entrada del programa: los benchmarks de FERRO le pasan N
    por stdin, y medir sin ella cuenta solo el arranque (140 mil instrucciones)
    en lugar del trabajo real (853 mil para N=2000 en el programa de prueba).
    """
    valgrind = shutil.which("valgrind")
    if not valgrind:
        return MedicionCache(medido=False, detalle="valgrind no está instalado.")

    cmd = [
        valgrind,
        "--tool=cachegrind",
        # Desde Valgrind 3.2x la simulación de caché no viene activada por
        # defecto: sin esto Cachegrind solo informa "I refs".
        "--cache-sim=yes",
        "--cachegrind-out-file=/dev/null",
        str(binario),
        *(args or []),
    ]
    try:
        res = subprocess.run(cmd, input=stdin_texto, capture_output=True, text=True, timeout=timeout_segundos)
    except subprocess.TimeoutExpired:
        return MedicionCache(
            medido=False,
            detalle=f"Cachegrind excedió el límite de {timeout_segundos:.0f} s.",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return MedicionCache(medido=False, detalle=f"No se pudo ejecutar Cachegrind: {exc}")

    salida = res.stderr or ""
    m_d1 = _TASA_D1.search(salida)
    m_lld = _TASA_LLD.search(salida)
    if not m_d1:
        return MedicionCache(
            medido=False,
            detalle="Cachegrind no emitió estadísticas de caché para esta ejecución.",
        )

    m_ir = _INSTRUCCIONES.search(salida)
    return MedicionCache(
        medido=True,
        tasa_fallos_d1=float(m_d1.group(1)),
        tasa_fallos_lld=float(m_lld.group(1)) if m_lld else None,
        instrucciones=int(m_ir.group(1).replace(",", "")) if m_ir else None,
    )
