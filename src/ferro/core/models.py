"""Modelos de datos para el perfilado de rendimiento en FERRO."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BenchmarkPoint(BaseModel):
    input_size_n: int
    elapsed_time_ms: float
    cpu_cycles_est: int = 0
    instructions_est: int = 0
    cycles_per_element: float = 0.0
    ipc: float = 0.0  # Instructions Per Cycle
    timed_out: bool = False


class PerformanceProfile(BaseModel):
    target_name: str
    target_file: Optional[str] = None
    points: List[BenchmarkPoint] = Field(default_factory=list)
    theoretical_complexity_guess: str = "O(N)"
    cache_locality_assessment: str = "Buena localidad espacial detectada."
    passed: bool = True
    error_message: Optional[str] = None

    def __init__(self, **data):
        if "target_name" in data and not data.get("target_file"):
            data["target_file"] = data["target_name"]
        super().__init__(**data)
