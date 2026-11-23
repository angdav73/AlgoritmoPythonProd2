import io
import time
import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st
import itertools

import algorithms
import puebla_data

def interpolar_recorrido(coordenadas, num_muestras_tramo=10):
    recorrido_completo = []
    for i in range(len(coordenadas) - 1):
        p1 = coordenadas[i]
        p2 = coordenadas[i + 1]
        for t in np.linspace(0, 1, num_muestras_tramo, endpoint=False):
            lon = (1.0 - t) * p1[0] + t * p2[0]
            lat = (1.0 - t) * p1[1] + t * p2[1]
            recorrido_completo.append([lon, lat])
    recorrido_completo.append(coordenadas[-1])
    return recorrido_completo

def renderizar_deck(puntos_df, camino_rec, camino_pend, vehiculo_df, halo_df, centro_lat, centro_lon, estilo_mapa):
    capas = []

    if camino_rec is not None and len(camino_rec) > 1:
        capas.append(pdk.Layer(
            "PathLayer",
            data=pd.DataFrame([{"camino": camino_rec}]),
            get_path="camino",
            get_color=[16, 185, 129, 240],
            width_scale=20,
            width_min_pixels=5,
            pickable=True,
        ))

    if camino_pend is not None and len(camino_pend) > 1:
        capas.append(pdk.Layer(
            "PathLayer",
            data=pd.DataFrame([{"camino": camino_pend}]),
            get_path="camino",
            get_color=[148, 163, 184, 180],
            width_scale=15,
            width_min_pixels=3,
            pickable=True,
        ))

    capas.append(pdk.Layer(
        "ScatterplotLayer",
        data=puntos_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radio",
        pickable=True,
        auto_highlight=True,
    ))

    if halo_df is not None:
        capas.append(pdk.Layer(
            "ScatterplotLayer",
            data=halo_df,
            get_position=["lon", "lat"],
            get_color=[251, 191, 36, 90],
            get_radius="radio",
        ))

    if vehiculo_df is not None:
        capas.append(pdk.Layer(
            "ScatterplotLayer",
            data=vehiculo_df,
            get_position=["lon", "lat"],
            get_color=[245, 158, 11, 255],
            get_radius="radio",
            pickable=True,
            auto_highlight=True,
        ))

    estado_vista = pdk.ViewState(
        latitude=centro_lat,
        longitude=centro_lon,
        zoom=11.3,
        pitch=30,
        bearing=0
    )

    return pdk.Deck(
        layers=capas,
        initial_view_state=estado_vista,
        map_style=estilo_mapa,
        tooltip={"text": "{nombre}\n{categoria}\n{direccion}"}
    )

st.set_page_config(
    page_title="OptiRoute AI - Puebla",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Opciones de Ruta")

    fuente_datos = st.selectbox(
        "Lugares a visitar:",
        ["Puebla (UTP, FINSA, Centros Comerciales)", "Generar puntos al azar", "Cargar archivo propio"]
    )

    if "Puebla" in fuente_datos:
        num_puntos = st.slider("Cantidad de paradas:", min_value=4, max_value=len(puebla_data.PUNTOS_PUEBLA), value=12)
        puntos_seleccionados = puebla_data.obtener_subconjunto_puntos(num_puntos)
    elif "azar" in fuente_datos:
        num_puntos = st.slider("Cantidad de paradas:", min_value=10, max_value=50, value=25)
        puntos_seleccionados = puebla_data.generar_puntos_sinteticos(num_puntos)
    else:
        archivo_csv = st.file_uploader("Subir archivo CSV:", type=["csv"])
        if archivo_csv is not None:
            df_subido = pd.read_csv(archivo_csv)
            puntos_seleccionados = df_subido.to_dict(orient="records")
            num_puntos = len(puntos_seleccionados)
            st.success(f"{num_puntos} paradas cargadas correctamente.")
        else:
            st.warning("Usando 10 puntos de Puebla hasta subir archivo.")
            puntos_seleccionados = puebla_data.obtener_subconjunto_puntos(10)
            num_puntos = 10

    st.markdown("---")
    st.markdown("### Calidad del Cálculo")

    modo = st.select_slider(
        "Nivel de optimización:",
        options=["Rápido", "Recomendado", "Máxima precisión"],
        value="Recomendado"
    )

    if modo == "Rápido":
        tam_poblacion = 50
        generaciones = 60
    elif modo == "Recomendado":
        tam_poblacion = 100
        generaciones = 120
    else:
        tam_poblacion = 200
        generaciones = 250

    tasa_cruce = 0.85
    tasa_mutacion = 0.15
    elitismo = 2

    with st.expander("Ajustes avanzados"):
        tam_poblacion = st.slider("Rutas analizadas por grupo:", min_value=20, max_value=300, value=tam_poblacion, step=10)
        generaciones = st.slider("Intentos de mejora:", min_value=20, max_value=400, value=generaciones, step=10)
        comparar_heuristica = st.checkbox("Comparar con ruta rápida (Vecino más cercano)", value=True)
        comparar_ciega = st.checkbox("Comparar con ruta al azar (Sin IA)", value=True)

    st.markdown("---")
    st.markdown("### Costos Operativos")
    precio_combustible = st.number_input("Precio de combustible ($/Litro):", min_value=15.0, max_value=40.0, value=24.80, step=0.50)
    rendimiento_vehiculo = st.number_input("Rendimiento del vehículo (km/L):", min_value=3.0, max_value=20.0, value=8.5, step=0.5)

    ejecutar = st.button("Calcular Ruta Óptima", type="primary", use_container_width=True)

st.markdown('<div class="main-header">OptiRoute AI: Planificador Inteligente de Rutas</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Sistema inteligente para la planificación y optimización de rutas de transporte y logística. '
    'Calcula la secuencia óptima de paradas para minimizar tiempos de traslado, reducir distancias y optimizar el consumo de combustible mediante algoritmos de búsqueda y optimización.'
    '</div>',
    unsafe_allow_html=True
)

matriz_distancias = puebla_data.calcular_matriz_distancias(puntos_seleccionados)

if "resultados_optimizacion" not in st.session_state or ejecutar:
    with st.spinner("Ejecutando algoritmos de búsqueda y optimización..."):
        res_ga = algorithms.ejecutar_algoritmo_genetico(
            matriz_distancias=matriz_distancias,
            tam_poblacion=tam_poblacion,
            generaciones=generaciones,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion,
            elitismo=elitismo
        )

        res_nn = algorithms.busqueda_heuristica_vecino_cercano(matriz_distancias)
        res_2opt = algorithms.heuristica_2opt_local_search(res_nn["mejor_ruta"], matriz_distancias)

        if num_puntos <= 9:
            res_ciega = algorithms.busqueda_ciega_exhaustiva(matriz_distancias, max_nodos=9)
        else:
            res_ciega = algorithms.busqueda_ciega_aleatoria(matriz_distancias, num_muestras=15000)

        st.session_state.resultados_optimizacion = {
            "ga": res_ga,
            "nn": res_nn,
            "2opt": res_2opt,
            "ciega": res_ciega,
            "puntos": puntos_seleccionados,
            "matriz": matriz_distancias
        }

datos_sesion = st.session_state.resultados_optimizacion
res_ga = datos_sesion["ga"]
res_nn = datos_sesion["nn"]
res_2opt = datos_sesion["2opt"]
res_ciega = datos_sesion["ciega"]
puntos = datos_sesion["puntos"]

tab_mapa, tab_metricas = st.tabs([
    "Mapa y Ruta",
    "Métricas y Comparativa"
])

with tab_mapa:
    st.subheader("Trazado Georreferenciado del Circuito Óptimo")

    distancia_ga = res_ga["mejor_distancia"]
    tiempo_ga = res_ga["tiempo_ms"]
    consumo_litros = distancia_ga / rendimiento_vehiculo
    costo_monetario = consumo_litros * precio_combustible
    co2_kg = consumo_litros * 2.68

    distancia_inicial = res_ga["distancia_inicial"]
    consumo_inicial = distancia_inicial / rendimiento_vehiculo
    costo_inicial = consumo_inicial * precio_combustible
    ahorro_dinero = max(0.0, costo_inicial - costo_monetario)
    ahorro_vs_inicial = res_ga["mejora_porcentaje"]

    total_paquetes = sum(p.get("demanda_paquetes", 0) for p in puntos)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Distancia Óptima", f"{distancia_ga:.2f} km", delta=f"-{ahorro_vs_inicial:.1f}% vs inicial")
    col2.metric("Tiempo de Cómputo", f"{tiempo_ga:.1f} ms")
    col3.metric("Combustible", f"{consumo_litros:.2f} L")
    col4.metric("Costo de Ruta", f"${costo_monetario:.2f} MXN", delta=f"-${ahorro_dinero:.2f} MXN")
    col5.metric("Carga Total", f"{total_paquetes} paq.")

    ruta_indices = res_ga["mejor_ruta"] + [res_ga["mejor_ruta"][0]]

    df_puntos = pd.DataFrame(puntos)
    df_puntos["es_hub"] = df_puntos["id"].apply(lambda x: x == 0)
    df_puntos["color"] = df_puntos["es_hub"].apply(
        lambda es_hub: [220, 38, 38, 240] if es_hub else [37, 99, 235, 200]
    )
    df_puntos["radio"] = df_puntos["es_hub"].apply(lambda es_hub: 480 if es_hub else 260)

    coordenadas_ruta = [[puntos[idx]["lon"], puntos[idx]["lat"]] for idx in ruta_indices]
    puntos_interpolados = interpolar_recorrido(coordenadas_ruta, num_muestras_tramo=10)

    centro_lat = float(np.mean([p["lat"] for p in puntos]))
    centro_lon = float(np.mean([p["lon"] for p in puntos]))

    st.markdown("#### Simulación de Tráfico y Navegación")
    col_capa, col_trafico, col_btn, col_slider = st.columns([1.3, 1.3, 1.0, 1.4])
    
    estilo_opcion = col_capa.selectbox("Capa Cartográfica:", ["Calles Urbanas (Carto Positron)", "Modo Nocturno (Carto DarkMatter)"])
    estilo_mapa = "carto-positron" if "Positron" in estilo_opcion else "carto-darkmatter"
    
    condicion_trafico = col_trafico.selectbox("Condición de Tránsito:", ["Fluido / Normal", "Hora Pico en Puebla (+40% tiempo)", "Lluvia intensa (+25% tiempo)"])
    
    if "Hora Pico" in condicion_trafico:
        factor_tiempo = 1.40
        velocidad_media = 28.0
    elif "Lluvia" in condicion_trafico:
        factor_tiempo = 1.25
        velocidad_media = 32.0
    else:
        factor_tiempo = 1.0
        velocidad_media = 42.0

    tiempo_conduccion_horas = (distancia_ga / velocidad_media) * factor_tiempo
    tiempo_descarga_horas = (len(puntos) * 8.0) / 60.0
    tiempo_total_jornada = tiempo_conduccion_horas + tiempo_descarga_horas
    horas_jornada = int(tiempo_total_jornada)
    minutos_jornada = int((tiempo_total_jornada - horas_jornada) * 60)

    btn_simular = col_btn.button("Simular Recorrido", use_container_width=True)
    progreso_slider = col_slider.slider("Progreso (%):", min_value=0, max_value=100, value=0, step=1)

    contenedor_mapa = st.empty()
    contenedor_telemetria = st.empty()

    if btn_simular:
        for p in range(0, 101, 2):
            idx_v = int((p / 100.0) * (len(puntos_interpolados) - 1))
            pos_v = puntos_interpolados[idx_v]
            camino_rec = puntos_interpolados[:idx_v + 1]
            camino_pend = puntos_interpolados[idx_v:]

            df_veh = pd.DataFrame([{"lon": pos_v[0], "lat": pos_v[1], "radio": 450, "nombre": "Unidad de Reparto en Tránsito"}])
            df_halo = pd.DataFrame([{"lon": pos_v[0], "lat": pos_v[1], "radio": 800}])

            d = renderizar_deck(df_puntos, camino_rec, camino_pend, df_veh, df_halo, centro_lat, centro_lon, estilo_mapa)
            contenedor_mapa.pydeck_chart(d)

            with contenedor_telemetria.container():
                c_tel1, c_tel2, c_tel3, c_tel4 = st.columns(4)
                c_tel1.metric("Odómetro Acumulado", f"{(p / 100.0) * distancia_ga:.2f} km")
                c_tel2.metric("Estado del Agente", "Completado" if p == 100 else "En Tránsito")
                c_tel3.metric("Velocidad Estimada", f"{velocidad_media:.1f} km/h")
                c_tel4.metric("Coordenadas GPS", f"{pos_v[1]:.4f}°, {pos_v[0]:.4f}°")

            time.sleep(0.04)
    else:
        idx_v = int((progreso_slider / 100.0) * (len(puntos_interpolados) - 1))
        pos_v = puntos_interpolados[idx_v]
        camino_rec = puntos_interpolados[:idx_v + 1] if progreso_slider > 0 else None
        camino_pend = puntos_interpolados[idx_v:] if progreso_slider < 100 else None

        df_veh = pd.DataFrame([{"lon": pos_v[0], "lat": pos_v[1], "radio": 450, "nombre": "Unidad de Reparto"}])
        df_halo = pd.DataFrame([{"lon": pos_v[0], "lat": pos_v[1], "radio": 800}])

        d = renderizar_deck(df_puntos, camino_rec, camino_pend, df_veh, df_halo, centro_lat, centro_lon, estilo_mapa)
        contenedor_mapa.pydeck_chart(d)

        with contenedor_telemetria.container():
            c_tel1, c_tel2, c_tel3, c_tel4 = st.columns(4)
            c_tel1.metric("Odómetro Acumulado", f"{(progreso_slider / 100.0) * distancia_ga:.2f} km")
            c_tel2.metric("Estado del Agente", "Completado" if progreso_slider == 100 else ("En Espera" if progreso_slider == 0 else "En Tránsito"))
            c_tel3.metric("Velocidad Estimada", f"{velocidad_media:.1f} km/h")
            c_tel4.metric("Coordenadas GPS", f"{pos_v[1]:.4f}°, {pos_v[0]:.4f}°")

    st.markdown("---")
    st.markdown("### Resumen Operativo de la Jornada")
    col_op1, col_op2, col_op3, col_op4 = st.columns(4)
    col_op1.metric("Duración Estimada", f"{horas_jornada}h {minutos_jornada}m")
    col_op2.metric("Emisiones CO₂", f"{co2_kg:.2f} kg")
    col_op3.metric("Ahorro Anual Estimado", f"${ahorro_dinero * 300:,.2f} MXN")
    col_op4.metric("Paradas a Entregar", f"{len(puntos) - 1} clientes")

    st.markdown("---")
    st.markdown("### Hoja de Ruta e Itinerario Secuencial")
    filas_itinerario = []
    distancia_acumulada = 0.0

    for paso, idx in enumerate(res_ga["mejor_ruta"]):
        nodo_actual = puntos[idx]
        sig_idx = res_ga["mejor_ruta"][(paso + 1) % len(res_ga["mejor_ruta"])]
        dist_tramo = matriz_distancias[idx, sig_idx]
        distancia_acumulada += dist_tramo
        enlace_gmaps = f"https://www.google.com/maps/search/?api=1&query={nodo_actual['lat']},{nodo_actual['lon']}"

        filas_itinerario.append({
            "Secuencia": f"Parada #{paso}",
            "Ubicación": nodo_actual["nombre"],
            "Categoría": nodo_actual["categoria"],
            "Carga / Demanda": f"{nodo_actual['demanda_paquetes']} paquetes",
            "Distancia Tramo": f"{dist_tramo:.2f} km",
            "Distancia Total": f"{distancia_acumulada:.2f} km",
            "Coordenadas": f"{nodo_actual['lat']:.4f}, {nodo_actual['lon']:.4f}",
            "Google Maps": enlace_gmaps
        })

    filas_itinerario.append({
        "Secuencia": "Cierre de Circuito",
        "Ubicación": f"Retorno a {puntos[0]['nombre']}",
        "Categoría": "Hub Central",
        "Carga / Demanda": "Fin de Jornada",
        "Distancia Tramo": "0.00 km",
        "Distancia Total": f"{distancia_acumulada:.2f} km",
        "Coordenadas": f"{puntos[0]['lat']:.4f}, {puntos[0]['lon']:.4f}",
        "Google Maps": f"https://www.google.com/maps/search/?api=1&query={puntos[0]['lat']},{puntos[0]['lon']}"
    })

    df_itinerario = pd.DataFrame(filas_itinerario)
    st.dataframe(
        df_itinerario,
        column_config={
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="Abrir Mapa")
        },
        use_container_width=True,
        hide_index=True
    )

    col_desc1, col_desc2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_itinerario.to_csv(csv_buffer, index=False)
    col_desc1.download_button(
        label="Descargar Hoja de Ruta (CSV)",
        data=csv_buffer.getvalue(),
        file_name="hoja_de_ruta_puebla_optiroute.csv",
        mime="text/csv",
        use_container_width=True
    )

    manifiesto_texto = (
        f"MANIFIESTO DE DESPACHO Y LOGISTICA\n"
        f"Sistema: OptiRoute AI Puebla\n"
        f"Origen: {puntos[0]['nombre']}\n"
        f"Total de paradas: {len(puntos)} nodos\n"
        f"Carga total a bordo: {total_paquetes} paquetes\n"
        f"Distancia total programada: {distancia_ga:.2f} km\n"
        f"Combustible estimado: {consumo_litros:.2f} L\n"
        f"Costo presupuestado: ${costo_monetario:.2f} MXN\n"
        f"Ahorro estimado por optimizacion: ${ahorro_dinero:.2f} MXN\n"
        f"Duracion estimada: {horas_jornada} horas y {minutos_jornada} minutos\n\n"
        f"SECUENCIA DE RECORRIDO:\n"
    )
    for fila in filas_itinerario:
        manifiesto_texto += f"- {fila['Secuencia']}: {fila['Ubicación']} ({fila['Carga / Demanda']}) -> Dist. Acumulada: {fila['Distancia Total']}\n"

    col_desc2.download_button(
        label="Descargar Manifiesto de Despacho (TXT)",
        data=manifiesto_texto,
        file_name="manifiesto_despacho_puebla.txt",
        mime="text/plain",
        use_container_width=True
    )

with tab_metricas:
    st.subheader("Análisis y Comparación entre Paradigmas de Búsqueda")

    st.markdown("#### Curva de Convergencia del Algoritmo Genético")
    st.caption("Evolución de la mejor distancia encontrada y la distancia promedio de la población por generación.")

    df_convergencia = pd.DataFrame({
        "Generación": list(range(1, len(res_ga["historial_mejor_distancia"]) + 1)),
        "Mejor Solución (km)": res_ga["historial_mejor_distancia"],
        "Promedio de la Población (km)": res_ga["historial_promedio_distancia"]
    }).set_index("Generación")

    st.line_chart(df_convergencia, color=["#10B981", "#3B82F6"])

    st.markdown("#### Benchmark Comparativo: Ciega vs Heurística vs Evolutiva")

    comparativa_filas = [
        {
            "Paradigma de IA": "1. Algoritmo Evolutivo (Genético)",
            "Algoritmo Específico": "AG (Cruce OX1 + Mutación Inversión + Torneo)",
            "Distancia Total": f"{res_ga['mejor_distancia']:.2f} km",
            "Tiempo de Ejecución": f"{res_ga['tiempo_ms']:.2f} ms",
            "Complejidad / Escalabilidad": "O(G · P · N) — Alta escalabilidad",
            "Garantía de Solución": "Metaheurística cercana al óptimo global"
        },
        {
            "Paradigma de IA": "2. Búsqueda Heurística (Voraz)",
            "Algoritmo Específico": "Vecino más Cercano (Nearest Neighbor)",
            "Distancia Total": f"{res_nn['mejor_distancia']:.2f} km",
            "Tiempo de Ejecución": f"{res_nn['tiempo_ms']:.4f} ms",
            "Complejidad / Escalabilidad": "O(N²) — Ultrarrápido pero local",
            "Garantía de Solución": "Suele quedar atrapado en óptimos locales"
        },
        {
            "Paradigma de IA": "2b. Heurística Local Refinada",
            "Algoritmo Específico": "Búsqueda Local 2-Opt",
            "Distancia Total": f"{res_2opt['mejor_distancia']:.2f} km",
            "Tiempo de Ejecución": f"{res_2opt['tiempo_ms']:.2f} ms",
            "Complejidad / Escalabilidad": "O(N² por pasada)",
            "Garantía de Solución": "Óptimo local respecto a vecindario 2-opt"
        }
    ]

    if res_ciega.get("mejor_distancia") is not None:
        nombre_ciega = res_ciega["algoritmo"]
        info_eval = f"{res_ciega.get('permutaciones_evaluadas', res_ciega.get('muestras_evaluadas', 0)):,} evaluaciones"
        comparativa_filas.append({
            "Paradigma de IA": "3. Búsqueda Ciega (No Informada)",
            "Algoritmo Específico": f"{nombre_ciega} ({info_eval})",
            "Distancia Total": f"{res_ciega['mejor_distancia']:.2f} km",
            "Tiempo de Ejecución": f"{res_ciega['tiempo_ms']:.2f} ms",
            "Complejidad / Escalabilidad": "O(N!) — Inviable para N > 10",
            "Garantía de Solución": "Óptimo si es exhaustiva; deficiente si es muestreo"
        })
    else:
        comparativa_filas.append({
            "Paradigma de IA": "3. Búsqueda Ciega (Fuerza Bruta)",
            "Algoritmo Específico": "Permutación Exhaustiva",
            "Distancia Total": "Inviable",
            "Tiempo de Ejecución": "> Varios años",
            "Complejidad / Escalabilidad": f"O({num_puntos}!) = {itertools.permutations(range(num_puntos-1))} estados",
            "Garantía de Solución": "Colapso por explosión combinatoria"
        })

    df_comparativa = pd.DataFrame(comparativa_filas)
    st.table(df_comparativa)

    with st.expander("Demostración Matemática: ¿Por qué la Búsqueda Ciega falla en este problema?"):
        st.markdown(r"""
        El espacio de búsqueda para el Problema del Agente Viajero con $N$ nodos fijando el nodo origen es de:
        $$\text{Espacio de Búsqueda} = (N - 1)!$$

        * Para $N = 5$ paradas: $(5-1)! = 4! = 24$ rutas posibles (trivial).
        * Para $N = 10$ paradas: $(10-1)! = 9! = 362,880$ rutas.
        * Para $N = 15$ paradas: $(15-1)! = 14! \approx 8.71 \times 10^{10}$ rutas.
        * Para $N = 25$ paradas (el dataset de Puebla): $(25-1)! = 24! \approx 6.20 \times 10^{23}$ rutas.
        * Para $N = 50$ clientes: $(50-1)! = 49! \approx 6.08 \times 10^{62}$ rutas.

        Una supercomputadora que evalúe 1,000,000,000 de rutas por segundo tardaría más de **$1.9 \times 10^{46}$ años** en completar una búsqueda ciega para 50 clientes.
        Por ello, el uso de **Algoritmos Evolutivos** es obligatorio: explora eficientemente regiones prometedoras del espacio sin recorrerlo todo.
        """)
