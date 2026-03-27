import streamlit as st
import PyPDF2
import google.generativeai as genai
import json
import os
import re
import base64
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURACION DE PAGINA ---
st.set_page_config(page_title="Menu Pro", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GESTIÓN DEL FONDO ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
NOMBRE_IMAGEN = "Imagen de fondo ChefStock.png"
RUTA_IMAGEN = os.path.join(DIRECTORIO_ACTUAL, NOMBRE_IMAGEN)

logo_b64 = ""
usa_imagen = False

if os.path.exists(RUTA_IMAGEN):
    with open(RUTA_IMAGEN, "rb") as img_file:
        logo_b64 = base64.b64encode(img_file.read()).decode()
    usa_imagen = True

if usa_imagen:
    fondo_html = f"""
    <style>
        /* Engañar a Streamlit para que el fondo sea la pantalla entera */
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{logo_b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Capa oscura para que el texto se lea bien */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.6);
            z-index: -1;
        }}
        
        /* Quitar fondo blanco por defecto */
        .stApp, html, body, [data-testid="stHeader"] {{
            background-color: transparent !important;
            background: transparent !important;
        }}
    </style>
    """
    st.markdown(fondo_html, unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp { background-color: #101010 !important; }</style>", unsafe_allow_html=True)


# --- 3. DISEÑO PREMIUM: MODO APP NATIVA (NUCLEAR) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }
    
    /* 💥 MODO NUCLEAR: ELIMINAR MÁRGENES Y CABECERA DE STREAMLIT */
    [data-testid="stAppViewContainer"] > .main {
        padding: 0px !important;
        margin: 0px !important;
    }
    
    .block-container {
        padding-top: 2rem !important; /* Espacio mínimo para el notch del móvil */
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    header {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}

    /* DISEÑO DE TARJETAS (Cajas de texto y menús) */
    .tarjeta {
        background-color: rgba(30, 30, 30, 0.85); 
        border-radius: 20px; 
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
        border: 1px solid #444444;
        backdrop-filter: blur(10px); 
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(30, 30, 30, 0.85) !important;
        border-radius: 20px !important;
        border: 1px solid #444444 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        padding: 15px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* 🔥 BOTONES PRINCIPALES (Grandes y redondeados para móvil) */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #FF007F 0%, #B0005D 100%) !important;
        color: white !important; 
        border-radius: 50px !important; 
        font-size: 20px !important; 
        font-weight: 800 !important; 
        border: none !important; 
        box-shadow: 0 8px 25px rgba(255, 0, 127, 0.4) !important; 
        width: 50%; 
        min-height: 65px !important; 
        margin-bottom: 15px;
        transition: all 0.2s ease;
    }
    [data-testid="baseButton-primary"]:active { 
        transform: scale(0.96) !important; 
    }
    
    /* 💦 BOTONES SECUNDARIOS (Para menús y opciones) */
    [data-testid="baseButton-secondary"] {
        background-color: rgba(26, 26, 26, 0.7) !important; 
        color: #00FFFF !important;
        border: 2px solid #00FFFF !important; 
        border-radius: 50px !important; 
        font-size: 18px !important; 
        font-weight: 800 !important; 
        width: 100%; 
        min-height: 60px !important; 
        margin-bottom: 15px;
        backdrop-filter: blur(5px);
    }
    [data-testid="baseButton-secondary"]:active {
        background-color: rgba(0, 255, 255, 0.2) !important; 
    }

    /* ENTRADAS DE TEXTO Y DESPLEGABLES */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        background-color: rgba(26, 26, 26, 0.9) !important; 
        border: 1px solid #666 !important; 
        border-radius: 20px !important; 
        color: #FFFFFF !important; 
        padding: 15px !important;
        font-size: 16px !important;
    }
    
    /* TEXTOS */
    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2, 
    div[data-testid="stMarkdownContainer"] h3, 
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stMarkdownContainer"] span.texto-rosa { color: #FF007F !important; }
    div[data-testid="stMarkdownContainer"] span.texto-cyan { color: #00FFFF !important; }

    h1 { font-weight: 800; text-align: center; font-size: 3rem !important; margin-bottom: 0px; text-shadow: 2px 2px 10px rgba(0,0,0,0.8); }
    h2, h3 { font-weight: 800; text-align: center; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); }
    .subtitulo { text-align: center; margin-bottom: 30px; font-size: 1.1rem; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); color: #ddd;}
</style>
""", unsafe_allow_html=True)

# --- ENRUTAMIENTO ---
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nueva_pagina):
    st.session_state['pagina_actual'] = nueva_pagina
    st.rerun() 

# --- 4. CONFIGURACION DE IA Y FIREBASE ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("❌ Error crítico: No encuentro 'GEMINI_API_KEY' en .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# Inicializar Firebase
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("firebase_key.json")
            
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Error crítico al conectar con Firebase: {e}")
        st.stop()
        
db = firestore.client()

# --- FUNCIONES DE NUBE ---
def cargar_nube(documento, por_defecto):
    try:
        doc_ref = db.collection('app_data').document(documento)
        doc = doc_ref.get(timeout=10) 
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        st.warning(f"⚠️ Nota: Usando datos locales temporales para {documento}")
    return por_defecto

def guardar_nube(documento, datos):
    doc_ref = db.collection('app_data').document(documento)
    doc_ref.set(datos)

despensa = cargar_nube('mi_despensa', {})
perfil = cargar_nube('mi_perfil', {"comensales": 2, "edades": "Ej: 2 adultos", "dieta": "Mediterránea", "alergias": "", "odios": "", "calorias": 2350, "tiempo": "Indiferente"})
favoritos = cargar_nube('mis_favoritos', {})

# --- FUNCIONES DE PROCESAMIENTO ---
def calcular_unidades_reales(nombre_ticket, cantidad_comprada, precio_total_ticket, catalogo):
    nombre_limpio = nombre_ticket.lower().strip()
    precio_unitario_ticket = precio_total_ticket / cantidad_comprada if cantidad_comprada > 0 else precio_total_ticket
    mejor_coincidencia = None
    menor_diferencia = 999.0
    
    for nombre_cat, datos in catalogo.items():
        if nombre_limpio in nombre_cat and ("frit" not in nombre_cat if "frit" not in nombre_limpio else True):
            try: precio_cat = float(datos.get("precio", 0.0))
            except: precio_cat = 0.0
            diferencia = abs(precio_cat - precio_unitario_ticket)
            if diferencia < menor_diferencia:
                menor_diferencia = diferencia
                mejor_coincidencia = datos

    if mejor_coincidencia:
        formato = mejor_coincidencia.get("formato", "1 ud").lower()
        match_kg = re.search(r'(\d+[.,]?\d*)\s*kg', formato)
        if match_kg:
            return int(cantidad_comprada * float(match_kg.group(1).replace(',', '.')) * 1000), f"{float(match_kg.group(1).replace(',', '.'))} kg"
        match_ud = re.search(r'(\d+)\s*ud', formato)
        if match_ud:
            return int(cantidad_comprada * int(match_ud.group(1))), f"{int(match_ud.group(1))} ud"
    return int(cantidad_comprada), 1

def procesar_compra_pdf(pdf_file, nombres_existentes):
    texto_pdf = " ".join([pagina.extract_text() for pagina in PyPDF2.PdfReader(pdf_file).pages])
    prompt = f"""Eres un asistente de cocina profesional. Lee esta lista de ticket: {texto_pdf}
    TAREA: Extrae ÚNICAMENTE productos de ALIMENTACIÓN.
    REGLA CLAVE: Devuelve un JSON donde cada producto tenga 'cantidad' y 'precio' (el TOTAL en euros).
    Ejemplo: {{"pechuga de pollo": {{"cantidad": 1, "precio": 4.65}}}}"""
    respuesta = model.generate_content(prompt)
    return json.loads(respuesta.text.replace("```json", "").replace("```", "").strip())

def cocinar_y_descontar(despensa, perfil, antojo_hoy):
    calorias_obj = perfil.get('calorias', 2350)
    prompt = f"""Eres un Elite Chef y Nutricionista de la aplicación MenuPro.
    Despensa actual (JSON): {json.dumps(despensa, ensure_ascii=False)}
    REGLAS: Comensales {perfil.get('comensales', 2)}, Edades: {perfil.get('edades', 'Adultos')}, Dieta: {perfil.get('dieta', 'Ninguna')}, Alergias: {perfil.get('alergias', 'Ninguna')}
    ANTOJO DEL USUARIO: "{antojo_hoy if antojo_hoy else 'Ninguno'}"
    
    INSTRUCCIONES CLAVE:
    1. Si el usuario TIENE UN ANTOJO ESPECÍFICO (Ej: "Paella de marisco"):
       - Piensa en la receta real para ese plato.
       - Revisa estrictamente la "Despensa actual".
       - SI FALTAN INGREDIENTES CLAVE: Sé honesto. Dile amablemente que no se puede cocinar, haz una lista viñeteada de exactamente qué ingredientes le faltan comprar en el supermercado, y DETÉNTE AQUÍ (NO generes pasos de receta ni la sección de consumo).
       - SI HAY INGREDIENTES (o sustitutos muy válidos): Dale la receta paso a paso.
    2. Si NO HAY ANTOJO:
       - Invéntate un menú delicioso y sano usando ÚNICAMENTE lo que hay en la despensa.
    3. SOLO si has dado una receta que se va a cocinar hoy, añade AL FINAL EXACTAMENTE ESTA PALABRA: "---CONSUMO---" seguido de un JSON SOLO con lo que se va a gastar. Si denegaste el plato por falta de ingredientes, NO ESCRIBAS "---CONSUMO---".
    """
    return model.generate_content(prompt).text


# ==========================================
# 🏠 PANTALLA 1: INICIO (MENÚ PRINCIPAL)
# ==========================================
if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<h1>Menu<span class='texto-rosa'>Pro</span></h1>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Tu nutrición es importante</div>", unsafe_allow_html=True)

    if st.button("👤 ESTADO DE MI PERFIL", type="secondary"):
        cambiar_pagina('Perfil')
        
    if st.button("📦 GESTIÓN DE DESPENSA", type="secondary"):
        cambiar_pagina('Despensa')
        
    if st.button("⭐ MIS FAVORITOS", type="secondary"):
        cambiar_pagina('Favoritos')
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.text_area("✍️ ¿Algún antojo o petición especial para hoy?", key="antojo_hoy", placeholder="Ej: Pescado al horno...", height=100)
    
    if st.button("🍳 GENERAR MI MENÚ ", type="primary"):
        if not despensa:
            st.error("No hay ingredientes en la despensa. Ve a 'Gestión de Despensa'.")
        else:
            with st.spinner("Conectando con el Chef..."):
                try:
                    res = cocinar_y_descontar(despensa, perfil, st.session_state.get('antojo_hoy', ''))
                    st.session_state['menu_borrador'] = res
                except Exception as e:
                    st.error(f"Error: {e}")

    if 'menu_borrador' in st.session_state:
        res = st.session_state['menu_borrador']
        
        if "---CONSUMO---" in res:
            partes = res.split("---CONSUMO---")
            st.markdown(f"<div class='tarjeta'>{partes[0]}</div>", unsafe_allow_html=True)
            try:
                gastado = json.loads(partes[1].strip().replace("```json", "").replace("```", ""))
                st.markdown(f"<p style='font-weight:bold;'>Previsión de gasto:</p>", unsafe_allow_html=True)
                for i, (ing, cant_g) in enumerate(gastado.items()):
                    st.markdown(f"<span class='texto-cyan' style='font-weight:bold;'>{i + 1}. {ing.capitalize()}</span> <span>➔ `{cant_g}`</span>", unsafe_allow_html=True)
                
                st.write("")
                
                with st.container(border=True):
                    nombre_fav = st.text_input("Dale un nombre para favoritos:", placeholder="Ej: Pollo crujiente", key="input_fav")
                    if st.button("⭐ Guardar", use_container_width=True):
                        nombre_final = nombre_fav if nombre_fav else f"Menú #{len(favoritos) + 1}"
                        favoritos[nombre_final] = {"receta": partes[0], "ingredientes": gastado}
                        guardar_nube('mis_favoritos', favoritos)
                        st.success("¡Guardado!")
                
                st.write("")
                if st.button("✅ Cocinar y Descontar", type="primary"):
                    for ing, cant_g in gastado.items():
                        ing_l = ing.lower()
                        if ing_l in despensa:
                            despensa[ing_l] -= cant_g
                            if despensa[ing_l] <= 0: del despensa[ing_l]
                    guardar_nube('mi_despensa', despensa)
                    del st.session_state['menu_borrador']
                    st.success("¡Ingredientes consumidos!")
                    st.rerun()
                
                if st.button("❌ Descartar Menú", type="secondary"):
                    del st.session_state['menu_borrador']
                    st.rerun()
            except json.JSONDecodeError:
                st.error("Error al leer consumo.")
                
        else:
            st.markdown(f"<div class='tarjeta' style='border-color:#FF007F;'>{res}</div>", unsafe_allow_html=True)
            if st.button("Cerrar Aviso", type="secondary"):
                del st.session_state['menu_borrador']
                st.rerun()

# ==========================================
# ⭐ PANTALLA NUEVA: MIS FAVORITOS
# ==========================================
elif st.session_state['pagina_actual'] == 'Favoritos':
    if st.button("🔙 Volver al Inicio", type="primary"):
        cambiar_pagina('Inicio')
        
    st.markdown("<h2>MIS <span class='texto-rosa'>FAVORITOS</span></h2>", unsafe_allow_html=True)

    if not favoritos:
        st.info("Aún no tienes menús guardados.")
    else:
        for nombre_menu, datos_menu in favoritos.items():
            with st.expander(f"⭐ {nombre_menu}"):
                st.markdown(datos_menu["receta"], unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                if st.button(f"🍳 Cocinar hoy", key=f"cocinar_{nombre_menu}", type="primary"):
                    faltantes = []
                    for ing, cant_necesaria in datos_menu["ingredientes"].items():
                        cant_actual = despensa.get(ing.lower(), 0)
                        if cant_actual < cant_necesaria:
                            faltantes.append(f"{ing.capitalize()} ({cant_actual} / {cant_necesaria})")
                    
                    if faltantes:
                        st.error("Faltan ingredientes:")
                        for f in faltantes: st.write(f"- {f}")
                    else:
                        for ing, cant_necesaria in datos_menu["ingredientes"].items():
                            ing_l = ing.lower()
                            despensa[ing_l] -= cant_necesaria
                            if despensa[ing_l] <= 0: del despensa[ing_l]
                        guardar_nube('mi_despensa', despensa)
                        st.success("¡Ingredientes consumidos!")
                        st.balloons() 
                        
                if st.button(f"🗑️ Borrar", key=f"borrar_{nombre_menu}", type="secondary"):
                    del favoritos[nombre_menu]
                    guardar_nube('mis_favoritos', favoritos)
                    st.rerun()

# ==========================================
# 👤 PANTALLA 2: MI PERFIL
# ==========================================
elif st.session_state['pagina_actual'] == 'Perfil':
    if st.button("🔙 Volver al Inicio", type="primary"):
        cambiar_pagina('Inicio')
        
    st.markdown("<h2>MI <span class='texto-rosa'>PERFIL</span></h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        opciones_dieta = ["Mediterránea", "Vegetariana", "Vegana", "Keto", "Baja en calorías", "Ninguna"]
        idx_dieta = opciones_dieta.index(perfil.get("dieta", "Mediterránea")) if perfil.get("dieta", "Mediterránea") in opciones_dieta else 0
        
        p_comensales = st.number_input("Comensales", min_value=1, value=perfil.get("comensales", 2))
        p_dieta = st.selectbox("Tipo de Dieta", opciones_dieta, index=idx_dieta)
        p_calorias = st.number_input("Objetivo Kcal (Adulto)", min_value=1000, max_value=5000, value=perfil.get("calorias", 2350), step=50)
        
        op_tiempo = ["Indiferente", "Rápida (< 20 min)", "Media (20 - 45 min)", "Elaborada (> 45 min)"]
        p_tiempo = st.selectbox("Tiempo Prep.", op_tiempo, index=op_tiempo.index(perfil.get("tiempo", "Indiferente")))

        p_edades = st.text_input("Perfil Comensales (Edades)", value=perfil.get("edades", "Adultos"))
        p_alergias = st.text_input("Alergias Clínicas", value=perfil.get("alergias", ""))
        
        st.write("")
        if st.button("💾 GUARDAR CAMBIOS", type="primary"):
            perfil.update({"comensales": p_comensales, "edades": p_edades, "dieta": p_dieta, "alergias": p_alergias, "calorias": p_calorias, "tiempo": p_tiempo})
            guardar_nube('mi_perfil', perfil)
            st.success("Perfil guardado.")

# ==========================================
# 📦 PANTALLA 3: MI DESPENSA
# ==========================================
elif st.session_state['pagina_actual'] == 'Despensa':
    if st.button("🔙 Volver al Inicio", type="primary"):
        cambiar_pagina('Inicio')

    st.markdown("<h2>MI <span class='texto-rosa'>DESPENSA</span></h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<p style='font-weight:bold; text-align:center;'>📄 ESCANEAR TICKET PDF</p>", unsafe_allow_html=True)
        supermercado_elegido = st.selectbox("Súper del ticket:", ("Elige uno...", "Mercadona", "DIA", "Carrefour"), index=0)
        
        if supermercado_elegido != "Elige uno...":
            documento_firebase = f"catalogo_{supermercado_elegido.lower()}"
            catalogo_activo = cargar_nube(documento_firebase, {})
            
            if not catalogo_activo:
                st.error(f"Falta catálogo de {supermercado_elegido}.")
            else:
                st.success(f"Catálogo listo ({len(catalogo_activo)} prod).")
                archivo = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
                
                if archivo and st.button("Procesar Ticket PDF", type="primary"):
                    with st.spinner("Procesando..."):
                        try:
                            nuevos = procesar_compra_pdf(archivo, list(despensa.keys()))
                            for ing, datos_t in nuevos.items():
                                c = datos_t.get("cantidad", 1) if isinstance(datos_t, dict) else datos_t
                                p = datos_t.get("precio", 0.0) if isinstance(datos_t, dict) else 0.0
                                c_real, mult = calcular_unidades_reales(ing.lower(), c, p, catalogo_activo)
                                despensa[ing.lower()] = despensa.get(ing.lower(), 0) + c_real
                            guardar_nube('mi_despensa', despensa)
                            st.success("Añadido.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    with st.container(border=True):
        st.markdown("<p style='font-weight:bold; text-align:center;'>✍🏻 AÑADIR MANUAL</p>", unsafe_allow_html=True)
        nuevo_nom = st.text_input("Ingrediente", placeholder="Ej: Pollo")
        cant_man = st.number_input("Cantidad", min_value=0.0, step=1.0)
        un_man = st.selectbox("Medida", ["Gramos", "Kilos", "Litros", "Unidades"])
        if st.button("Añadir", type="primary") and nuevo_nom:
            c_fin = cant_man * 1000 if un_man in ["Kilos", "Litros"] else cant_man
            nom_l = nuevo_nom.lower().strip()
            despensa[nom_l] = despensa.get(nom_l, 0) + int(c_fin) if c_fin.is_integer() else c_fin
            guardar_nube('mi_despensa', despensa)
            st.success("Añadido.")
            st.rerun()

    st.write("")
    if 'mostrar_inventario' not in st.session_state: st.session_state['mostrar_inventario'] = False
    texto_boton = "🙈 Ocultar Inventario" if st.session_state['mostrar_inventario'] else "🔍 Ver Inventario Actual"
    
    if st.button(texto_boton, type="secondary"):
        st.session_state['mostrar_inventario'] = not st.session_state['mostrar_inventario']
        st.rerun()

    if st.session_state['mostrar_inventario']:
        with st.container(border=True):
            if not despensa:
                st.info("Despensa vacía.")
            else:
                for i, (ing, cant) in enumerate(despensa.items()):
                    st.markdown(f"**{i + 1}. {ing.capitalize()}**: `{cant} g/ud`")
                
                st.markdown("<hr>", unsafe_allow_html=True)
                ing_elegido = st.selectbox("Editar/Borrar:", list(despensa.keys()))
                if ing_elegido:
                    cant_act = float(despensa[ing_elegido])
                    n_cant = st.number_input(f"Cantidad actual:", min_value=0.0, value=cant_act, step=1.0)
                    
                    if st.button("Actualizar Cantidad", type="primary"):
                        if n_cant <= 0: del despensa[ing_elegido]
                        else: despensa[ing_elegido] = n_cant
                        guardar_nube('mi_despensa', despensa)
                        st.rerun()
                        
                    if st.button("🗑️ Borrar Ingrediente", type="secondary"):
                        del despensa[ing_elegido]
                        guardar_nube('mi_despensa', despensa)
                        st.rerun()
                        
            st.write("")
            if st.button("❌ Vaciar Despensa Completa", type="secondary"):
                guardar_nube('mi_despensa', {})
                st.rerun()
