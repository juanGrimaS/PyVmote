from .Graph_generator import Graph
from .Service import Server

class Pyvmote:
    def __init__(self):
        self.gr = Graph()
        self.sv = Server()

    def start_server(self, puerto):
        self.sv.start_server(puerto)

    def stop_server(self):
        self.sv.stop_server()
        self.gr.clear_history()

    def line_plot(self, x, y, xname="X", yname="Y", title="Line Graph", interactive=True):
        plot_file = self.gr.line_plot(x, y, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def scatter_plot(self, x, y, xname="X", yname="Y", title="Scatter Plot", interactive=True):
        plot_file = self.gr.scatter_plot(x, y, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def bar_plot(self, x, y, xname="X", yname="Y", title="Bar Plot", interactive=True):
        plot_file = self.gr.bar_plot(x, y, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def hist_plot(self, x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True):
        plot_file = self.gr.hist_plot(x, xname, yname, title, bins, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def box_plot(self, x, xname="", yname="Value", title="Box Plot", interactive=True):
        plot_file = self.gr.box_plot(x, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def density_plot(self, x, xname="X", yname="Density", title="Density Plot", interactive=True):
        plot_file = self.gr.density_plot(x, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file
    
    def export_graph(self, title, extension="jpg", target_folder="exports"):
        ruta = self.gr.save_as_format(title, extension, target_folder)
        print(ruta)




