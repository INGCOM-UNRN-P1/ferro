"""Regresión de FERRO-D0801: entrada no numérica y contrato de entrada."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ferro.cli import app

runner = CliRunner()
README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.mark.parametrize("inputs", ["abc", "10,x", "0", "-5", ",,"])
@pytest.mark.parametrize("comando", ["profile", "report"])
def test_un_inputs_invalido_es_error_de_uso_y_no_un_traceback(tmp_path, comando, inputs):
    src = tmp_path / "a.c"
    src.write_text("int main(void) { return 0; }", encoding="utf-8")
    res = runner.invoke(app, [comando, str(src), "--inputs", inputs])
    assert res.exit_code == 2
    assert "--inputs inválido" in res.output
    assert not isinstance(res.exception, ValueError)


def test_report_acepta_opt_y_lo_valida(tmp_path):
    src = tmp_path / "a.c"
    src.write_text("int main(void) { return 0; }", encoding="utf-8")
    assert runner.invoke(app, ["report", str(src), "--opt", "-O9"]).exit_code == 2
    assert runner.invoke(app, ["report", str(src), "-i", "10", "--opt", "-O1"]).exit_code == 0


def test_el_readme_no_promete_contadores_de_hardware_inexistentes():
    texto = README.read_text(encoding="utf-8")
    assert "perf_event_open" not in texto.split("Qué no cubre")[0].replace("**no se miden**", "")
    assert "N/D" in texto
    assert "stdin" in texto.lower() or "entrada estándar" in texto
