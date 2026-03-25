import asyncio
from playwright.async_api import async_playwright
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

async def scrape_mercadona():
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
        
        print("🔗 Entrando en Mercadona...")
        # Entramos a la categoría de Carne de Mercadona
        await page.goto("https://tienda.mercadona.es/categories/112")
        
        try:
            # Mercadona siempre pide código postal al entrar
            await page.fill("input[name='postalCode']", "28029") # Pon tu CP aquí si quieres
            await page.click("button[data-test='btn-submit']")
            await asyncio.sleep(3) # Esperamos a que cargue la tienda
        except: 
            print("⚠️ No pidió código postal.")

        print("🔎 Buscando productos...")
        await asyncio.sleep(4)
        
        items = await page.query_selector_all(".product-cell")
        catalogo = {}
        for item in items:
            try:
                nom = await (await item.query_selector("h4")).inner_text()
                pre = await (await item.query_selector(".product-price__unit-price")).inner_text()
                num_precio = pre.split("€")[0].replace(",", ".").strip()
                catalogo[nom.strip()] = {"precio": num_precio, "supermercado": "Mercadona"}
            except: continue

        if catalogo:
            db.collection('app_data').document('catalogo_mercadona').set(catalogo)
            print(f"✅ ¡Guardados {len(catalogo)} productos de Mercadona en Firebase!")
        else:
            print("⚠️ No se encontraron productos. (A veces Mercadona bloquea conexiones automatizadas en la nube).")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_mercadona())
