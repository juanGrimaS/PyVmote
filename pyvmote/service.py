from fastapi import FastAPI, WebSocketDisconnect, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import asyncio
import threading
import shutil
import json 
import atexit
import signal
import sys
import re
from .graph_generator import Graph

class Server:
    def __init__(self):
        self.port = ""
        self.app = FastAPI()
        self.ws_connection = None 
        self.last_timestamp = 0
        self.loop = None
        self.start = False
        self.init_server()
        self._register_shutdown_hooks()

    
    def init_server(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.image_folder = os.path.join(self.base_path, "static", "images")
        self.html_folder = os.path.join(self.base_path, "static", "html")
        self.templates_path = os.path.join(self.base_path, "templates")
        
        self.app.mount("/static", StaticFiles(directory=os.path.join(self.base_path, "static")), name="static")
        
        self.templates = Jinja2Templates(directory=self.templates_path)
        
        self.app.get("/")(self.index)
        self.app.add_api_route("/preview", self.preview_page)
        self.app.get("/latest")(self.latest_image)
        self.app.add_api_route("/rename", self.rename_graph, methods=["POST"])
        
        self.app.on_event("startup")(self.startup_event)
        self.app.websocket("/ws")(self.websocket_endpoint)
    
    def _register_shutdown_hooks(self):
        if hasattr(self, '_hooks_registered') and self._hooks_registered:
            return

        def safe_shutdown(*args):
            if self.start:
                print("[pyvmote] Deteniendo servidor automáticamente...")
                self.stop_server()
                if args:  # si viene de signal
                    sys.exit(0)

        atexit.register(safe_shutdown)
        signal.signal(signal.SIGINT, safe_shutdown)
        signal.signal(signal.SIGTERM, safe_shutdown)
        self._hooks_registered = True

    async def startup_event(self):
        self.loop = asyncio.get_running_loop()

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.ws_connection = websocket
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.ws_connection = None

    def get_image_files(self):
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        if not os.path.exists(self.image_folder):
            return []
        return [f for f in os.listdir(self.image_folder) if f.lower().endswith(valid_extensions)]

    def get_html_files(self):
        if not os.path.exists(self.html_folder):
            return []
        return [f for f in os.listdir(self.html_folder) if f.endswith(".html")]

    def get_latest_graphs(self):
        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return None, None

        with open(history_file, "r") as f:
            history = json.load(f)

        if not history:
            return None, None

        latest = history[-1]
        if latest["type"] == "html":
            return None, latest["title"] + ".html"
        elif latest["type"] == "image":
            return latest["title"] + ".png", None
        else:
            return None, None


    async def index(self, request: Request):
        latest_img, latest_html = self.get_latest_graphs()
        return self.templates.TemplateResponse("index.html", {
            "request": request,
            "latest_img": latest_img,
            "latest_html": latest_html
        })

    async def preview_page(self,request: Request):
        graphs = self.get_ordered_graphs()
        return self.templates.TemplateResponse("preview.html", {"request": request, "graphs": graphs})

    
    def show_port(self):
        print(f"Servidor corriendo en http://localhost:{self.port}")
    
    def generate_history(self):
        # Verifica que el archivo de historial exista; si no, lo crea vacío
        history_path = os.path.join(os.path.dirname(__file__), "static", "graph_history.json")
        if not os.path.exists(history_path):
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            with open(history_path, "w") as f:
                json.dump([], f)
            print(f"[INFO] Archivo de historial creado en {history_path}")


    def start_server(self, port):
        self.generate_history()
        self.port = port
        self.start = True
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        self.show_port()

    def get_ordered_graphs(self):
        """Lee el historial de gráficos en el orden en que se generaron."""
        history_file = os.path.join(self.base_path, "static", "graph_history.json")
    
        if not os.path.exists(history_file):
            return []
    
        with open(history_file, "r") as f:
            return json.load(f)

    async def latest_image(self):
        """
        Devuelve la lista de gráficos en formato JSON, manteniendo el orden de creación.
        """
        graphs = self.get_ordered_graphs()
        return JSONResponse(content={"graphs": graphs})

    def notify_update(self):
        if self.ws_connection is not None and self.loop is not None:
            asyncio.run_coroutine_threadsafe(self.msg_notify_update(), self.loop)

    async def msg_notify_update(self):
        try:
            await self.ws_connection.send_text("update")
        except Exception:
            self.ws_connection = None

    def stop_server(self):
        if not self.start:
            return
        self.start = False
        if self.server is not None:
            self.server.should_exit = True
            self.clear_graphs()
        if hasattr(self, 'server_thread') and self.server_thread is not None:
            self.server_thread.join()

        # ✅ Borrar historial de gráficos
        try:
            from .graph_generator import Graph
            Graph().clear_history()
            print("🧹 Historial de gráficos borrado.")
        except Exception as e:
            print(f"[pyvmote] No se pudo borrar el historial: {e}")

        print("Servidor detenido.")



    def clear_graphs(self):
        """
        Borra todo el contenido de la carpeta de imágenes y de gráficos interactivos.
        """
        for folder in [self.image_folder, self.html_folder]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"No se pudo borrar {file_path}. Motivo: {e}")

    async def rename_graph(self, request: Request):
        data = await request.json()
        old_title = data.get("old_title")
        new_title = data.get("new_title")

        if not old_title or not new_title:
            return JSONResponse(content={"error": "Faltan parámetros"}, status_code=400)

        # Sanear nuevo título como lo hace internamente Graph
        new_title_sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', new_title.replace(' ', '_'))

        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return JSONResponse(content={"error": "No hay historial"}, status_code=404)

        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        if any(g["title"] == new_title_sanitized for g in history):
            return JSONResponse(content={"error": "Ya existe un gráfico con ese título"}, status_code=400)

        try:
            Graph().rename_graph(old_title, new_title)
            print(f"[INFO] Gráfico renombrado: {old_title} → {new_title_sanitized}")
        except Exception as e:
            return JSONResponse(content={"error": f"No se pudo renombrar: {str(e)}"}, status_code=500)

        self.notify_update()
        return JSONResponse(content={"message": "Título actualizado"})