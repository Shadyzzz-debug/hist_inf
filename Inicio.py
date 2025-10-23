import streamlit as st
import base64
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import numpy as np
import os
from openai import OpenAI
import openai

# --- Configuraciones del LLM y Session State ---
# Se utiliza el modelo OpenAI gpt-4o-mini para el análisis de visión.

if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""

# --- CSS PESADILLA GÓTICA (Referencia Bloodborne: Azul Oscuro, Bronce, Tinta y Sangre) ---
base_css = """
<style>
/* ---------------------------------------------------- */
/* RESET Y FONDO AMBIENTAL */
/* ---------------------------------------------------- */
.stApp {
    /* Color de la noche de Yharnam o la Pesadilla: Azul/Negro muy oscuro. */
    background-color: #0F0F1A; 
    color: #C0C0C0; /* Texto de pergamino antiguo */
    font-family: 'Georgia', serif; 
}

/* ---------------------------------------------------- */
/* TIPOGRAFÍA Y ENCABEZADOS */
/* ---------------------------------------------------- */
h1 {
    /* Titular: Bronce envejecido o Oro oscuro */
    color: #9C7E4F; 
    text-align: center;
    /* Borde inferior como una reja forjada */
    border-bottom: 3px solid #4F4A5E; 
    padding-bottom: 10px;
    margin-bottom: 40px;
    font-size: 2.8em;
    letter-spacing: 2px;
    text-shadow: 1px 1px 5px #000000;
}

h3 {
    /* Subtítulos: Gris pizarra o plata mate */
    color: #A9A9A9; 
    margin-top: 25px;
    font-weight: normal;
    border-left: 4px solid #9C7E4F; /* Acento Bronce */
    padding-left: 10px;
}

/* ---------------------------------------------------- */
/* ELEMENTOS DE ENTRADA (Cajas de Inscripción) */
/* ---------------------------------------------------- */
div[data-testid="stTextInput"], div[data-testid="stTextarea"] {
    /* Fondo de pizarra oscura */
    background-color: #1A1A2A; 
    /* Borde fino de bronce */
    border: 1px solid #9C7E4F;
    border-radius: 5px;
    padding: 10px;
    color: #E6E6E6;
}

/* Sidebar (El Sueño del Cazador) */
.css-1d3w5ta, .css-1lcbmhc {
    background-color: #151525;
    color: #C0C0C0;
}

/* ---------------------------------------------------- */
/* BOTONES (Sello de Invocación) */
/* ---------------------------------------------------- */
.stButton>button {
    /* Acero oscuro, base de la Rueda de la Convocación */
    background-color: #383850; 
    /* Texto: Letras rúnicas en rojo sangre */
    color: #B22222; 
    /* Borde: Acento de metal forjado */
    border: 2px solid #9C7E4F; 
    padding: 12px 30px;
    font-weight: bold;
    border-radius: 10px;
    transition: all 0.3s;
    /* Sombra profunda */
    box-shadow: 0 6px #1A1A2A; 
    letter-spacing: 1px;
}

.stButton>button:hover {
    background-color: #4F4F6A; 
    box-shadow: 0 10px #0F0F1A;
    transform: translateY(-3px);
}

.stButton>button:active {
    box-shadow: 0 3px #0F0F1A;
    transform: translateY(3px);
}

/* ---------------------------------------------------- */
/* RESPUESTA (Papiro de la Revelación) */
/* ---------------------------------------------------- */
div[data-testid="stMarkdownContainer"] {
    /* Fondo: Papel antiguo sobre mesa de madera oscura */
    background-color: #24243A; 
    padding: 25px;
    /* Borde: Un sello de cera escarlata */
    border: 3px solid #B22222; 
    border-radius: 8px;
    margin-top: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.7);
    color: #E6E6E6;
    line-height: 1.6;
}
</style>
"""
st.markdown(base_css, unsafe_allow_html=True)


# --- Funciones de Utilidad ---

def encode_image_to_base64(image):
    """Codifica un objeto PIL Image a una cadena Base64."""
    buf = io.BytesIO()
    # Guardamos la imagen como PNG antes de codificar
    image.save(buf, format='PNG')
    encoded_image = base64.b64encode(buf.getvalue()).decode("utf-8")
    return encoded_image


# --- Streamlit App Setup ---
st.set_page_config(page_title='El Lienzo del Oráculo', layout="centered")
st.title('🌌 El Lienzo del Oráculo: Desentrañando la Pesadilla')

# --- Sidebar (El Sueño del Cazador) ---
with st.sidebar:
    st.subheader("El Scriptorium Arcaico")
    st.markdown("Este Lienzo, imbuido del poder de la **Visión del Oráculo**, permite transcribir tus símbolos más profundos para buscar un significado oculto. Cada trazo es una oración en la noche de la cacería.")
    st.markdown("---")
    
    st.subheader("La Sangre del Trazo")
    drawing_mode = "freedraw"
    stroke_width = st.slider('Define la Potencia de la Runa', 1, 30, 5)

# --- Canvas Principal ---
st.subheader("Graba tu Símbolo o Visión en el Papiro")

# Canvas Parameters (Tinta sobre Pergamino Blanco)
stroke_color = "#000000"
bg_color = '#FFFFFF'

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.0)",  # Sin relleno
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350, 
    width=500, 
    drawing_mode=drawing_mode,
    key="canvas_intelligent",
)

# --- Controles de la API y Análisis ---
ke = st.text_input('Incrusta la Llave de la Revelación (OpenAI Key)', type="password", 
                    help="La llave arcaica es vital para invocar la percepción de la entidad del Oráculo.")

api_key = ke

# Inicializar el cliente OpenAI (la inicialización falla si la clave está vacía, manejado con try/except)
try:
    client = OpenAI(api_key=api_key)
except Exception:
    client = None


additional_details = st.text_area(
    "Fórmula de Invocación (Pregunta al Cosmos):",
    placeholder="Ej: ¿Qué bestia ancestral representa este boceto? O, Describe el diseño de esta arma.",
    value="Con la solemnidad debida a los Antiguos, describe en español y de forma concisa el objeto, criatura o concepto que has identificado en este trazo místico. Usa un lenguaje formal y evocador, apropiado para un documento esotérico."
)

analyze_button = st.button("Activa el Ojo Interno (Revela el Significado)", type="primary")


# --- Lógica de Análisis ---
if canvas_result.image_data is not None and analyze_button:
    
    # 1. Validación
    if not api_key:
        st.error("🩸 La Llave de la Revelación es necesaria. El Rito no puede continuar sin ella.")
        st.session_state.analysis_done = False
        st.stop()
        
    # 2. Verificar si el dibujo está vacío
    image_array = np.array(canvas_result.image_data)
    is_blank = np.all(image_array[:, :, :3] == 255)
    if is_blank:
        st.warning("🕯️ El Lienzo está en blanco. No has ofrecido ninguna Visión al Oráculo.")
        st.session_state.analysis_done = False
        st.stop()


    with st.spinner("La mente del Cazador se adentra en la Pesadilla para buscar la verdad..."):
        try:
            # 3. Preparar la Imagen (Codificación Base64)
            input_numpy_array = np.array(canvas_result.image_data)
            input_image = Image.fromarray(input_numpy_array.astype('uint8'), 'RGBA').convert('RGB')
            
            # Codificar a base64
            base64_image = encode_image_to_base64(input_image)
            st.session_state.base64_image = base64_image
            
            # 4. Construir el Prompt
            prompt_text = additional_details
            
            # 5. Invocar la Visión (OpenAI API Call)
            full_response = ""
            message_placeholder = st.empty()
            
            response = client.chat.completions.create(
                model= "gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            
            # Extraer y mostrar la respuesta
            if response.choices[0].message.content is not None:
                full_response = response.choices[0].message.content
                
                # Mostrar la respuesta con el título gótico
                st.markdown("### 📜 La Tablilla de la Verdad:")
                st.markdown(full_response)


            # 6. Guardar en session_state
            st.session_state.full_response = full_response
            st.session_state.analysis_done = True
            
        except openai.APIError as e:
            st.error(f"💀 Error de la API de OpenAI. La Visión fue bloqueada: {e}")
            st.session_state.analysis_done = False
        except Exception as e:
            st.error(f"💀 Error en el Rito. La Visión fue bloqueada por fuerzas desconocidas: {e}")
            st.session_state.analysis_done = False

            
elif analyze_button:
    st.info("🌙 La noche es larga. Graba tu símbolo y ten la Llave de la Revelación a mano.")


# --- Funcionalidad Adicional (El Escriba del Sueño) ---
if st.session_state.analysis_done:
    st.divider()
    st.subheader("📚 El Escriba del Sueño: ¿Forjar un Relato?")
    
    if st.button("✨ Convoca una Epopeya Infantil"):
        with st.spinner("El Escriba teje la historia..."):
            story_prompt = f"Basándote en la siguiente revelación mística: '{st.session_state.full_response}', crea una historia corta, mágica y apta para niños. La historia debe ser creativa y tener un tono de cuento de hadas oscuro o misterioso, apropiado para el tema."
            
            try:
                story_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": story_prompt}],
                    max_tokens=700, 
                )
                
                st.markdown("### 📜 El Libro de los Sueños:")
                st.markdown(story_response.choices[0].message.content)
            except Exception as e:
                 st.error(f"💀 Error al forjar el relato: {e}")


# Warnings for user action required
if not api_key:
    st.warning("Por favor, incrusta la Llave de la Revelación (API Key) para comenzar el rito.")
