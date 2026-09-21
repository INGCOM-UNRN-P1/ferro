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


def test_json_versionado_y_distingue_medido_de_no_medido(tmp_path):
    """FERRO-D0602: el JSON lleva schema_version y el origen de cada contador."""
    import json
    src = tmp_path / "a.c"
    src.write_text("#include <stdio.h>\nint main(void){int n;scanf(\"%d\",&n);return 0;}", encoding="utf-8")
    res = runner.invoke(app, ["profile", str(src), "-i", "10,20", "--json"])
    data = json.loads(res.output)
    assert data["schema_version"] == "1.0.0"
    for pt in data["points"]:
        assert pt["origen_instrucciones"] in ("cachegrind", "no medido")
        if pt["instructions_est"] is not None:
            assert pt["origen_instrucciones"] == "cachegrind"


def test_version_como_opcion_global():
    """FERRO-D0402: `--version`/`-v` como en el resto del ecosistema."""
    from ferro import __version__
    for flag in ("--version", "-v"):
        res = runner.invoke(app, [flag])
        assert res.exit_code == 0
        assert __version__ in res.output


def test_error_de_compilacion_es_fallo_limpio_y_no_traceback(tmp_path):
    """FERRO-D0403/D0305: un .c que no compila da passed=false y exit 1, sin CalledProcessError."""
    import json
    src = tmp_path / "mal.c"
    src.write_text("int main(void){ return x; }", encoding="utf-8")
    res = runner.invoke(app, ["profile", str(src), "--json"])
    assert res.exit_code == 1
    assert json.loads(res.output)["passed"] is False
    assert "CalledProcessError" not in res.output
