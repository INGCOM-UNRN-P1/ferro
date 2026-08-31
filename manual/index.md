---
title: "Manual de Referencia: ferro"
subtitle: "Ferro — Perfilador de Rendimiento Algorítmico, Caché y Contadores de Hardware en C"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-ferro)=
# Ferro — Perfilador de Rendimiento Algorítmico, Caché y Contadores de Hardware en C

````{abstract}
**Rol en el ecosistema:** Medición de métricas de rendimiento en tiempo de ejecución: ciclos de CPU, instrucciones ejecutadas (IPC), aciertos y fallos de caché L1/L2/L3 y predicción de saltos.
````

---

(manual-ferro-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`ferro`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-ferro-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `ferro`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
ferro doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-ferro-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `ferro`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `ferro profile -- ./bin/programa` | Mide ciclos, tiempo de CPU y fallos de caché durante la ejecución. |
| `ferro compare --bin1 ./bin/opt --bin2 ./bin/naive` | Compara el rendimiento de dos algoritmos lado a lado. |
| `ferro cache-sim -- ./bin/matriz_mult` | Simula el comportamiento de las líneas de caché L1 (64 bytes). |
| `ferro doctor` | Verifica soporte de contadores de hardware `perf` o `valgrind --tool=cachegrind`. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-ferro-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
#define N 1024
int matriz[N][N];

// Recorrido por filas (Cache-Friendly: acceso contiguo)
void recorrido_filas(void) {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            matriz[i][j] = 1;
}

// Recorrido por columnas (Cache-Unfriendly: saltos de N * 4 bytes)
void recorrido_columnas(void) {
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
            matriz[i][j] = 1;
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
ferro profile -- ./bin/programa
````

### Salida Obtenida en Consola

````{code-block} text
PERFIL FERRO: recorrido_filas vs recorrido_columnas (N = 1024)
┌──────────────────────────┬────────────────────┬────────────────────┬───────────┐
│ Métrica                  │ Recorrido Filas    │ Recorrido Columnas │ Ganancia  │
├──────────────────────────┼────────────────────┼────────────────────┼───────────┤
│ Tiempo de CPU            │ 1.82 ms            │ 14.30 ms           │ 7.85x     │
│ Fallos de Caché L1 (D1)  │ 16,384 (1.5%)      │ 1,048,576 (99.8%)  │ 64.0x     │
│ Instrucciones / Ciclo    │ 2.45 IPC           │ 0.38 IPC           │ 6.44x     │
└──────────────────────────┴────────────────────┴────────────────────┴───────────┘
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-ferro-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`ferro`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Optimización de Recorrido de Matrices
Medir la tasa de fallos de caché L1 al transponer una matriz.

**Instrucción de ejecución:**
```bash
ferro profile -- ./bin/transposicion
```
````

````{solution} Desafío 1
```bash
ferro profile -- ./bin/transposicion
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Comparativa de Algoritmos de Ordenamiento
Comparar QuickSort vs BubbleSort midiendo instrucciones y saltos mal predichos.

**Instrucción de ejecución:**
```bash
ferro compare --bin1 ./bin/quicksort --bin2 ./bin/bubblesort
```
````

````{solution} Desafío 2
```bash
ferro compare --bin1 ./bin/quicksort --bin2 ./bin/bubblesort
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Simulación de Localidad Espacial
Inspeccionar cómo el empaquetamiento de structs reduce accesos a memoria.

**Instrucción de ejecución:**
```bash
ferro cache-sim -- ./bin/test_structs
```
````

````{solution} Desafío 3
```bash
ferro cache-sim -- ./bin/test_structs
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-ferro-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `ferro` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-ferro:
	@echo "=== Ejecutando verificación con ferro ==="
	ferro check src/ include/

.PHONY: check-ferro
````

Ejecutá `make check-ferro` antes de cada commit para asegurar que tu código conserve el estado de aprobación.
