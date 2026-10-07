"""Gráfico de N contra la métrica medida (QoL #375): en la terminal (ASCII, escala log-log) y como
SVG sin dependencias, para el reporte del estudiante."""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple

from ferro.core.models import BenchmarkPoint, PerformanceProfile

ANCHO, ALTO = 48, 12


def _serie(perfil: PerformanceProfile) -> Tuple[str, List[Tuple[int, float]]]:
    campo = "instructions_est" if perfil.metrica_complejidad.startswith("instrucciones") else "elapsed_time_ms"
    nombre = "instrucciones" if campo == "instructions_est" else "tiempo (ms)"
    puntos: List[BenchmarkPoint] = [p for p in perfil.points if getattr(p, campo) and not p.timed_out]
    return nombre, [(p.input_size_n, float(getattr(p, campo))) for p in puntos]


def grafico_ascii(perfil: PerformanceProfile) -> Optional[str]:
    nombre, serie = _serie(perfil)
    if len(serie) < 2:
        return None
    lx = [math.log10(n) for n, _ in serie]
    ly = [math.log10(v) for _, v in serie]
    x0, x1, y0, y1 = min(lx), max(lx), min(ly), max(ly)
    grilla = [[" "] * ANCHO for _ in range(ALTO)]
    for x, y in zip(lx, ly, strict=False):
        col = round((x - x0) / ((x1 - x0) or 1) * (ANCHO - 1))
        fila = ALTO - 1 - round((y - y0) / ((y1 - y0) or 1) * (ALTO - 1))
        grilla[fila][col] = "●"
    lineas = [f"{nombre} (escala log)"]
    lineas += [f"{'│'}{''.join(f)}" for f in grilla]
    lineas.append("└" + "─" * ANCHO)
    lineas.append(f" N = {serie[0][0]:,} … {serie[-1][0]:,} (escala log)")
    if perfil.exponente_empirico is not None:
        lineas.append(f" pendiente k = {perfil.exponente_empirico} (R² = {perfil.r2_ajuste}): crece como N^{perfil.exponente_empirico}")
    return "\n".join(lineas)


def grafico_svg(perfil: PerformanceProfile, destino: Path) -> bool:
    nombre, serie = _serie(perfil)
    if len(serie) < 2:
        return False
    ancho, alto, margen = 480, 300, 50
    lx = [math.log10(n) for n, _ in serie]
    ly = [math.log10(v) for _, v in serie]
    x0, x1, y0, y1 = min(lx), max(lx), min(ly), max(ly)

    def px(x: float, y: float) -> Tuple[float, float]:
        return (margen + (x - x0) / ((x1 - x0) or 1) * (ancho - 2 * margen),
                alto - margen - (y - y0) / ((y1 - y0) or 1) * (alto - 2 * margen))

    puntos = [px(x, y) for x, y in zip(lx, ly, strict=False)]
    trazo = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    circulos = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#2563eb"/>' for x, y in puntos)
    etiquetas = "".join(f'<text x="{x:.1f}" y="{alto - margen + 16}" font-size="10" text-anchor="middle">{n:,}</text>'
                        for (x, _), (n, _) in zip(puntos, serie, strict=False))
    titulo = perfil.target_name + (f" — crece como N^{perfil.exponente_empirico}" if perfil.exponente_empirico else "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" font-family="sans-serif">'
           f'<rect width="100%" height="100%" fill="white"/>'
           f'<text x="{ancho / 2}" y="20" font-size="13" text-anchor="middle">{titulo}</text>'
           f'<line x1="{margen}" y1="{alto - margen}" x2="{ancho - margen}" y2="{alto - margen}" stroke="#444"/>'
           f'<line x1="{margen}" y1="{margen}" x2="{margen}" y2="{alto - margen}" stroke="#444"/>'
           f'<polyline points="{trazo}" fill="none" stroke="#2563eb" stroke-width="2"/>{circulos}{etiquetas}'
           f'<text x="{ancho / 2}" y="{alto - 10}" font-size="11" text-anchor="middle">N (escala log)</text>'
           f'<text x="14" y="{alto / 2}" font-size="11" text-anchor="middle" transform="rotate(-90 14 {alto / 2})">'
           f'{nombre} (escala log)</text></svg>')
    destino.write_text(svg, encoding="utf-8")
    return True
