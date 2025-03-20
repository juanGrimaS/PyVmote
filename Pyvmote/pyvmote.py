from .Graph_generator import Graph
from .Service import Server

class Pyvmote:
    def __init__(self):
        self.gr = Graph()
        self.sv = Server()

    def plot(self, x, y, xname="X", yname="Y", title="graph", interactive=False):
        """
        Genera un gráfico y notifica al servidor si está activo.
        - interactive: Si es True, genera un gráfico interactivo en HTML.
        - Si es False, genera una imagen en PNG.
        """
        plot_file = self.gr.plot(x, y, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def start_server(self, puerto):
        self.sv.start_server(puerto)

    def stop_server(self):
        self.sv.stop_server()
        self.gr.clear_history()


