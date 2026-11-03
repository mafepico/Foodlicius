import httpx

def probar_conexion_mercadona():
    # Usamos el endpoint con el código postal como query param
    url = "https://tienda.mercadona.es/api/categories/?postal_code=46001"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    print(" Conectando con Mercadona...")
    
    with httpx.Client(headers=headers, timeout=15.0) as client:
        try:
            # 1. Obtener el árbol completo de categorías
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            categorias = data.get("results", [])
            print(f" Conexión exitosa. Se encontraron {len(categorias)} categorías.")

            # 2. Buscar una subcategoría real (las hojas del árbol que contienen productos)
            subcategoria_id = None
            nombre_subcat = ""

            for cat in categorias:
                subcategorias = cat.get("categories", [])
                if subcategorias:
                    primera_sub = subcategorias[0]
                    subcategoria_id = primera_sub.get("id")
                    nombre_subcat = primera_sub.get("name")
                    break

            if not subcategoria_id:
                print(" No se encontraron subcategorías válidas.")
                return

            print(f" Consultando subcategoría: '{nombre_subcat}' (ID: {subcategoria_id})...")

            # 3. Obtener los productos de esa subcategoría concreta
            url_detalle = f"https://tienda.mercadona.es/api/categories/{subcategoria_id}/?postal_code=46001"
            resp_detalle = client.get(url_detalle)
            resp_detalle.raise_for_status()
            detalle = resp_detalle.json()
            
            # 4. Extraer y mostrar productos reales
            productos = []
            for sub in detalle.get("categories", [detalle]):
                for prod in sub.get("products", []):
                    precio_info = prod.get("price_instructions", {})
                    productos.append({
                        "nombre": prod.get("display_name"),
                        "precio": precio_info.get("unit_price"),
                        "formato": prod.get("packaging")
                    })
            
            print(f"\n Muestra de {min(3, len(productos))} productos obtenidos:")
            for p in productos[:3]:
                print(f" • {p['nombre']} | {p['precio']} € | Formato: {p['formato']}")

        except Exception as e:
            print(f" Error en la petición: {e}")

if __name__ == "__main__":
    probar_conexion_mercadona()