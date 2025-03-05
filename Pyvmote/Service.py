from fastapi import FastAPI, WebSocketDisconnect, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import asyncio
import threading
import shutil

"""
Clase que se encarga sel inicio del servidor
"""
class Server:

    def __init__(self):
        self.port = ""
        self.app = FastAPI()
        self.ws_connection = None # Conexion de web socket
        self.last_timestamp = 0
        self.loop = None
        self.start = False

        # Inicializar configuración del servidor y configura rutas HTTP, archivos estáticos, templates, etc.
        self.init_server()
    
    def init_server(self):
        """
        Configuracion de inicio del servidor
        """
         # Definir rutas base y carpetas
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.image_folder = os.path.join(self.base_path, "static", "images")
        self.templates_path = os.path.join(self.base_path, "templates")
        
        # Montar archivos estáticos (CSS, JavaScript, imágenes)
        self.app.mount("/static", StaticFiles(directory=os.path.join(self.base_path, "static")), name="static")
        
        # Configurar el motor de plantillas Jinja2 para renderizar HTML dinámico
        self.templates = Jinja2Templates(directory=self.templates_path)
        
        # Registrar rutas HTTP
        self.app.get("/")(self.index)
        self.app.get("/latest")(self.latest_image)
        
        # Para iniciar el evento de startup y capturar el loop
        self.app.on_event("startup")(self.startup_event)

        #Ruta del web socket
        self.app.websocket("/ws")(self.websocket_endpoint)

    async def startup_event(self):
        self.loop = asyncio.get_running_loop()

    async def websocket_endpoint(self, websocket: WebSocket):
        """
        Se queda en espera para recibir mensajes del websocket
        """
        await websocket.accept()
        self.ws_connection = websocket  # Asigna la conexión actual
        try:
            # Mantén la conexión abierta esperando mensajes (aunque no sean necesarios)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.ws_connection = None  # Cuando se desconecta, la variable se vuelve None

    def get_image_files(self):
        """
        Busca y devuelve una lista de imagenes válidss dentro de la carpeta de imágenes.
        """
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        if not os.path.exists(self.image_folder):
            return []
        files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(valid_extensions)] #Obtiene todas los files de images
        return files

    def get_latest_image(self):
        """
        Retorna el nombre y el timestamp de la imagen más reciente según la fecha de modificación.
        Si no hay imágenes, devuelve None
        """
        files = self.get_image_files()
        if not files:
            return None, 0
        
        full_paths = [os.path.join(self.image_folder, f) for f in files]
        latest_file = max(full_paths, key=os.path.getmtime)
        timestamp = os.path.getmtime(latest_file)
        return os.path.basename(latest_file), timestamp

    async def index(self, request: Request):
        """
        metodo que renderiza la plantilla principal 'index.html' utilizando Jinja2.
        Se envia a la plantilla la información de la última imagen (nombre y timestamp).
        """
        latest_img, timestamp = self.get_latest_image()
        return self.templates.TemplateResponse("index.html", {"request": request, "latest_img": latest_img, "timestamp": timestamp})

    async def latest_image(self):
        """
        metodo que devuelve en formato JSON la información de la última imagen.
        """
        latest_img, timestamp = self.get_latest_image()
        return JSONResponse(content={"filename": latest_img, "timestamp": timestamp})
    
    def show_port(self):
        print(f"Servidor corriendo en http://localhost:{self.port}")

    def start_server(self, port):
        """
        Inicia el servidor en otro hilo para no bloquear la terminal actual.
        """
        self.port = port
        self.start = True
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        self.show_port()

    def notify_update(self):
        """
        Notifica a la conexión WebSocket (si existe) para recargar la página.
        """
        if self.ws_connection is not None and self.loop is not None:
            asyncio.run_coroutine_threadsafe(self.msg_notify_update(), self.loop)

    async def msg_notify_update(self):
        try:
            await self.ws_connection.send_text("update")
        except Exception:
            self.ws_connection = None

    def stop_server(self):
        """
        Detiene el servidor.
        """
        if self.server is not None:
            self.start = False
            self.server.should_exit = True  # Indica a uvicorn que debe salir
            self.clear_images_folder()
        if hasattr(self, 'server_thread') and self.server_thread is not None:
            self.server_thread.join()  # Espera a que el hilo termine
        print("Servidor detenido.")

    def clear_images_folder(self):
        """
        Borra todo el contenido de la carpeta de imágenes.
        """
        if os.path.exists(self.image_folder):
            for filename in os.listdir(self.image_folder):
                file_path = os.path.join(self.image_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"No se pudo borrar {file_path}. Motivo: {e}")
