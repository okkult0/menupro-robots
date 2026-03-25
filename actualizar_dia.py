import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import firebase_admin
from firebase_admin import credentials, firestore
import os

BASE_URL = "https://www.dia.es"

CATEGORIAS_DIA = [
    "/frutas/c/L105",
    "/verduras/c/L104",
    "/carnes/c/L102",
    "/pescados-y-mariscos/c/L103",
    "/charcuteria-y-quesos/c/L101",
    "/huevos-leche-y-mantequilla/c/L108",
    "/panaderia/c/L112",
    "/yogures-y-postres/c/L113",
    "/arroz-pastas-y-legumbres/c/L106",
    "/aceites-salsas-y-especias/c/L107",
    "/conservas-caldos-y-cremas/c/L114",
    "/azucar-chocolates-y-caramelos/c/L110",
    "/galletas-bollos-y-cereales/c/L111",
    "/aperitivos-y-frutos-secos/c/L115",
    "/agua-y-refrescos/c/L117",
    "/zumos-y-smoothies/c/L127",
    "/cervezas-vinos-y-licores/c/L118",
    "/congelados/c/L119"
]

EXCLUIR = ["detergente", "friegasuelos", "lavavajillas", "limpieza", "lejía", "suavizante", "mascotas", "perro", "gato", "champú", "gel de baño", "desodorante", "papel higiénico", "pañales", "pasta de dientes"]

def limpiar_formato(texto):
    texto = texto.lower()
    match_kg = re.search(r'(\d+[.,]?\d*)\s*(kg|kilos|kilo)\b', texto)
    if match_kg: return f"{match_kg.group(1).replace(',', '.')} kg"
    match_g = re.search(r'(\d+[.,]?\d*)\s*(g|gr|gramos)\b', texto)
    if match_g: return f"{match_g.group(1)} g"
    match_l = re.search(r'(\d+[.,]?\d*)\s*(l|litro|litros)\b', texto)
    if match_l: return f"{match_l.group(1).replace(',', '.')} l"
    match_ml = re.search(r'(\d+[.,]?\d*)\s*(ml|mililitros)\b', texto)
    if match_ml: return f"{match_ml.group(1)} ml"
    match_ud = re.search(r'(\d+)\s*(ud|uds|unidades|pack|x)\b', texto)
    if match_ud: return f"{match_ud.group(1)} ud"
    return "1 ud"

async def obtener_subcategorias(page, url_cat):
    url_completa = f"{BASE_URL}{url_cat}"
    subcategorias = set()
    try:
        await page.goto(url_completa, timeout=60000)
        await page.wait_for_timeout(3000)
        try: await page.locator("text=Aceptar").first.click(timeout=2000)
        except: pass
            
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        enlaces = soup.find_all('a', href=True)
        base_path = url_cat.split('/')[1] 
        
        for a in enlaces:
            href = a['href']
            if f"/{base_path}/" in href and "/c/L" in href and href != url_cat:
                subcategorias.add(href)
                
        if not subcategorias: subcategorias.add(url_cat)
        return list(subcategorias)
    except Exception as e:
        print(f"   ❌ Error leyendo menú lateral: {e}")
        return [url_cat]

async def explorar_categoria(page, url_cat, catalogo):
    url_completa = f"{BASE_URL}{url_cat}"
    try:
        await page.goto(url_completa, timeout=60000)
        await page.wait_for_timeout(3000)
        print("      ⬇️ Desenrollando la página completa...")
        
        productos_a_la_vista = 0
        intentos_atascado = 0
        
        while intentos_atascado < 3:
            await page.keyboard.press("End")
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollBy(0, -600)")
            await page.wait_for_timeout(500)
            await page.keyboard.press("End")
            await page.wait_for_timeout(3000) 
            
            try:
                boton = page.locator("button:has-text('Cargar más'), button:has-text('Mostrar más')").first
                if await boton.is_visible(timeout=500):
                    await boton.click()
                    await page.wait_for_timeout(2000)
            except: pass

            html_temp = await page.content()
            soup_temp = BeautifulSoup(html_temp, 'html.parser')
            nombres_temp = soup_temp.find_all(class_=re.compile(r'name|title', re.I))
            cantidad_actual = len(nombres_temp)
            
            if cantidad_actual > productos_a_la_vista:
                productos_a_la_vista = cantidad_actual
                intentos_atascado = 0 
                print(f"        ...Llevamos {cantidad_actual} artículos cargados")
            else:
                intentos_atascado += 1 
                
        html_final = await page.content()
        soup = BeautifulSoup(html_final, 'html.parser')
        productos = soup.find_all(class_=re.compile(r'product', re.I))
        
        nombres_vistos = set()
        for prod in productos:
            elem_nombre = prod.find(class_=re.compile(r'name|title', re.I))
            elem_precio = prod.find(class_=re.compile(r'price', re.I))
            if not elem_nombre or not elem_precio: continue
            
            nombre = elem_nombre.get_text(strip=True).lower()
            if not nombre or any(palabra in nombre for palabra in EXCLUIR): continue
                
            if nombre not in nombres_vistos:
                nombres_vistos.add(nombre)
                text_card = elem_precio.get_text(separator=" ", strip=True)
                match_precio = re.search(r'(\d+[.,]\d{2})\s*€', text_card)
                if match_precio:
                    precio = float(match_precio.group(1).replace(',', '.'))
                else:
                    match_precio_entero = re.search(r'(\d+)\s*€', text_card)
                    precio = float(match_precio_entero.group(1)) if match_precio_entero else 0.0

                formato_real = limpiar_formato(nombre)
                nombre_unico = f"{nombre} | {formato_real}"

                catalogo[nombre_unico] = {
                    "formato": formato_real,
                    "precio": precio,
                    "supermercado": "DIA"
                }
                
        print(f"      ✅ Pasillo completado. {len(nombres_vistos)} productos extraídos.")
    except Exception as e:
        print(f"      ❌ Error en subcategoría: {e}")

async def main():
    print("☁️ Conectando a Firebase...")
    if not firebase_admin._apps:
        try:
            cert_info = json.loads(os.environ.get('FIREBASE_KEY'))
            cred = credentials.Certificate(cert_info)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"❌ Error Firebase: {e}"); return
    
    db = firestore.client()
    catalogo_dia = {}
    
    print("🚀 Arrancando el Navegador EN MODO NUBE...")
    async with async_playwright() as p:
        # headless=True porque estamos en un servidor sin pantalla
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        for categoria in CATEGORIAS_DIA:
            nombre_pasillo = categoria.split('/')[1].upper() if len(categoria.split('/')) > 1 else "DESCONOCIDO"
            print(f"\n🛒 Entrando al pasillo general: {nombre_pasillo}")
            subcategorias = await obtener_subcategorias(page, categoria)
            for subcat in subcategorias:
                await explorar_categoria(page, subcat, catalogo_dia)

        await browser.close()

    # Guardar en la nube (Firebase)
    if catalogo_dia:
        db.collection('app_data').document('catalogo_dia').set(catalogo_dia)
        print(f"\n🎉 ¡TERMINADO! Guardados {len(catalogo_dia)} productos de DIA en Firebase.")
    else:
        print("⚠️ No se guardó nada porque el catálogo está vacío.")

if __name__ == "__main__":
    asyncio.run(main())
