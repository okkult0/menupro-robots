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
st.set_page_config(page_title="Menu Pro", page_icon="👩🏻‍🍳", layout="centered", initial_sidebar_state="collapsed")

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
else:
    pass 

if usa_imagen:
    fondo_html = f"""
    <style>
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: transparent !important;
            background: transparent !important;
        }}
        
        #mi-fondo-nuclear {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url("data:image/png;base64,{logo_b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: -99999; 
        }}
        
        #mi-fondo-nuclear::after {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.40); 
        }}
    </style>
    <div id="mi-fondo-nuclear"></div>
    """
    st.markdown(fondo_html, unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp { background-color: #101010 !important; }</style>", unsafe_allow_html=True)


# --- 3. DISEÑO PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }
    footer { display: none !important; }

    .tarjeta {
        background-color: rgba(30, 30, 30, 0.85); 
        border-radius: 20px; 
        padding: 30px;
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

    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #FF007F 0%, #B0005D 100%) !important;
        color: white !important; 
        border-radius: 50px !important; 
        padding: 20px !important; 
        font-size: 22px !important; 
        font-weight: 800 !important; 
        border: none !important; 
        box-shadow: 0 8px 25px rgba(255, 0, 127, 0.4) !important; 
        width: 100%; 
        min-height: 80px !important; 
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    [data-testid="baseButton-primary"]:hover { 
        transform: translateY(-3px) scale(1.02) !important; 
        box-shadow: 0 12px 30px rgba(255, 0, 127, 0.6) !important; 
    }
    
    [data-testid="baseButton-secondary"] {
        background-color: rgba(26, 26, 26, 0.7) !important; 
        color: #00FFFF !important;
        border: 2px solid #00FFFF !important; 
        border-radius: 50px !important; 
        font-size: 20px !important; 
        font-weight: 800 !important; 
        width: 100%; 
        min-height: 90px !important; 
        margin-bottom: 20px;
        transition: all 0.3s ease;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(5px);
    }
    [data-testid="baseButton-secondary"]:hover {
        background-color: rgba(0, 255, 255, 0.1) !important; 
        transform: translateY(-4px) !important;
        box-shadow: 0 10px 20px rgba(0, 255, 255, 0.2) !important;
    }

    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        background-color: rgba(26, 26, 26, 0.8) !important; border: 1px solid #555555 !important; 
        border-radius: 25px !important; color: #FFFFFF !important; padding: 15px 20px !important;
        font-size: 16px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border: 1px solid #00FFFF !important; box-shadow: 0 0 10px rgba(0, 255, 255, 0.2) !important;
    }
    
    [data-testid="stExpander"] {
        background-color: rgba(30, 30, 30, 0.85) !important;
        border-radius: 15px !important;
        border: 1px solid #444444 !important;
        backdrop-filter: blur(10px) !important;
    }
    [data-testid="stExpander"] summary p {
        color: #00FFFF !important;
        font-weight: 800 !important;
        font-size: 18px !important;
    }

    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2, 
    div[data-testid="stMarkdownContainer"] h3, 
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important; 
    }
    
    div[data-testid="stMarkdownContainer"] span.texto-rosa {
        color: #FF007F !important;
        -webkit-text-fill-color: #FF007F !important;
    }
    
    div[data-testid="stMarkdownContainer"] span.texto-cyan {
        color: #00FFFF !important;
        -webkit-text-fill-color: #00FFFF !important;
    }

    h1 { font-weight: 800; text-align: center; font-size: 3.5rem !important; margin-bottom: 0px; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    h2, h3 { font-weight: 800; text-align: center; text-shadow: 1px 1px 5px rgba(0,0,0,0.5); }
    .subtitulo { text-align: center; margin-bottom: 40px; font-size: 1.2rem; text-shadow: 1px 1px 5px rgba(0,0,0,0.5); }
    
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

# Inicializar Firebase (Solo 1 vez)
# Inicializar Firebase (Preparado para la Nube y Local)
if not firebase_admin._apps:
    try:
        # 1. Intentamos leer desde los Secretos de Streamlit (Para la Nube)
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        # 2. Si no estamos en la nube, usamos el archivo local (Para tu PC)
        else:
            cred = credentials.Certificate("firebase_key.json")
            
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Error crítico al conectar con Firebase: {e}")
        st.stop()
        
db = firestore.client()

# --- FUNCIONES DE NUBE ---
def cargar_nube(documento, por_defecto):
    doc_ref = db.collection('app_data').document(documento)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return por_defecto

def guardar_nube(documento, datos):
    doc_ref = db.collection('app_data').document(documento)
    doc_ref.set(datos)

# --- CARGA DE DATOS DESDE FIREBASE ---
despensa = cargar_nube('mi_despensa', {})
perfil = cargar_nube('mi_perfil', {"comensales": 2, "edades": "Ej: 2 adultos", "dieta": "Mediterránea", "alergias": "", "odios": "", "calorias": 2350, "tiempo": "Indiferente"})
favoritos = cargar_nube('mis_favoritos', {})

# Los catálogos de los supermercados se siguen cargando en local (por ahora)
def cargar_catalogo_local(archivo, por_defecto):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return por_defecto


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

    _, col_centro, _ = st.columns([1, 8, 1])
    
    with col_centro:
        if st.button("👤 ESTADO DE MI PERFIL", type="secondary", use_container_width=True):
            cambiar_pagina('Perfil')
            
        if st.button("📦 GESTIÓN DE DESPENSA", type="secondary", use_container_width=True):
            cambiar_pagina('Despensa')
            
        if st.button("⭐ MIS FAVORITOS", type="secondary", use_container_width=True):
            cambiar_pagina('Favoritos')
            
        st.markdown("<br><hr style='border:1px solid #333;'><br>", unsafe_allow_html=True)
        
        st.text_area("✍️ ¿Algún antojo o petición especial para hoy?", key="antojo_hoy", placeholder="Ej: Pescado al horno...")
        
        if st.button("🍳 GENERAR MI MENÚ ", type="primary", use_container_width=True):
            if not despensa:
                st.error("No hay ingredientes en la despensa. Ve a 'Gestión de Despensa' a añadir ingredientes.")
            else:
                with st.spinner("Conectando con el Chef, preparando la cocina..."):
                    try:
                        res = cocinar_y_descontar(despensa, perfil, st.session_state.get('antojo_hoy', ''))
                        st.session_state['menu_borrador'] = res
                    except Exception as e:
                        st.error(f"Error fatal: {e}")

        if 'menu_borrador' in st.session_state:
            res = st.session_state['menu_borrador']
            
            if "---CONSUMO---" in res:
                partes = res.split("---CONSUMO---")
                st.markdown(f"<div class='tarjeta'>{partes[0]}</div>", unsafe_allow_html=True)
                try:
                    gastado = json.loads(partes[1].strip().replace("```json", "").replace("```", ""))
                    st.markdown(f"<p>Previsión de ingredientes necesario:</p>", unsafe_allow_html=True)
                    for i, (ing, cant_g) in enumerate(gastado.items()):
                        st.markdown(f"<span class='texto-cyan' style='font-weight:800;'>{i + 1}. {ing.capitalize()}</span> <span>➔ `{cant_g}`</span>", unsafe_allow_html=True)
                    
                    st.write("")
                    
                    with st.container(border=True):
                        st.markdown("<p style='text-align:center;'>¿Te gusta este menú? Guárdalo en favoritos:</p>", unsafe_allow_html=True)
                        nombre_fav = st.text_input("Dale un nombre:", placeholder="Ej: Pollo crujiente de la Abuela", key="input_fav")
                        if st.button("⭐ Guardar en Favoritos", use_container_width=True):
                            nombre_final = nombre_fav if nombre_fav else f"Menú #{len(favoritos) + 1}"
                            favoritos[nombre_final] = {"receta": partes[0], "ingredientes": gastado}
                            guardar_nube('mis_favoritos', favoritos)
                            st.success(f"¡'{nombre_final}' guardado con éxito!")
                    
                    st.write("")
                    col_ok, col_ko = st.columns(2)
                    with col_ok:
                        if st.button("✅ Cocinar y Descontar", use_container_width=True):
                            for ing, cant_g in gastado.items():
                                ing_l = ing.lower()
                                if ing_l in despensa:
                                    despensa[ing_l] -= cant_g
                                    if despensa[ing_l] <= 0: del despensa[ing_l]
                            guardar_nube('mi_despensa', despensa)
                            del st.session_state['menu_borrador']
                            st.success("¡Ingredientes consumidos! 🍳.")
                            st.rerun()
                    with col_ko:
                        if st.button("❌ Descartar Menú", use_container_width=True):
                            del st.session_state['menu_borrador']
                            st.rerun()
                except json.JSONDecodeError:
                    st.error("Error al leer consumo.")
                    
            else:
                st.markdown(f"<div class='tarjeta' style='border-color:#FF007F;'>{res}</div>", unsafe_allow_html=True)
                if st.button("Cerrar Aviso", use_container_width=True):
                    del st.session_state['menu_borrador']
                    st.rerun()


# ==========================================
# ⭐ PANTALLA NUEVA: MIS FAVORITOS
# ==========================================
elif st.session_state['pagina_actual'] == 'Favoritos':
    col_volver, _ = st.columns([1, 2])
    with col_volver:
        if st.button("🔙 Volver al Inicio", type="primary", use_container_width=True):
            cambiar_pagina('Inicio')
            
    st.markdown("<h2>MIS <span class='texto-rosa'>FAVORITOS</span></h2>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Tu colección de menús estrella</div>", unsafe_allow_html=True)

    if not favoritos:
        st.info("Aún no tienes menús guardados. ¡Ve a Inicio, genera uno y guárdalo!")
    else:
        for nombre_menu, datos_menu in favoritos.items():
            with st.expander(f"⭐ {nombre_menu}"):
                st.markdown(datos_menu["receta"], unsafe_allow_html=True)
                
                st.markdown("<hr style='border:1px dashed #444;'>", unsafe_allow_html=True)
                st.markdown("<p class='texto-cyan' style='font-weight:bold;'>Ingredientes necesarios:</p>", unsafe_allow_html=True)
                for ing, cant in datos_menu["ingredientes"].items():
                    st.markdown(f"<span>- {ing.capitalize()}: `{cant}`</span>", unsafe_allow_html=True)
                
                st.write("")
                col_cocinar, col_borrar = st.columns(2)
                
                with col_cocinar:
                    if st.button(f"🍳 Cocinar hoy", key=f"cocinar_{nombre_menu}", use_container_width=True):
                        faltantes = []
                        for ing, cant_necesaria in datos_menu["ingredientes"].items():
                            ing_l = ing.lower()
                            cant_actual = despensa.get(ing_l, 0)
                            if cant_actual < cant_necesaria:
                                faltantes.append(f"<span class='texto-rosa' style='font-weight:bold;'>{ing.capitalize()}</span> (tienes {cant_actual}, necesitas {cant_necesaria})")
                        
                        if faltantes:
                            st.error("❌ Imposible cocinar. Faltan ingredientes en tu despensa:")
                            for f in faltantes:
                                st.markdown(f"- {f}", unsafe_allow_html=True)
                            st.info("Añade estos ingredientes en la 'Gestión de Despensa' o adapta el menú.")
                        else:
                            for ing, cant_necesaria in datos_menu["ingredientes"].items():
                                ing_l = ing.lower()
                                despensa[ing_l] -= cant_necesaria
                                if despensa[ing_l] <= 0:
                                    del despensa[ing_l]
                            guardar_nube('mi_despensa', despensa)
                            st.success("✅ ¡Ingredientes consumidos correctamente! A los fogones 🍳👩🏻‍🍳")
                            st.balloons() 
                            
                with col_borrar:
                    if st.button(f"🗑️ Borrar Menú", key=f"borrar_{nombre_menu}", use_container_width=True):
                        del favoritos[nombre_menu]
                        guardar_nube('mis_favoritos', favoritos)
                        st.rerun()


# ==========================================
# 👤 PANTALLA 2: MI PERFIL
# ==========================================
elif st.session_state['pagina_actual'] == 'Perfil':
    col_volver, _ = st.columns([1, 2])
    with col_volver:
        if st.button("🔙 Volver al Inicio", type="primary", use_container_width=True):
            cambiar_pagina('Inicio')
            
    st.markdown("<h2>ESTADO DE <span class='texto-rosa'>MI PERFIL</span></h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        opciones_dieta = ["Mediterránea", "Vegetariana", "Vegana", "Keto", "Baja en calorías", "Ninguna"]
        idx_dieta = opciones_dieta.index(perfil.get("dieta", "Mediterránea")) if perfil.get("dieta", "Mediterránea") in opciones_dieta else 0
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_comensales = st.number_input("Comensales", min_value=1, value=perfil.get("comensales", 2))
            p_dieta = st.selectbox("Tipo de Dieta", opciones_dieta, index=idx_dieta)
        with col_p2:
            p_calorias = st.number_input("Objetivo Kcal (Adulto)", min_value=1000, max_value=5000, value=perfil.get("calorias", 2350), step=50)
            op_tiempo = ["Indiferente", "Rápida (< 20 min)", "Media (20 - 45 min)", "Elaborada (> 45 min)"]
            p_tiempo = st.selectbox("Tiempo Prep.", op_tiempo, index=op_tiempo.index(perfil.get("tiempo", "Indiferente")))

        p_edades = st.text_input("Perfil Comensales (Edades)", value=perfil.get("edades", "Adultos"))
        p_alergias = st.text_input("Alergias Clínicas", value=perfil.get("alergias", ""))
        
        st.write("")
        if st.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
            perfil.update({"comensales": p_comensales, "edades": p_edades, "dieta": p_dieta, "alergias": p_alergias, "calorias": p_calorias, "tiempo": p_tiempo})
            guardar_nube('mi_perfil', perfil)
            st.success("¡Perfil guardado correctamente en Firebase!")


# ==========================================
# 📦 PANTALLA 3: MI DESPENSA
# ==========================================
elif st.session_state['pagina_actual'] == 'Despensa':
    col_volver, _ = st.columns([1, 2])
    with col_volver:
        if st.button("🔙 Volver al Inicio", type="primary", use_container_width=True):
            cambiar_pagina('Inicio')

    st.markdown("<h2>GESTIÓN DE <span class='texto-rosa'>DESPENSA</span></h2>", unsafe_allow_html=True)
    
    st.markdown("<h3>Agregar ingrediente </h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("<p style='font-weight:bold; text-align:center;'>📄 SUBIR TICKET PDF</p>", unsafe_allow_html=True)
            
            supermercado_elegido = st.selectbox(
                "¿De qué súper es el ticket?",
                ("Elige uno...", "Mercadona", "DIA", "Carrefour"),
                index=0
            )
            
            if supermercado_elegido != "Elige uno...":
                # 🚀 CONEXIÓN MÁGICA CON TUS ROBOTS EN FIREBASE
                documento_firebase = f"catalogo_{supermercado_elegido.lower()}"
                catalogo_activo = cargar_nube(documento_firebase, {})
                
                if not catalogo_activo:
                    st.error(f"⚠️ No se ha encontrado el catálogo de {supermercado_elegido} en la Nube. ¿Has ejecutado el robot?")
                else:
                    st.success(f"☁️ Catálogo de {supermercado_elegido} descargado de Firebase ({len(catalogo_activo)} productos listos).")
                    archivo = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
                    
                    if archivo and st.button("Procesar Ticket PDF", type="secondary", use_container_width=True):
                        with st.spinner("Procesando..."):
                            try:
                                nuevos = procesar_compra_pdf(archivo, list(despensa.keys()))
                                for ing, datos_t in nuevos.items():
                                    c = datos_t.get("cantidad", 1) if isinstance(datos_t, dict) else datos_t
                                    p = datos_t.get("precio", 0.0) if isinstance(datos_t, dict) else 0.0
                                    
                                    c_real, mult = calcular_unidades_reales(ing.lower(), c, p, catalogo_activo)
                                    despensa[ing.lower()] = despensa.get(ing.lower(), 0) + c_real
                                    
                                guardar_nube('mi_despensa', despensa)
                                st.success("Despensa actualizada en la nube.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    with col2:
        with st.container(border=True):
            st.markdown("<p style='font-weight:bold; text-align:center;'>✍🏻 AÑADIR MANUALMENTE </p>", unsafe_allow_html=True)
            nuevo_nom = st.text_input("Ingrediente", placeholder="Ej: Pollo")
            cant_man = st.number_input("Cantidad", min_value=0.0, step=1.0)
            un_man = st.selectbox("Medida", ["Gramos", "Kilos", "Litros", "Unidades"])
            if st.button("Añadir a la nube", type="secondary", use_container_width=True) and nuevo_nom:
                c_fin = cant_man * 1000 if un_man in ["Kilos", "Litros"] else cant_man
                nom_l = nuevo_nom.lower().strip()
                despensa[nom_l] = despensa.get(nom_l, 0) + int(c_fin) if c_fin.is_integer() else c_fin
                guardar_nube('mi_despensa', despensa)
                st.success("Añadido.")
                st.rerun()

    st.markdown("<hr style='border:1px solid #333;'>", unsafe_allow_html=True)
    
    if 'mostrar_inventario' not in st.session_state:
        st.session_state['mostrar_inventario'] = False
        
    texto_boton = "🙈 Ocultar Inventario" if st.session_state['mostrar_inventario'] else "🔍 Ver Inventario Actual"
    
    if st.button(texto_boton, use_container_width=True):
        st.session_state['mostrar_inventario'] = not st.session_state['mostrar_inventario']
        st.rerun()

    if st.session_state['mostrar_inventario']:
        st.markdown("<h3>Inventario Actual (Nube)</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            if not despensa:
                st.info("La despensa está a cero.")
            else:
                for i, (ing, cant) in enumerate(despensa.items()):
                    st.markdown(f"<span class='texto-cyan' style='font-weight:600; font-size:1.1rem;'>{i + 1}. {ing.capitalize()}</span> <span>➔ `{cant} g/ud`</span>", unsafe_allow_html=True)
                
                st.markdown("<br><hr style='border:1px dashed #444;'><br>", unsafe_allow_html=True)
                
                ing_elegido = st.selectbox("Selecciona para editar:", list(despensa.keys()))
                if ing_elegido:
                    cant_act = float(despensa[ing_elegido])
                    n_cant = st.number_input(f"Cantidad de {ing_elegido}", min_value=0.0, value=cant_act, step=1.0)
                    
                    c_ed1, c_ed2 = st.columns(2)
                    with c_ed1:
                        if st.button("Actualizar Cantidad", use_container_width=True):
                            if n_cant <= 0: del despensa[ing_elegido]
                            else: despensa[ing_elegido] = n_cant
                            guardar_nube('mi_despensa', despensa)
                            st.rerun()
                    with c_ed2:
                        if st.button("🗑️ Borrar", use_container_width=True):
                            del despensa[ing_elegido]
                            guardar_nube('mi_despensa', despensa)
                            st.rerun()
                            
                st.write("")
                if st.button("❌ Vaciar Despensa Completa", type="primary", use_container_width=True):
                    guardar_nube('mi_despensa', {})
                    st.rerun()