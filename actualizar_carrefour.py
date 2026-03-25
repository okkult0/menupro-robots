import asyncio
from playwright.async_api import async_playwright
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

async def scrape_carrefour():
    print("☁️ Conectando a Firebase...")
    if not firebase_admin._apps:
        try:
            cert_info = json.loads(os.environ.get('FIREBASE_KEY'))
            cred = credentials.Certificate(cert_info)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"❌ Error Firebase: {e}"); return
    
    db = firestore.client()

    async with async_playwright() as p:
        # headless=True para que se ejecute invisible en la nube
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔗 Entrando en Carrefour...")
        # Ejemplo: Categoría de carnicería de Carrefour
        await page.goto("https://www.carrefour.es/supermercado/el-mercado/carniceria/F-10fnZ1215/c")
        
        # 1. Aceptar Cookies
        try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
        except: pass

        print("🔎 Buscando productos...")
        await asyncio.sleep(4) # Esperamos a que carguen bien los productos
        
        # 2. Extraer tarjetas de producto
        items = await page.query_selector_all(".product-card-item")
        catalogo = {}
        
        for item in items:
            try:
                nom = await (await item.query_selector(".product-card-item__name")).inner_text()
                pre = await (await item.query_selector(".product-card-item__price")).inner_text()
                
                # Limpiar el precio (quitar el símbolo del euro)
                num_precio = pre.split("€")[0].replace(",", ".").strip()
                catalogo[nom.strip()] = {"precio": num_precio, "supermercado": "Carrefour"}
            except: continue

        # 3. Guardar en Firebase
        if catalogo:
            db.collection('app_data').document('catalogo_carrefour').set(catalogo)
            print(f"✅ ¡Guardados {len(catalogo)} productos de Carrefour en Firebase!")
        else:
            print("⚠️ No se encontraron productos. A veces Carrefour bloquea el acceso a robots, requeriría ajustes.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_carrefour())
