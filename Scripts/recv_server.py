"""Servidor local que recibe imágenes (POST base64/binario) desde el navegador y las guarda.
Uso: python recv_server.py <carpeta_destino> [puerto]
POST /save?name=01.png  (cuerpo = bytes de la imagen)
"""
import os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

OUT = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8766
os.makedirs(OUT, exist_ok=True)

class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        page = b"""<!doctype html><title>recv</title><body>listo<script>
(async () => {
  if (!location.hash) return;
  const items = JSON.parse(decodeURIComponent(location.hash.slice(1)));
  for (const {name, data} of items) {
    const bin = Uint8Array.from(atob(data.split(',')[1]), c => c.charCodeAt(0));
    const r = await fetch('/save?name=' + encodeURIComponent(name), {method: 'POST', body: bin});
    document.body.insertAdjacentHTML('beforeend', '<div class=ok>' + name + ' ' + await r.text() + '</div>');
  }
  document.title = 'done ' + items.length;
})();
window.addEventListener('message', async e => {
  const {name, data} = e.data || {};
  if (!name) return;
  const bin = Uint8Array.from(atob(data.split(',')[1]), c => c.charCodeAt(0));
  const r = await fetch('/save?name=' + encodeURIComponent(name), {method: 'POST', body: bin});
  document.body.insertAdjacentHTML('beforeend', '<div>' + name + ' ' + await r.text() + '</div>');
  e.source && e.source.postMessage({saved: name}, '*');
});
</script>"""
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        q = parse_qs(urlparse(self.path).query)
        name = os.path.basename(q.get("name", ["img.png"])[0])
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(data)
        print("saved", name, len(data), flush=True)
        self.send_response(200); self._cors(); self.end_headers()
        self.wfile.write(f"ok {len(data)}".encode())

HTTPServer(("127.0.0.1", PORT), H).serve_forever()
