"""Regresión de FERRO-D0301: la localidad de caché debe medirse, no afirmarse.

`cache_locality_assessment` era una cadena constante: cuatro programas con
patrones de acceso opuestos recibían el mismo veredicto.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from ferro.core.cache_locality import MedicionCache, medir_localidad_cache

FILAS = """#include <stdio.h>
#define N 700
static int m[N][N];
int main(void) {
    long s = 0;
    for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) m[i][j] = i + j;
    for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) s += m[i][j];
    printf("%ld\\n", s); return 0;
}
"""
COLUMNAS = FILAS.replace("m[i][j] = i + j", "m[j][i] = i + j").replace("s += m[i][j]", "s += m[j][i]")

necesita_toolchain = pytest.mark.skipif(
    not (shutil.which("valgrind") and shutil.which("gcc")),
    reason="requiere gcc y valgrind para medir de verdad",
)


def _compilar(tmp_path: Path, fuente: str, nombre: str) -> Path:
    c = tmp_path / f"{nombre}.c"
    c.write_text(fuente, encoding="utf-8")
    binario = tmp_path / nombre
    subprocess.run(["gcc", "-O1", str(c), "-o", str(binario)], check=True)
    return binario


@necesita_toolchain
def test_patrones_opuestos_dan_veredictos_distintos(tmp_path):
    """El recorrido por columnas debe fallar en caché mucho más que por filas."""
    por_filas = medir_localidad_cache(_compilar(tmp_path, FILAS, "filas"))
    por_columnas = medir_localidad_cache(_compilar(tmp_path, COLUMNAS, "columnas"))

    assert por_filas.medido and por_columnas.medido
    assert por_columnas.tasa_fallos_d1 > por_filas.tasa_fallos_d1 * 2
    assert por_filas.evaluacion != por_columnas.evaluacion


@necesita_toolchain
def test_la_evaluacion_cita_la_tasa_medida(tmp_path):
    medicion = medir_localidad_cache(_compilar(tmp_path, FILAS, "filas"))
    assert "Cachegrind" in medicion.evaluacion
    assert f"{medicion.tasa_fallos_d1:.1f}" in medicion.evaluacion


def test_sin_valgrind_se_declara_no_medido(tmp_path, monkeypatch):
    """Nunca hay que afirmar un patrón que no se midió."""
    monkeypatch.setattr("ferro.core.cache_locality.shutil.which", lambda _: None)
    medicion = medir_localidad_cache(tmp_path / "inexistente")
    assert medicion.medido is False
    assert medicion.evaluacion.startswith("No medido:")


@pytest.mark.parametrize(
    "tasa, esperado",
    [(0.5, "buena localidad espacial"), (5.0, "localidad intermedia"), (60.0, "localidad pobre")],
)
def test_umbrales_de_lectura(tasa, esperado):
    medicion = MedicionCache(medido=True, tasa_fallos_d1=tasa, tasa_fallos_lld=1.0)
    assert esperado in medicion.evaluacion
