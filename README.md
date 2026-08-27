# FERRO — Perfilador de Rendimiento Algorítmico y Hardware Counters en C

**FERRO** ejecuta programas C a través de múltiples tamaños de entrada ($N$), midiendo tiempos de alta resolución, ciclos de CPU estimados, throughput e infiriendo la complejidad temporal empírica ($O(N)$, $O(N \log N)$, $O(N^2)$).

---

## 🚀 Uso Rápido

```bash
# Perfilar algoritmo con diferentes tamaños de entrada
ferro profile ordenamiento.c --inputs "1000,10000,50000"

# Salida estructurada JSON
ferro profile ordenamiento.c --json
```
