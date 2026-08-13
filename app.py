import streamlit as st
import folium
from streamlit_folium import st_folium
from optimizacion_logistica import optimizar_coordenadas_geograficas
import pandas as pd


def eliminar_cliente(cliente_id):
    st.session_state.clientes = [
        cliente
        for cliente in st.session_state.clientes
        if cliente["id"] != cliente_id
    ]

    st.session_state.pop(f"nombre_{cliente_id}", None)
    st.session_state.pop(f"peso_{cliente_id}", None)

    st.session_state.resultado = None
    st.session_state.punto_optimo = None
    

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Optimización Logística",
    layout="wide"
)


# =========================================================
# ESTADO
# =========================================================

if "clientes" not in st.session_state:
    st.session_state.clientes = []

if "ultimo_click" not in st.session_state:
    st.session_state.ultimo_click = None

if "siguiente_id" not in st.session_state:
    st.session_state.siguiente_id = 1

if "siguiente_numero_cliente" not in st.session_state:
    st.session_state.siguiente_numero_cliente = 1

if "resultado" not in st.session_state:
    st.session_state.resultado = None

if "punto_optimo" not in st.session_state:
    st.session_state.punto_optimo = None


# Compatibilidad con clientes antiguos
for cliente in st.session_state.clientes:
    if "id" not in cliente:
        cliente["id"] = st.session_state.siguiente_id
        st.session_state.siguiente_id += 1


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>

    /* Menos espacio superior */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1600px;
    }

    /* Reducir separación entre elementos */
    div[data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }

    /* Botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        padding: 0.65rem 0.8rem;
        border-radius: 10px;
    }

    /* Inputs un poco más compactos */
    div[data-baseweb="input"] {
        border-radius: 8px;
    }

    /* Ocultar footer */
    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# ENCABEZADO
# =========================================================

st.markdown("## Optimización Logística")
st.caption(
    "Ubicación óptima de un centro de distribución "
    "mediante descenso de gradiente"
)

# =========================================================
# LAYOUT PRINCIPAL
# =========================================================

col_mapa, col_panel = st.columns(
    [3.2, 1],
    gap="medium"
)


# =========================================================
# MAPA
# =========================================================

with col_mapa:

    st.markdown("#### Mapa")

    mapa = folium.Map(
        location=[9.93, -84.08],
        zoom_start=8
    )

    capa_clientes = folium.FeatureGroup(
        name="Clientes"
    )


    # Clientes
    for cliente in st.session_state.clientes:

        folium.Marker(
            location=[
                cliente["Latitud"],
                cliente["Longitud"]
            ],
            popup=(
                f"<b>{cliente['Nombre']}</b><br>"
                f"Peso: {cliente['Peso']}"
            ),
            tooltip=cliente["Nombre"]
        ).add_to(capa_clientes)


    # Punto óptimo
    if st.session_state.punto_optimo is not None:

        longitud = st.session_state.punto_optimo[0]
        latitud = st.session_state.punto_optimo[1]

        folium.Marker(
            location=[latitud, longitud],
            popup="<b>Centro óptimo</b>",
            tooltip="Centro óptimo",
            icon=folium.Icon(
                color="red",
                icon="star"
            )
        ).add_to(capa_clientes)


    evento_mapa = st_folium(
        mapa,
        height=525,
        key="mapa",
        returned_objects=["last_clicked"],
        feature_group_to_add=capa_clientes,
        use_container_width=True
    )


# =========================================================
# AGREGAR CLIENTE
# =========================================================

if evento_mapa and evento_mapa.get("last_clicked"):

    punto_click = evento_mapa["last_clicked"]

    coordenadas_click = (
        round(punto_click["lat"], 7),
        round(punto_click["lng"], 7)
    )

    if coordenadas_click != st.session_state.ultimo_click:

        nuevo_cliente = {
            "id": st.session_state.siguiente_id,
            "Nombre": (
                f"Cliente "
                f"{st.session_state.siguiente_numero_cliente}"
            ),
            "Latitud": punto_click["lat"],
            "Longitud": punto_click["lng"],
            "Peso": 1.0
        }

        st.session_state.clientes.append(
            nuevo_cliente
        )

        st.session_state.siguiente_id += 1
        st.session_state.siguiente_numero_cliente += 1

        st.session_state.ultimo_click = (
            coordenadas_click
        )

        st.session_state.resultado = None
        st.session_state.punto_optimo = None

        st.rerun()


# =========================================================
# PANEL DERECHO
# =========================================================

with col_panel:

    # -----------------------------------------------------
    # CLIENTES
    # -----------------------------------------------------

    st.markdown("#### Clientes")

    enc1, enc2, enc3 = st.columns(
        [2.2, 1.3, 0.45],
        gap="small"
    )

    enc1.caption("Nombre del cliente")
    enc2.caption("Volumen de ventas")
    enc3.caption("Eliminar")


    if len(st.session_state.clientes) == 0:

        st.info("Haz clic en el mapa para agregar clientes.")

    else:

        for cliente in st.session_state.clientes:

            cliente_id = cliente["id"]

            col_nombre, col_peso, col_borrar = st.columns(
                [2.2, 1.3, 0.45],
                gap="small"
            )

            nuevo_nombre = col_nombre.text_input(
                "Nombre",
                value=cliente["Nombre"],
                key=f"nombre_{cliente_id}",
                label_visibility="collapsed"
            )

            nuevo_peso = col_peso.number_input(
                "Volumen de ventas",
                min_value=0.01,
                value=float(cliente["Peso"]),
                step=1.0,
                key=f"peso_{cliente_id}",
                label_visibility="collapsed",
                help="Volumen relativo de ventas asociado a este cliente."
            )

            cliente["Nombre"] = nuevo_nombre
            cliente["Peso"] = nuevo_peso

            col_borrar.button(
                "×",
                key=f"eliminar_{cliente_id}",
                help="Eliminar cliente",
                on_click=eliminar_cliente,
                args=(cliente_id,)
            )

    # -----------------------------------------------------
    # PARÁMETROS
    # -----------------------------------------------------

    st.markdown("#### Parámetros")

    alpha = st.number_input(
        "Alpha (α)",
        min_value=0.1,
        value=50.0,
        step=10.0,
        format="%.1f",
        help="Controla el tamaño de los pasos del descenso de gradiente."
    )

    tolerancia = st.number_input(
        "Tolerancia",
        min_value=0.000001,
        value=0.0001,
        step=0.0001,
        format="%.6f"
    )

    iteraciones = st.number_input(
        "Iteraciones máximas",
        min_value=1,
        value=100,
        step=10
    )


    # -----------------------------------------------------
    # BOTONES
    # -----------------------------------------------------

    puede_calcular = (
        len(st.session_state.clientes) >= 2
    )

    if not puede_calcular:
        st.caption(
            "Se requieren al menos 2 clientes."
        )


    col_calcular, col_reset = st.columns(
        2,
        gap="small"
    )

    calcular = col_calcular.button(
        "Calcular",
        disabled=not puede_calcular,
        type="primary",
        use_container_width=True
    )

    resetear = col_reset.button(
        "Reiniciar",
        use_container_width=True
    )


    # -----------------------------------------------------
    # RESET
    # -----------------------------------------------------

    if resetear:

        # Limpiar los widgets asociados a cada cliente
        for cliente in st.session_state.clientes:

            cliente_id = cliente["id"]

            st.session_state.pop(
                f"nombre_{cliente_id}",
                None
            )

            st.session_state.pop(
                f"peso_{cliente_id}",
                None
            )

        # Vaciar clientes y resultados
        st.session_state.clientes = []
        st.session_state.resultado = None
        st.session_state.punto_optimo = None

        # Reiniciar contadores
        st.session_state.siguiente_id = 1
        st.session_state.siguiente_numero_cliente = 1

        st.rerun()


    # -----------------------------------------------------
    # CALCULAR
    # -----------------------------------------------------

    if calcular:

        clientes = [
            (
                cliente["Longitud"],
                cliente["Latitud"]
            )
            for cliente
            in st.session_state.clientes
        ]

        pesos = [
            cliente["Peso"]
            for cliente
            in st.session_state.clientes
        ]

        resultado = optimizar_coordenadas_geograficas(
            clientes,
            pesos,
            alpha=alpha,
            max_iteraciones=iteraciones,
            tolerancia=tolerancia
        )

        st.session_state.resultado = resultado
        st.session_state.punto_optimo = (
            resultado["punto_optimo"]
        )

        st.rerun()

# =========================================================
# RESULTADOS
# =========================================================

if st.session_state.resultado is not None:

    resultado = st.session_state.resultado
    punto = resultado["punto_optimo"]

    st.markdown("#### Resultados")

    # -----------------------------------------------------
    # MÉTRICAS PRINCIPALES
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Longitud",
        f"{punto[0]:.5f}"
    )

    col2.metric(
        "Latitud",
        f"{punto[1]:.5f}"
    )

    col3.metric(
        "Costo ponderado",
        f"{resultado['costo_km']:.3f} km"
    )

    col4.metric(
        "Iteraciones",
        resultado["iteraciones"]
    )

    # Estado de convergencia
    if resultado["convergio"]:
        st.success(
            f"Convergencia alcanzada. "
            f"Gradiente final: {resultado['gradiente_final']:.6f}"
        )
    else:
        st.warning(
            f"Se alcanzó el máximo de {resultado['iteraciones']} iteraciones "
            f"sin cumplir la tolerancia. "
            f"Gradiente final: {resultado['gradiente_final']:.6f}"
        )


    # =====================================================
    # PANEL DE ANÁLISIS
    # =====================================================

    col_costo, col_gradiente, col_alpha = st.columns(
        [1.15, 1.15, 1.3],
        gap="medium"
    )


    # -----------------------------------------------------
    # GRÁFICO 1: COSTO
    # -----------------------------------------------------

    with col_costo:

        st.markdown("##### Convergencia del costo")

        datos_costo = pd.DataFrame({
            "Costo": resultado["historial_costos"]
        })

        st.line_chart(
            datos_costo,
            x_label="Iteración",
            y_label="Costo",
            height=260
        )


    # -----------------------------------------------------
    # GRÁFICO 2: GRADIENTE
    # -----------------------------------------------------

    with col_gradiente:

        st.markdown("##### Magnitud del gradiente")

        datos_gradiente = pd.DataFrame({
            "Gradiente": resultado["historial_gradientes"]
        })

        st.line_chart(
            datos_gradiente,
            x_label="Iteración",
            y_label="|∇f|",
            height=260
        )


    # -----------------------------------------------------
    # TABLA: COMPARACIÓN DE ALPHA
    # -----------------------------------------------------

    with col_alpha:

        st.markdown("##### Comparación de α")

        valores_alpha = [
            max(0.1, alpha - 20),
            max(0.1, alpha - 10),
            alpha,
            alpha + 10,
            alpha + 20
        ]

        # Evitar valores repetidos
        valores_alpha = list(dict.fromkeys(valores_alpha))

        filas_alpha = []

        # Los mismos clientes de la optimización principal
        clientes_comparacion = [
            (
                cliente["Longitud"],
                cliente["Latitud"]
            )
            for cliente in st.session_state.clientes
        ]

        pesos_comparacion = [
            cliente["Peso"]
            for cliente in st.session_state.clientes
        ]

        for alpha_prueba in valores_alpha:

            prueba = optimizar_coordenadas_geograficas(
                clientes_comparacion,
                pesos_comparacion,
                alpha=alpha_prueba,
                max_iteraciones=iteraciones,
                tolerancia=tolerancia
            )

            filas_alpha.append({
                "α": alpha_prueba,
                "Iteraciones": prueba["iteraciones"],
                "Costo (km)": round(
                    prueba["costo_km"], 3
                ),
                "Gradiente": round(
                    prueba["gradiente_final"], 6
                ),
                "Convergió": (
                    "Sí"
                    if prueba["convergio"]
                    else "No"
                ),
                "Seleccionado": (
                    "●"
                    if alpha_prueba == alpha
                    else ""
                )
            })

        tabla_alpha = pd.DataFrame(filas_alpha)

        st.dataframe(
            tabla_alpha,
            hide_index=True,
            use_container_width=True,
            height=260
        )