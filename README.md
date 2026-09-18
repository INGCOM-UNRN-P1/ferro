# FERRO — Perfilador de Rendimiento Algorítmico y Hardware Counters en C

**FERRO** ejecuta programas C a través de múltiples tamaños de entrada ($N$), midiendo el tiempo y las instrucciones ejecutadas (con Cachegrind) e infiriendo la complejidad temporal empírica ($O(N)$, $O(N \log N)$, $O(N^2)$).

---

## 🎯 Alcance

### Qué cubre
- Perfilado de rendimiento algorítmico y medición de eficiencia de bajo nivel en programas C.
- Instrucciones ejecutadas y tasa de fallos de caché L1/LLC **exactas**, medidas con Valgrind/Cachegrind (simulación determinista, no contadores del procesador). Ciclos, IPC y branch misses **no se miden**: se informan como `N/D`.
- Clasificación de la complejidad por el crecimiento de las instrucciones entre los dos mayores $N$, que no depende del ruido del reloj.
- Aviso cuando las instrucciones no crecen con $N$ (el optimizador eliminó el bucle medido o el programa no lee $N$).
- Medición del tiempo de pared por tamaño de entrada.
- Emisión de informes estructurados en terminal y JSON para análisis de complejidad empírica.

### Qué no cubre (Límites y Delegación)
- Análisis estático de grafos de control de flujo o complejidad ciclomática (delegado a `giger`).
- Aislamiento de ejecución en entornos no confiables (delegado a `nostromo`).
- Fuzzing de robustez (delegado a `drake`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux. Python >= 3.10.

### Dependencias Externas y Binarios
- `gcc` (para compilar `.c`).
- `valgrind` (recomendado): sin él no hay instrucciones ni evaluación de caché y solo se informa el tiempo.

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

### Contrato de entrada

El programa perfilado **debe leer $N$ por la entrada estándar** (`scanf("%d", &n)`): ferro se lo envía como `N\n`. Un programa que ignore stdin se perfila igual con $N$ irrelevante, y las instrucciones no crecerán (ferro lo advierte).

Por defecto se compila con `-O0` (`--opt`): con `-O2` un bucle cuyo resultado no se usa se elimina y no se mide. Si querés medir con optimización, hacé observable el resultado (variable `volatile` o `printf`).
