import asyncio
import httpx
import json
import re
import firebase_admin
from firebase_admin import credentials, firestore
import os

CP_USUARIO = "17162" # Pon tu código postal real
API_BASE = "https://tienda.mercadona.es/api"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def extraer_unidades(prod):
    p_inst = prod.get('price_instructions', {})
    
    unit_size = p_inst.get('unit_size')
    size_format = p_inst.get('size_format', '').lower()
    
    if unit_size and size_format in ['ud', 'uds']:
        return f"{int(unit_size)} ud"
    elif unit_size and size_format in ['kg', 'kilo', 'kilos']:
        return f"{unit_size} kg"

    total_units = p_inst.get('total_units')
    if total_units and total_units > 1:
        return f"{int(total_units)} ud"

    bundle = prod.get('bundle', {})
    if bundle and bundle.get('unit_count'):
        return f"{bundle.get('unit_count')} ud"

    textos = f"{prod.get('format_content', '')} {prod.get('content_description', '')} {prod.get('display_name', '')}".lower()
    
    match_kg = re.search(r'(\d+[.,]?\d*)\s*(kg|kilos)', textos)
    if match_kg:
        return f"{match_kg.group(1).replace(',', '.')} kg"

    match_ud = re.search(r'(\d+)\s*(ud|uds|unidades|x)', textos)
    if match_ud:
        return f"{match_ud.group(1)} ud"
        
    return "1 ud"

def recolectar_productos_recursivo(categoria, lista_productos):
    if 'products' in categoria:
        for p in categoria['products']:
            lista_productos.append(p)
            
    if 'categories' in categoria:
        for subcat in categoria['categories']:
            recolectar_productos_recursivo(subcat, lista_productos)

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
    catalogo = {}
    
    async with httpx.AsyncClient(headers=HEADERS_BASE, timeout=30.0) as client:
        print(f"📍 Sincronizando CP {CP_USUARIO}...")
        res_cp = await client.put(f"{API_BASE}/postal-codes/actions/change-pc/", json={"new_postal_code": CP_USUARIO})
        wh = res_cp.headers.get('x-customer-wh', '')
        
        print("🗺️ Descargando mapa de pasillos...")
        url_cat = f"{API_BASE}/categories/?lang=es" + (f"&wh={wh}" if wh else "")
        r_root = await client.get(url_cat)
        mapa = r_root.json().get('results', [])
        
        EXCLUIR = ["bebé", "limpieza", "perfumería", "mascotas", "fitoterapia", "maquillaje", "cabello", "facial", "corporal"]

        print("🚀 Extrayendo catálogo (Modo Exploración Profunda)...")
        for cat in mapa:
            nombre_cat = cat.get('name', '').lower()
            if any(palabra in nombre_cat for palabra in EXCLUIR): continue
            
            print(f"🛒 Pasillo: {cat.get('name')}")
            for sub in cat.get('categories', []):
                url_sub = f"{API_BASE}/categories/{sub.get('id')}/?lang=es" + (f"&wh={wh}" if wh else "")
                res_sub = await client.get(url_sub)
                
                if res_sub.status_code == 200:
                    data = res_sub.json()
                    todos_los_productos = []
                    recolectar_productos_recursivo(data, todos_los_productos)
                    
                    for prod in todos_los_productos:
                        nombre = prod.get('display_name', '').lower().strip()
                        formato_real = extraer_unidades(prod)
                        precio = prod.get('price_instructions', {}).get('unit_price', 0)
                        
                        if nombre:
                            nombre_unico = f"{nombre} | {formato_real}"
                            catalogo[nombre_unico] = {
                                "formato": formato_real,
                                "precio": precio,
                                "supermercado": "Mercadona",
                                "nombre_original": nombre
                            }
                await asyncio.sleep(0.05)

        print("\n☁️ Subiendo el catálogo a Firebase...")
        if catalogo:
            db.collection('app_data').document('catalogo_mercadona').set(catalogo)
            print(f"🎉 ¡TERMINADO! Guardados {len(catalogo)} productos de Mercadona en tu base de datos.")
        else:
            print("⚠️ No se encontró ningún producto.")

if __name__ == "__main__":
    asyncio.run(main())
