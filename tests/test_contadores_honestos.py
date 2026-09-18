"""Regresión de FERRO-D0303 y FERRO-D0304.

D0303: ciclos, instrucciones e IPC salían de fórmulas sobre el tiempo de pared.
D0304: con `-O2` un bucle sin efectos observables se eliminaba y un O(N^2) real
se clasificaba "O(N) o sublineal".
"""

import json
import shutil
import subprocess

import pytest
from typer.testing import CliRunner

from ferro.cli import app, generar_seccion_markdown
from ferro.core.models import BenchmarkPoint, PerformanceProfile
from ferro.core.perf_runner import _detectar_trabajo_eliminado, _estimar_complejidad, profile_algorithm

runner = CliRunner()

necesita_toolchain = pytest.mark.skipif(
    not (shutil.which("valgrind") and shutil.which("gcc")),
    reason="requiere gcc y valgrind para medir de verdad",
)

CUADRATICO_SIN_EFECTOS = """#include <stdio.h>
int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long s = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            s += i ^ j;
    return 0;
}
"""

LINEAL_OBSERVABLE = """#include <stdio.h>
int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    volatile long s = 0;
    for (int i = 0; i < n; i++) s += i;
    printf("%ld\\n", (long)s);
    return 0;
}
"""


def _pt(n, instrucciones=None, ms=10.0):
    return BenchmarkPoint(input_size_n=n, elapsed_time_ms=ms, instructions_est=instrucciones)


def test_punto_sin_medicion_no_inventa_cifras():
    pt = BenchmarkPoint(input_size_n=1000, elapsed_time_ms=12.5)
    assert pt.instructions_est is None
    assert pt.instrucciones_por_elemento is None
    assert pt.contadores == "no medido"


def test_markdown_muestra_nd_para_contadores_no_medidos():
    perfil = PerformanceProfile(
        target_name="a.c",
        points=[BenchmarkPoint(input_size_n=1000, elapsed_time_ms=12.5)],
        theoretical_complexity_guess="O(N)",
        cache_locality_assessment="No medido",
    )
    md = generar_seccion_markdown(perfil)
    assert "N/D" in md
    assert "IPC" not in md and "Ciclos" not in md


def test_clasifica_por_instrucciones_aunque_el_reloj_no_distinga():
    # 10 ms constantes (arranque del proceso) e instrucciones que crecen como N^2.
    puntos = [_pt(100, 250_000), _pt(400, 1_450_000), _pt(1600, 20_600_000)]
    assert _estimar_complejidad(puntos) == "O(N^2) o superior"


def test_clasifica_lineal_por_instrucciones():
    puntos = [_pt(1000, 100_000), _pt(10_000, 1_000_000), _pt(100_000, 10_000_000)]
    assert _estimar_complejidad(puntos) == "O(N) o sublineal"


def test_sin_instrucciones_recurre_al_tiempo():
    puntos = [_pt(100, None, 1.0), _pt(1000, None, 100.0)]
    assert _estimar_complejidad(puntos) == "O(N^2) o superior"


def test_detecta_trabajo_eliminado():
    avisos = _detectar_trabajo_eliminado([_pt(100, 171_856), _pt(400, 171_856), _pt(1600, 171_904)])
    assert len(avisos) == 1
    assert "optimizador" in avisos[0]


def test_no_avisa_cuando_las_instrucciones_crecen():
    assert _detectar_trabajo_eliminado([_pt(100, 250_000), _pt(1600, 20_600_000)]) == []


def test_no_avisa_con_un_solo_punto_medido():
    assert _detectar_trabajo_eliminado([_pt(100, 250_000), _pt(1600, None)]) == []


def test_opt_invalido_se_rechaza(tmp_path):
    src = tmp_path / "a.c"
    src.write_text("int main(void) { return 0; }")
    res = runner.invoke(app, ["profile", str(src), "--opt", "-O9"])
    assert res.exit_code == 2


@necesita_toolchain
def test_o0_mide_cuadratico_y_o2_avisa_de_eliminacion(tmp_path):
    src = tmp_path / "cuad.c"
    src.write_text(CUADRATICO_SIN_EFECTOS)

    o0 = profile_algorithm(src, [100, 400, 1600], opt_level="-O0")
    assert o0.passed
    assert o0.theoretical_complexity_guess == "O(N^2) o superior"
    assert o0.advertencias == []
    assert o0.opt_level == "-O0"

    o2 = profile_algorithm(src, [100, 400, 1600], opt_level="-O2")
    assert o2.opt_level == "-O2"
    assert len(o2.advertencias) == 1


@necesita_toolchain
def test_instrucciones_medidas_recibiendo_n_por_stdin(tmp_path):
    src = tmp_path / "lin.c"
    src.write_text(LINEAL_OBSERVABLE)
    perfil = profile_algorithm(src, [1000, 100_000], opt_level="-O0")
    chico, grande = perfil.points
    # Si N no llegara por stdin, ambas corridas ejecutarían lo mismo. El arranque
    # del proceso suma una base fija, así que se mira el costo marginal por elemento.
    marginal = (grande.instructions_est - chico.instructions_est) / (grande.input_size_n - chico.input_size_n)
    assert 3 <= marginal <= 30
    assert grande.instrucciones_por_elemento < chico.instrucciones_por_elemento


@necesita_toolchain
def test_json_expone_nivel_de_optimizacion_y_advertencias(tmp_path):
    src = tmp_path / "cuad.c"
    src.write_text(CUADRATICO_SIN_EFECTOS)
    res = runner.invoke(app, ["profile", str(src), "-i", "100,400,1600", "--opt", "-O2", "--json"])
    datos = json.loads(res.output)
    assert datos["opt_level"] == "-O2"
    assert datos["advertencias"]
