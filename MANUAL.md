# Manual de Uso y Referencia Técnica: ferro

> **FERRO** — Perfilador de rendimiento algorítmico y hardware counters en C
> **Versión:** `0.1.0` · **CLI principal:** `ferro` · **Plugin Ripley:** `hardware_profiler`

---

## 1. Arquitectura y Propósito Pedagógico

`ferro` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Perfilado de rendimiento algorítmico y medición de eficiencia de bajo nivel en programas C.
- Instrucciones ejecutadas y tasa de fallos de caché L1/LLC **exactas**, medidas con Valgrind/Cachegrind (simulación determinista, no contadores del procesador). Ciclos, IPC y branch misses **no se miden**: se informan como `N/D`.
- Clasificación de la complejidad por el crecimiento de las instrucciones entre los dos mayores $N$, que no depende del ruido del reloj.
- Aviso cuando las instrucciones no crecen con $N$ (el optimizador eliminó el bucle medido o el programa no lee $N$).
- Medición del tiempo de pared por tamaño de entrada.
- Emisión de informes estructurados en terminal y JSON para análisis de complejidad empírica.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Análisis estático de grafos de control de flujo o complejidad ciclomática (delegado a `giger`).
- Aislamiento de ejecución en entornos no confiables (delegado a `nostromo`).
- Fuzzing de robustez (delegado a `drake`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/ferro
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
ferro doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`ferro check`](#check) | Mide tiempo de ejecución e instrucciones ejecutadas, y evalúa la complejidad empírica. |
| [`ferro profile`](#profile) | Mide tiempo de ejecución e instrucciones ejecutadas, y evalúa la complejidad empírica. |
| [`ferro report`](#report) | Genera directamente la sección de reporte Markdown de FERRO para Dredd. |
| [`ferro doctor`](#doctor) | Verifica el estado del entorno de perfilado de rendimiento FERRO (Python, GCC, perf/time). |
| [`ferro version`](#version) | Muestra la versión de FERRO. |

### `ferro check`

Mide tiempo de ejecución e instrucciones ejecutadas, y evalúa la complejidad empírica.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `target` | `<class 'pathlib._local.Path'>` | Archivo .c o binario a perfilar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--inputs`, `-i` | `<class 'str'>` | `1000,10000,50000` | Lista de tamaños de entrada N separados por coma |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |
| `--opt` | `<class 'str'>` | `-O0` | Nivel de optimización al compilar un .c (-O0, -O1, -O2, -O3, -Os). Con -O2 un bucle sin efectos observables se elimina y no se mide. |

#### Ejemplo de Invocación
```bash
ferro check <target>
```

### `ferro profile`

Mide tiempo de ejecución e instrucciones ejecutadas, y evalúa la complejidad empírica.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `target` | `<class 'pathlib._local.Path'>` | Archivo .c o binario a perfilar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--inputs`, `-i` | `<class 'str'>` | `1000,10000,50000` | Lista de tamaños de entrada N separados por coma |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |
| `--opt` | `<class 'str'>` | `-O0` | Nivel de optimización al compilar un .c (-O0, -O1, -O2, -O3, -Os). Con -O2 un bucle sin efectos observables se elimina y no se mide. |

#### Ejemplo de Invocación
```bash
ferro profile <target>
```

### `ferro report`

Genera directamente la sección de reporte Markdown de FERRO para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `target` | `<class 'pathlib._local.Path'>` | Archivo .c o binario a perfilar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[pathlib._local.Path]` | `None` | Ruta de destino del archivo Markdown. |
| `--inputs`, `-i` | `<class 'str'>` | `1000,10000,50000` | Lista de tamaños de entrada N |
| `--opt` | `<class 'str'>` | `-O0` | Nivel de optimización al compilar un .c (-O0, -O1, -O2, -O3, -Os). |

#### Ejemplo de Invocación
```bash
ferro report <target>
```

### `ferro doctor`

Verifica el estado del entorno de perfilado de rendimiento FERRO (Python, GCC, perf/time).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
ferro doctor
```

### `ferro version`

Muestra la versión de FERRO.

#### Ejemplo de Invocación
```bash
ferro version
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
ferro check --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: ferro, tool=ferro, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`ferro` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
ferro doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.