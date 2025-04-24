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

class Server:
    def __init__(self):
        self.port = ""
        self.app = FastAPI()
        self.ws_connection = None 
        self.last_timestamp = 0
        self.loop = None
        self.start = False
        self.init_server()
    
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
        images = self.get_image_files()
        htmls = self.get_html_files()
        return images, htmls

    async def index(self, request: Request):
        latest_img, latest_html = self.get_latest_graphs()
        return self.templates.TemplateResponse("index.html", {"request": request, "latest_img": latest_img[0] if latest_img else None, "latest_html": latest_html[0] if latest_html else None})
    
    async def preview_page(self,request: Request):
        graphs = self.get_ordered_graphs()
        return self.templates.TemplateResponse("preview.html", {"request": request, "graphs": graphs})

    
    def show_port(self):
        print(f"Servidor corriendo en http://localhost:{self.port}")

    def start_server(self, port):
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
        if self.server is not None:
            self.start = False
            self.server.should_exit = True
            self.clear_graphs()
        if hasattr(self, 'server_thread') and self.server_thread is not None:
            self.server_thread.join()
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

        history_file = os.path.join(self.base_path, "static", "graph_history.json")
        if not os.path.exists(history_file):
            return JSONResponse(content={"error": "No hay historial"}, status_code=404)

        with open(history_file, "r") as f:
            history = json.load(f)

        updated = False
        for graph in history:
            if graph["title"] == old_title:
                graph["title"] = new_title
                updated = True
                break

        if updated:
            with open(history_file, "w") as f:
                json.dump(history, f)
            return JSONResponse(content={"message": "Título actualizado"})
        else:
            return JSONResponse(content={"error": "Gráfico no encontrado"}, status_code=404)
