from playwright.sync_api import sync_playwright
import json
import time
import re
import random
import firebase_admin
from firebase_admin import credentials, firestore
import os

def escaner_absoluto_carrefour():
    print("☁️ Conectando a Firebase...")
    if not firebase_admin._apps:
        try:
            cert_info = json.loads(os.environ.get('FIREBASE_KEY'))
            cred = credentials.Certificate(cert_info)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"❌ Error Firebase: {e}"); return
    
    db = firestore.client()

    print("🤖 Iniciando el Escáner Maestro (El Gran Saqueo de Frescos y Despensa)...")

    pasillos = {
        "Carne": "https://www.carrefour.es/supermercado/frescos/carne/cat20018/c",
        "Pescaderia": "https://www.carrefour.es/supermercado/frescos/pescado-y-marisco/cat20014/c",
        "Frutas": "https://www.carrefour.es/supermercado/frescos/frutas/cat220006/c",
        "Verduras": "https://www.carrefour.es/supermercado/frescos/verduras-y-hortalizas/cat220014/c",
        "Quesos": "https://www.carrefour.es/supermercado/frescos/quesos/cat20020/c",
        "Charcuteria": "https://www.carrefour.es/supermercado/frescos/charcuteria/cat20017/c",
        "Charcuteria_Corte": "https://www.carrefour.es/supermercado/frescos/charcuteria-y-quesos-al-corte/cat510001/c",
        "Panaderia": "https://www.carrefour.es/supermercado/frescos/pan-y-bolleria-del-dia/cat20019/c",
        "Sushi": "https://www.carrefour.es/supermercado/frescos/sushi-del-dia/cat10928974/c",
        "Lacteos": "https://www.carrefour.es/supermercado/la-despensa/lacteos/cat20011/c",
        "Alimentacion_General": "https://www.carrefour.es/supermercado/la-despensa/alimentacion/cat20009/c",
        "Desayunos": "https://www.carrefour.es/supermercado/la-despensa/desayuno/cat26100390/c",
        "Yogures-y-Postres": "https://www.carrefour.es/supermercado/la-despensa/yogures-y-postres/cat390008/c",
        "Dulces": "https://www.carrefour.es/supermercado/la-despensa/dulce/cat26100388/c",
        "Panaderia-Bolleria-y-Pasteleria": "https://www.carrefour.es/supermercado/la-despensa/panaderia-bolleria-y-pasteleria/cat21319201/c",
        "Conservas-Sopas-y-Precocinados": "https://www.carrefour.es/supermercado/la-despensa/conservas-sopas-y-precocinados/cat20013/c",
        "Aperitivos": "https://www.carrefour.es/supermercado/la-despensa/aperitivos/cat390001/c",
        "Huevos": "https://www.carrefour.es/supermercado/la-despensa/huevos/cat20021/c",
    }

    inventario_total = {}

    try:
        with sync_playwright() as p:
            # HEADLESS=TRUE para que se ejecute invisible en GitHub
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()

            print("🌍 Entrando por la portada principal de Carrefour...")
            page.goto("https://www.carrefour.es", timeout=60000)
            time.sleep(3)

            if page.locator('#cf-wrapper').is_visible():
                print("🚨 ¡Gorila detectado en la entrada! Intentando esperar a que nos dejen pasar...")
                page.wait_for_selector('#cf-wrapper', state='hidden', timeout=30000)

            try:
                boton_cookies = page.locator('#onetrust-accept-btn-handler')
                if boton_cookies.is_visible(timeout=3000):
                    boton_cookies.click()
            except:
                pass

            for nombre_pasillo, url_base in pasillos.items():
                print(f"\n🛒 --- ENTRANDO A LA SECCIÓN: {nombre_pasillo.upper()} ---")
                productos_pasillo = []
                
                pagina_actual = 1
                total_paginas = 1 
                
                while pagina_actual <= total_paginas:
                    offset = (pagina_actual - 1) * 24
                    url_actual = f"{url_base}?offset={offset}" if offset > 0 else url_base
                    
                    print(f"   📄 Aspirando Página {pagina_actual} de {total_paginas if total_paginas > 1 else '?'}...")
                    
                    try:
                        page.evaluate(f"""
                            let boton = document.getElementById('boton-hacker');
                            if (!boton) {{
                                boton = document.createElement('a');
                                boton.id = 'boton-hacker';
                                boton.style.position = 'fixed';
                                boton.style.top = '50%';
                                boton.style.left = '50%';
                                boton.style.transform = 'translate(-50%, -50%)';
                                boton.style.zIndex = '999999';
                                boton.style.fontSize = '30px';
                                boton.style.background = '#00549f';
                                boton.style.color = 'white';
                                boton.style.padding = '15px';
                                boton.style.borderRadius = '10px';
                                document.body.appendChild(boton);
                            }}
                            boton.href = '{url_actual}';
                            boton.innerText = 'Ir a {nombre_pasillo} (Pág {pagina_actual})';
                        """)
                        
                        time.sleep(1.5) 
                        page.click('#boton-hacker', force=True) 
                        
                        time.sleep(2) 
                        if page.locator('#cf-wrapper').is_visible():
                            print("🚨 ¡Cloudflare atacó de nuevo! Intentando sobrevivir...")
                            page.wait_for_selector('#cf-wrapper', state='hidden', timeout=30000)
                        
                        page.wait_for_selector('.product-card', timeout=15000)

                        for _ in range(5):
                            page.keyboard.press('PageDown')
                            time.sleep(0.8)

                        if pagina_actual == 1:
                            print("   🔍 Analizando el mapa del pasillo...")
                            texto_completo = page.inner_text('body')
                            match = re.search(r'P[áa]gina\s+1\s+de\s+(\d+)', texto_completo, re.IGNORECASE)
                            
                            if match:
                                total_paginas = int(match.group(1))
                                print(f"   📊 ¡BINGO! La web confiesa: Hay exactamente {total_paginas} páginas aquí.")
                            else:
                                elementos_li = page.locator('.pagination__item').count()
                                if elementos_li > 0:
                                    total_paginas = elementos_li
                                    print(f"   📊 Contando botones ocultos veo {total_paginas} páginas.")
                                else:
                                    print("   ⚠️ No encontré el paginador. Asumiendo 1 página.")

                        tarjetas = page.locator('.product-card').all()
                        
                        for tarjeta in tarjetas:
                            nombre_formato = "Sin nombre"
                            precio = "0.00 €"

                            try:
                                elemento_titulo = tarjeta.locator('.product-card__title-link')
                                if elemento_titulo.count() > 0:
                                    nombre_formato = elemento_titulo.first.inner_text().strip()
                            except:
                                pass

                            try:
                                texto_bruto = tarjeta.inner_text().strip().split('\n')
                                precios_posibles = [l.strip() for l in texto_bruto if '€' in l and '/' not in l]
                                if precios_posibles:
                                    precio_bruto = precios_posibles[-1]
                                    precios_encontrados = re.findall(r'\d+,\d+\s*€|\d+\.\d+\s*€', precio_bruto)
                                    precio = precios_encontrados[-1] if precios_encontrados else precio_bruto
                            except:
                                pass

                            if nombre_formato != "Sin nombre" and nombre_formato != "":
                                productos_pasillo.append({
                                    "nombre": nombre_formato,
                                    "precio": precio
                                })

                        print(f"   ✅ Pág {pagina_actual}/{total_paginas} aspirada. Llevamos {len(productos_pasillo)} productos.")

                        pagina_actual += 1
                        
                        if pagina_actual <= total_paginas:
                            time.sleep(random.uniform(2.0, 3.5))

                    except Exception as e:
                        print(f"   💥 Problema inesperado en la página {pagina_actual}: {e}")
                        break 
                        
                inventario_total[nombre_pasillo] = productos_pasillo
                print(f"📦 Resumen de {nombre_pasillo}: {len(productos_pasillo)} productos guardados en total.")
                
                try:
                    espera = random.uniform(3.0, 5.0)
                    page.goto("https://www.carrefour.es", timeout=60000)
                    time.sleep(espera)
                except:
                    pass

            browser.close()

    except Exception as error_global:
        print(f"\n💥 ERROR CRÍTICO DURANTE LA EJECUCIÓN: {error_global}")
        
    finally:
        print("\n☁️ Subiendo la Gran Despensa a Firebase...")
        if inventario_total:
            try:
                db.collection('app_data').document('catalogo_carrefour').set(inventario_total)
                print("🎉 ¡MISIÓN FINALIZADA! Revisa tu Firebase. Los datos de Carrefour están a salvo.")
            except Exception as e:
                print(f"❌ Error fatal al intentar subir a Firebase: {e}")
        else:
            print("⚠️ El inventario está vacío, no se guardó nada en la nube.")

if __name__ == "__main__":
    escaner_absoluto_carrefour()
