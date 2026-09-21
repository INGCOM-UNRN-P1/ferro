"""Plugin de FERRO para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any
from ferro.core.perf_runner import profile_algorithm


class FerroPlugin:
    """Plugin de perfilado de rendimiento y hardware counters para Ripley."""

    name = "hardware_profiler"
    description = "Perfilado de rendimiento algorítmico, ciclos de CPU y localidad de caché"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        main_c = source_dir / "main.c"
        if not main_c.exists():
            return {"passed": True, "message": "main.c no encontrado"}

        profile = profile_algorithm(main_c, [1000, 10000])

        return {
            "schema_version": profile.schema_version,
            "passed": profile.passed,
            "complexity": profile.theoretical_complexity_guess,
            "points": [p.model_dump() for p in profile.points]
        }
