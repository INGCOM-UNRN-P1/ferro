"""Ajuste a + b·N^k con todos los tamaños, gráfico (QoL #375) y origen de la medición (#369)."""

from ferro.core.grafico import grafico_ascii, grafico_svg
from ferro.core.models import BenchmarkPoint, PerformanceProfile
from ferro.core.perf_runner import ajuste_loglog


def _puntos(f):
    return [BenchmarkPoint(input_size_n=n, elapsed_time_ms=1.0, instructions_est=int(f(n))) for n in (100, 200, 400, 800)]


def test_costo_fijo_no_engana_al_exponente():
    k, r2 = ajuste_loglog(_puntos(lambda n: 100_000 + 10 * n * n), "instructions_est")
    assert abs(k - 2.0) < 0.05 and r2 > 0.99
    k, _ = ajuste_loglog(_puntos(lambda n: 100_000 + 50 * n), "instructions_est")
    assert abs(k - 1.0) < 0.05


def test_pocos_puntos():
    assert ajuste_loglog(_puntos(lambda n: n)[:2], "instructions_est") is None


def test_graficos(tmp_path):
    perfil = PerformanceProfile(target_name="p.c", points=_puntos(lambda n: n * n),
                                metrica_complejidad="instrucciones (Cachegrind)", exponente_empirico=2.0, r2_ajuste=1.0)
    assert "N^2.0" in grafico_ascii(perfil)
    destino = tmp_path / "g.svg"
    assert grafico_svg(perfil, destino) and destino.read_text().startswith("<svg")
