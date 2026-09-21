"""Modelos de datos para el perfilado de rendimiento en FERRO."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BenchmarkPoint(BaseModel):
    input_size_n: int
    elapsed_time_ms: float
    # Contadores: se informan solo si se MIDIERON. Antes los ciclos eran
    # tiempo × 3 GHz fijos, las instrucciones ciclos × 1,5 y el IPC un 1.5
    # constante presentado como dato: tres cifras inventadas con aspecto de
    # medición. Sin `perf_event_open` no hay ciclos ni IPC reales, así que quedan
    # en `None`; las instrucciones salen de Cachegrind (exactas).
    cpu_cycles_est: Optional[int] = None
    instructions_est: Optional[int] = None
    instrucciones_por_elemento: Optional[float] = None
    cycles_per_element: Optional[float] = None
    ipc: Optional[float] = None  # Instructions Per Cycle
    contadores: str = "no medido"
    # Distingue lo MEDIDO de lo estimado: "cachegrind" (instrucciones exactas),
    # "tiempo-de-pared" (solo cronómetro) o "no medido".
    origen_instrucciones: str = "no medido"
    timed_out: bool = False


class PerformanceProfile(BaseModel):
    schema_version: str = "1.0.0"
    target_name: str
    target_file: Optional[str] = None
    points: List[BenchmarkPoint] = Field(default_factory=list)
    theoretical_complexity_guess: str = "O(N)"
    cache_locality_assessment: str = "Buena localidad espacial detectada."
    passed: bool = True
    error_message: Optional[str] = None
    opt_level: str = "-O0"
    advertencias: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        if "target_name" in data and not data.get("target_file"):
            data["target_file"] = data["target_name"]
        super().__init__(**data)
