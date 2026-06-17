from fastapi import FastAPI, WebSocketDisconnect, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
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
        self.port = 0
        self.ws_connection = None
        self.last_timestamp = 0
        self.loop = None
        self.start = False
        self.server = None
        self.server_thread = None
        self._hooks_registered = False

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Equivalente moderno a on_event("startup")
            self.loop = asyncio.get_running_loop()
            yield

        self.app = FastAPI(lifespan=lifespan)
        self.init_server()
        self._register_shutdown_hooks()

    # ------------------------------------------------------------------
    #  Configuración inicial
    # ------------------------------------------------------------------
    def init_server(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.image_folder = os.path.join(self.base_path, "static", "images")
        self.html_folder = os.path.join(self.base_path, "static", "html")
        self.templates_path = os.path.join(self.base_path, "templates")

        # Garantizamos que las carpetas existan antes de montarlas
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.html_folder, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "static"), exist_ok=True)

        self.app.mount(
            "/static",
            StaticFiles(directory=os.path.join(self.base_path, "static")),
            name="static",
        )

        self.templates = Jinja2Templates(directory=self.templates_path)

        self.app.get("/")(self.index)
        self.app.add_api_route("/preview", self.preview_page)
        self.app.add_api_route("/view/{kind}/{title}", self.view_graph)
        self.app.get("/latest")(self.latest_image)
        self.app.add_api_route("/rename", self.rename_graph, methods=["POST"])
        self.app.websocket("/ws")(self.websocket_endpoint)

    def _register_shutdown_hooks(self):
        if self._hooks_registered:
            return

        def safe_shutdown(*args):
            if self.start:
                print("[pyvmote] Deteniendo servidor automáticamente...")
                self.stop_server()
                if args:
                    sys.exit(0)

        atexit.register(safe_shutdown)

        # signal.signal sólo funciona en el hilo principal
        if threading.current_thread() is threading.main_thread():
            try:
                signal.signal(signal.SIGINT, safe_shutdown)
                signal.signal(signal.SIGTERM, safe_shutdown)
            except (ValueError, OSError):
                # Entornos como notebooks pueden no permitirlo
                pass

        self._hooks_registered = True

    # ------------------------------------------------------------------
    #  WebSocket
    # ------------------------------------------------------------------
    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.ws_connection = websocket
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.ws_connection = None

    # ------------------------------------------------------------------
    #  Páginas
    # ------------------------------------------------------------------
    def get_latest_graphs(self):
        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return None, None

        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        if not history:
            return None, None

        latest = history[-1]
        if latest["type"] == "html":
            return None, latest["title"] + ".html"
        elif latest["type"] == "image":
            return latest["title"] + ".png", None
        return None, None

    async def index(self, request: Request):
        latest_img, latest_html = self.get_latest_graphs()
        return self.templates.TemplateResponse(
            request,
            "index.html",
            {"latest_img": latest_img, "latest_html": latest_html},
        )

    async def preview_page(self, request: Request):
        graphs = self.get_ordered_graphs()
        return self.templates.TemplateResponse(
            request, "preview.html", {"graphs": graphs}
        )

    async def view_graph(self, request: Request, kind: str, title: str):
        safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title.replace(" ", "_"))
        kind = "html" if kind == "html" else "image"
        return self.templates.TemplateResponse(
            request, "viewer.html", {"title": safe_title, "kind": kind}
        )

    # ------------------------------------------------------------------
    #  Ciclo de vida del servidor
    # ------------------------------------------------------------------
    def show_port(self):
        print(f"Servidor PyVmote corriendo en http://localhost:{self.port}")

    def generate_history(self):
        history_path = os.path.join(
            os.path.dirname(__file__), "static", "graph_history.json"
        )
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        if not os.path.exists(history_path):
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"[INFO] Archivo de historial creado en {history_path}")

    def start_server(self, port):
        if self.start:
            print("[pyvmote] El servidor ya está en ejecución.")
            return
        self.generate_history()
        try:
            self.port = int(port)
        except (TypeError, ValueError):
            raise ValueError(f"Puerto inválido: {port!r}")
        self.start = True
        config = uvicorn.Config(
            self.app, host="0.0.0.0", port=self.port, log_level="warning"
        )
        self.server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        self.show_port()

    def get_ordered_graphs(self):
        """Lee el historial de gráficos en el orden en que se generaron."""
        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return []
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)

    async def latest_image(self):
        """Devuelve la lista de gráficos en formato JSON."""
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
        if self.server_thread is not None:
            try:
                self.server_thread.join(timeout=5)
            except Exception:
                pass

        # Borrar historial de gráficos
        try:
            Graph().clear_history()
            print("Historial de gráficos borrado.")
        except Exception as e:
            print(f"[pyvmote] No se pudo borrar el historial: {e}")

        print("Servidor detenido.")

    def clear_graphs(self):
        """Borra el contenido de las carpetas de imágenes y gráficos interactivos."""
        for folder in [self.image_folder, self.html_folder]:
            if not os.path.exists(folder):
                continue
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"No se pudo borrar {file_path}. Motivo: {e}")

    # ------------------------------------------------------------------
    #  Renombrar gráficos
    # ------------------------------------------------------------------
    async def rename_graph(self, request: Request):
        data = await request.json()
        old_title = data.get("old_title")
        new_title = data.get("new_title")

        if not old_title or not new_title:
            return JSONResponse(content={"error": "Faltan parámetros"}, status_code=400)

        new_title_sanitized = re.sub(
            r"[^a-zA-Z0-9_-]", "_", new_title.replace(" ", "_")
        )

        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return JSONResponse(content={"error": "No hay historial"}, status_code=404)

        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        if any(g["title"] == new_title_sanitized for g in history):
            return JSONResponse(
                content={"error": "Ya existe un gráfico con ese título"},
                status_code=400,
            )

        try:
            Graph().rename_graph(old_title, new_title)
            print(f"[INFO] Gráfico renombrado: {old_title} → {new_title_sanitized}")
        except Exception as e:
            return JSONResponse(
                content={"error": f"No se pudo renombrar: {str(e)}"},
                status_code=500,
            )

        self.notify_update()
        return JSONResponse(content={"ok": True, "new_title": new_title_sanitized})
