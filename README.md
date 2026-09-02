# FERRO — Perfilador de Rendimiento Algorítmico y Hardware Counters en C

**FERRO** ejecuta programas C a través de múltiples tamaños de entrada ($N$), midiendo tiempos de alta resolución, ciclos de CPU estimados, throughput e infiriendo la complejidad temporal empírica ($O(N)$, $O(N \log N)$, $O(N^2)$).

---

## 🎯 Alcance

### Qué cubre
- Perfilado de rendimiento algorítmico y medición de eficiencia de bajo nivel en programas C.
- Acceso directo a contadores de hardware del procesador mediante el subsistema Linux `perf_event_open`: ciclos de clock, instrucciones retiradas, fallos de caché L1/LLC y desaciertos de predicción de saltos (branch misses).
- Medición de tiempos de ejecución de CPU de alta resolución (monótonos de nano-segundos).
- Emisión de informes estructurados en terminal y JSON para análisis de complejidad empírica.

### Qué no cubre (Límites y Delegación)
- Análisis estático de grafos de control de flujo o complejidad ciclomática (delegado a `giger`).
- Aislamiento de ejecución en entornos no confiables (delegado a `nostromo`).
- Fuzzing de robustez (delegado a `drake`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux x86_64 / arm64 con kernel que permita lectura de contadores (`/proc/sys/kernel/perf_event_paranoid <= 2`). Python >= 3.10.

### Dependencias Externas y Binarios
- `gcc`.

### Integración en el Ecosistema
- CLI `ferro`. Plugin registrado en `ripley.plugins` (`hardware_profiler`).

---

## 🚀 Uso Rápido

```bash
# Perfilar algoritmo con diferentes tamaños de entrada
ferro profile ordenamiento.c --inputs "1000,10000,50000"

# Salida estructurada JSON
ferro profile ordenamiento.c --json
```
