"""Tests unitarios y de integración para FERRO."""

from pathlib import Path
from typer.testing import CliRunner
from ferro.cli import app
from ferro.core.perf_runner import profile_algorithm
from ferro.plugins.ripley_plugin import FerroPlugin

runner = CliRunner()


def test_profile_algorithm_c_source(tmp_path):
    src = tmp_path / "app.c"
    src.write_text("""
    #include <stdio.h>
    int main(void) {
        long n = 1000;
        scanf("%ld", &n);
        long sum = 0;
        for (long i = 0; i < n; i++) {
            sum += i;
        }
        return 0;
    }
    """)
    profile = profile_algorithm(src, [100, 500])
    assert len(profile.points) == 2
    assert profile.points[0].input_size_n == 100
    assert profile.points[1].input_size_n == 500


def test_cli_profile_json(tmp_path):
    src = tmp_path / "app.c"
    src.write_text("int main(void) { return 0; }")
    res = runner.invoke(app, ["profile", str(src), "-i", "10,20", "--json"])
    assert res.exit_code == 0
    assert '"theoretical_complexity_guess"' in res.output


def test_cli_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "FERRO" in res.output


def test_ripley_plugin(tmp_path):
    src = tmp_path / "main.c"
    src.write_text("int main(void) { return 0; }")
    plugin = FerroPlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "points" in res
