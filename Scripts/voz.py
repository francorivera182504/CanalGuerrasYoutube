"""Genera la voz por escena con edge-tts y guarda los tiempos de cada palabra.
Uso: python voz.py guion.json carpeta_salida [rate]
Salida: NN.mp3 + NN.words.json por escena.
"""
import asyncio, json, os, sys, edge_tts

async def one(text, voice, rate, mp3, wj):
    for attempt in range(5):
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            words, audio = [], bytearray()
            async for ch in com.stream():
                if ch["type"] == "audio":
                    audio += ch["data"]
                elif ch["type"] == "WordBoundary":
                    words.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
            if not audio:
                raise RuntimeError("sin audio")
            open(mp3, "wb").write(audio)
            json.dump(words, open(wj, "w", encoding="utf-8"), ensure_ascii=False)
            return
        except Exception as e:
            print("reintento", attempt, e)
            await asyncio.sleep(2)
    raise SystemExit("falló " + mp3)

async def main():
    g = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]; rate = sys.argv[3] if len(sys.argv) > 3 else "+0%"
    os.makedirs(out, exist_ok=True)
    for s in g["scenes"]:
        await one(s["text"], g["voice"], rate, f"{out}/{s['id']}.mp3", f"{out}/{s['id']}.words.json")
        print("ok", s["id"])

asyncio.run(main())
