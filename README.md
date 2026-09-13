# JAM (Just Another Mind) 🧠🤖

JAM es un asistente de Inteligencia Artificial **local, privado y autónomo** diseñado para ejecutarse enteramente en tu propio hardware (Linux, macOS y Windows). 

Con un diseño basado en terminal (TUI) de estética futurista y minimalista, JAM incorpora un sistema dual de modelos (Orquestador ligero + Generador pesado), memoria vectorial persistente a largo plazo (RAG) y conciencia de entorno (clima y geolocalización).

## ✨ Características Principales

- **Privacidad Total:** Los datos, la memoria RAG y los perfiles de usuario se encriptan (vectorizan) y se guardan de forma local en tu disco. Ningún dato privado viaja a la nube.
- **Arquitectura Dual Híbrida:** 
  - **MNG (Manager):** Un modelo ultraligero que lee intenciones, guarda recuerdos y crea *prompts* enriquecidos.
  - **GEN (Generator):** Un modelo pesado escalado a tu hardware que genera la respuesta final.
- **Recomendador de Hardware Integrado:** Analiza tu RAM, VRAM y Sistema Operativo para recomendar automáticamente el modelo GGUF ideal (desde `Qwen2.5-0.5B` para laptops sin GPU, hasta monstruos como `Qwen3-235B-MoE` para estaciones de trabajo masivas).
- **Interfaz Futurista TUI:** Construida sobre `Textual`, ofrece una experiencia fluida, compatible con mouse y redimensionable, directamente en tu terminal.
- **Memoria a Largo Plazo (RAG):** Impulsado por `ChromaDB`. JAM recuerda quién eres y adapta sus respuestas a tus preferencias a través de un protocolo de "Onboarding" automático.
- **Bilingüe:** UI e Inteligencia Artificial reactiva que entiende y responde en Inglés o Español dinámicamente según le hables.

---

## 🚀 Instalación y Uso (Fase Interfaz y Orquestador)

### 🐧 Linux y 🍏 macOS

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/jam-assistant.git
cd jam-assistant

# 2. Crear entorno virtual y activarlo
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar JAM
python3 jam/main.py
```

### 🪟 Windows

Abre **Windows Terminal**, PowerShell o Símbolo del Sistema:

```cmd
:: 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/jam-assistant.git
cd jam-assistant

:: 2. Crear entorno virtual y activarlo
python -m venv .venv
.venv\Scripts\activate

:: 3. Instalar dependencias
pip install -r requirements.txt

:: 4. Iniciar JAM
python jam\main.py
```

---

## 🧠 Activación de Inteligencia Artificial (Llama.cpp)

Para que JAM deje de usar la simulación y pase a procesar inferencia real descargando los modelos GGUF, debes instalar el motor de inferencia (`llama-cpp-python`).

**Para Linux / macOS (Apple Silicon Metal):**
```bash
# En Mac (Metal)
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# En Linux (Dependerá si usas CUDA o Vulkan)
pip install llama-cpp-python
```

**Para Windows (NVIDIA CUDA):**
Para evitar compilar C++ manualmente en Windows, puedes instalar los binarios pre-construidos para CUDA 12.4:
```cmd
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

---

## 🛠 Arquitectura del Proyecto

- `jam/main.py`: Punto de entrada y selección de idioma.
- `jam/ui/`: Interfaz gráfica TUI (Textual).
- `jam/core/`: 
  - `detector.py`: Análisis de OS, RAM, CPU y GPU (Nvidia/AMD/Apple).
  - `recommender.py`: Lógica de asignación de modelos.
  - `orchestrator.py`: Pipeline RAG y enrutamiento MNG -> GEN.
  - `inference.py`: Integración directa con `llama.cpp` y auto-descarga desde HuggingFace.
  - `environment.py`: Ping de clima y geolocalización.
- `jam/memory/`: Base de datos vectorial impulsada por ChromaDB.

## 🤝 Contribuciones
¡Los Pull Requests son bienvenidos! Para cambios mayores, abre un *issue* primero para discutir qué te gustaría modificar.
