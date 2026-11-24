"""Genera una imagen con la API de Gemini.
La clave se lee de la variable de entorno GEMINI_API_KEY (nunca se escribe en archivos).
Uso: python gemini_img.py "prompt" salida.png [modelo] [aspect]
"""
import base64, json, os, sys, urllib.request, urllib.error

def get_key():
    k = os.environ.get("GEMINI_API_KEY")
    if not k and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            k = winreg.QueryValueEx(h, "GEMINI_API_KEY")[0]
    if not k:
        sys.exit("Falta GEMINI_API_KEY")
    return k

def generate(prompt, out, model="gemini-3.1-flash-image", aspect="16:9"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": get_key()})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:600]}")
    for c in data.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "inlineData" in p:
                os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
                with open(out, "wb") as f:
                    f.write(base64.b64decode(p["inlineData"]["data"]))
                print("OK", out, data.get("usageMetadata", {}))
                return
    sys.exit("Sin imagen: " + json.dumps(data)[:600])

if __name__ == "__main__":
    generate(sys.argv[1], sys.argv[2], *(sys.argv[3:5]))
