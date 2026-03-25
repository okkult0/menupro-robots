import asyncio
from playwright.async_api import async_playwright
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

async def scrape_dia():
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
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔗 Entrando en DIA...")
        await page.goto("https://www.dia.es/compra-online/despensa/carnes/cf")
        
        try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
        except: pass

        print("🔎 Buscando productos...")
        await asyncio.sleep(3) # Esperamos a que cargue
        
        items = await page.query_selector_all(".search-product-card")
        catalogo = {}
        for item in items:
            try:
                nom = await (await item.query_selector(".search-product-card__product-name")).inner_text()
                pre = await (await item.query_selector(".search-product-card__active-price")).inner_text()
                num_precio = pre.split("€")[0].replace(",", ".").strip()
                catalogo[nom.strip()] = {"precio": num_precio, "supermercado": "DIA"}
            except: continue

        if catalogo:
            db.collection('app_data').document('catalogo_dia').set(catalogo)
            print(f"✅ ¡Guardados {len(catalogo)} productos de DIA en Firebase!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dia())
