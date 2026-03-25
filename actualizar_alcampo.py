import asyncio
from playwright.async_api import async_playwright
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

async def scrape_alcampo():
    print("☁️ Conectando a Firebase...")
    # Conexión a Firebase usando la llave secreta de GitHub
    if not firebase_admin._apps:
        try:
            cert_info = json.loads(os.environ.get('FIREBASE_KEY'))
            cred = credentials.Certificate(cert_info)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"❌ Error con la llave de Firebase: {e}")
            return
    
    db = firestore.client()

    async with async_playwright() as p:
        # headless=True porque en la nube no hay pantalla física
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔗 Entrando en Alcampo...")
        # Entramos a una categoría de ejemplo (Carnicería)
        await page.goto("https://compraonline.alcampo.es/categories/fresco/carne/3553")
        
        # Intentar aceptar cookies rápido
        try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
        except: pass

        print("🔎 Buscando productos...")
        try:
            await page.wait_for_selector(".product-card", timeout=10000)
            items = await page.query_selector_all(".product-card")
            
            catalogo = {}
            for item in items:
                try:
                    nom = await (await item.query_selector(".product-card__title")).inner_text()
                    pre = await (await item.query_selector(".product-card__price-container")).inner_text()
                    
                    # Limpiamos el texto del precio para quedarnos solo con el número
                    num_precio = pre.split("€")[0].replace(",", ".").strip()
                    
                    catalogo[nom.strip()] = {"precio": num_precio, "supermercado": "Alcampo"}
                except: continue

            # Guardar directamente en la nube de Firebase
            if catalogo:
                doc_ref = db.collection('app_data').document('catalogo_alcampo')
                doc_ref.set(catalogo)
                print(f"✅ ¡Éxito! Guardados {len(catalogo)} productos de Alcampo en tu Firebase.")
            else:
                print("⚠️ No se extrajo ningún producto.")

        except Exception as e:
            print(f"❌ Error al raspar la página: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_alcampo())
