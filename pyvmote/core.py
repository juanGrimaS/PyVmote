from .graph_generator import Graph
from .service import Server

class Pyvmote:
    def __init__(self):
        self.gr = Graph()
        self.sv = Server()

    def start_server(self, puerto):
        self.sv.start_server(puerto)

    def stop_server(self):
        self.gr.clear_history()
        self.sv.stop_server()

    def line_plot(self, x, y=None, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None):
        plot_file = self.gr.line_plot(x, y, xname, yname, title, interactive, color, linewidth, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def scatter_plot(self, x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None):
        plot_file = self.gr.scatter_plot(x, y, xname, yname, title, interactive, color, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def bar_plot(self, x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None):
        plot_file = self.gr.bar_plot(x, y, xname, yname, title, interactive, color, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def hist_plot(self, x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
        plot_file = self.gr.hist_plot(x, xname, yname, title, bins, interactive, color, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def box_plot(self, x=None, xname="", yname="Value", title="Box Plot", interactive=True):
        plot_file = self.gr.box_plot(x, xname, yname, title, interactive)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def density_plot(self, x=None, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None):
        plot_file = self.gr.density_plot(x, xname, yname, title, interactive, color, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file
    
    def pie_plot(self, sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
        plot_file = self.gr.pie_plot(sizes, labels, title, interactive, colors)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file
    
    def cluster_plot(self, data, labels, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None):
        plot_file = self.gr.cluster_plot(data, labels, title, interactive, cmap, xlim, ylim)
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def export_graph(self, title, extension="jpg", target_folder="exports"):
        ruta = self.gr.save_as_format(title, extension, target_folder)
        print(ruta)




