from .Graph_generator import Graph
from .Service import Server

class Pyvmote:
    def __init__(self):
        self.gr = Graph()
        self.sv = Server()
    
    def plot(self, x, y, xname="X", yname="Y", title="graph"):
        self.gr.plot(x, y, xname, yname, title)
        if(self.sv.start):
            self.sv.notify_update()

    def start_server(self, puerto):
        self.sv.start_server(puerto)

    def stop_server(self):
        self.sv.stop_server()

