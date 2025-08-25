import asyncio, argparse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
from lightymclightshow.client.lights_client import LightsClient

app = FastAPI()
lc: LightsClient | None = None

@app.on_event("startup")
async def startup(): pass

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!doctype html><meta name=viewport content="width=device-width, initial-scale=1">
<style>button{font-size:1.4rem;padding:1rem;margin:.5rem;width:100%;}</style>
<h1>Steely Glint</h1>
<button onclick="post('/preset','steely/nav_lights')">Nav Lights</button>
<button onclick="post('/preset','steely/dock_light')">Dock Light</button>
<button onclick="post('/preset','steely/lighthouse')">Lighthouse</button>
<button onclick="post('/preset','steely/newtons_cradle')">Newton's Cradle</button>
<button onclick="post('/preset','steely/bow_wave')">Bow Wave</button>
<button onclick="fetch('/api/stop_all',{method:'POST'})">All Off</button>
<label>Brightness <input type=range min=0 max=100 value=100 oninput="setb(this.value)"></label>
<script>
function post(url,name){ fetch('/api/preset/'+name,{method:'POST'}) }
function setb(v){ fetch('/api/brightness/'+(v/100),{method:'POST'}) }
</script>
"""

@app.post("/api/preset/{name:path}")
async def run_preset(name: str):
    await lc.run_preset(name)
    return {"ok": True}

@app.post("/api/stop_all")
async def stop_all():
    await lc.stop_all(); return {"ok": True}

@app.post("/api/brightness/{value}")
async def brightness(value: float):
    await lc.set_brightness(value); return {"ok": True}

def main():
    global lc
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--socket", default="/run/lightymc.sock")
    args = ap.parse_args()
    lc = LightsClient(args.socket)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()

