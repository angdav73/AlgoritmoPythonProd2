


---



**OptiRoute AI** es una aplicación web interactiva que resuelve el **Problema del Agente Viajero (TSP)** aplicado a la distribución logística y de transporte en la Zona Metropolitana de Puebla.

La aplicación implementa y compara los tres paradigmas de búsqueda del temario:
1. **Algoritmo Evolutivo (Genético):** Núcleo principal con cruce de orden (OX1), mutación por inversión 2-opt, selección por torneo y elitismo.
2. **Búsqueda Heurística (Informada):** Algoritmo del vecino más cercano (Greedy Nearest Neighbor) y refinamiento local 2-opt.
3. **Búsqueda Ciega (No Informada):** Búsqueda exhaustiva por fuerza bruta ($N \le 9$) y muestreo aleatorio uniforme para demostrar la explosión combinatoria.

---


1. Clona o abre esta carpeta en tu terminal:
   ```bash
   cd "w:\ESCRITORIOO\FUNDAMENTOS DE IA\AlgoritmoPython"
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicia la aplicación web:
   ```bash
   streamlit run app.py
   ```
   Se abrirá en tu navegador en `http://localhost:8501`.

---


