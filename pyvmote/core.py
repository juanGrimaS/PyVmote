import os
from .graph_generator import Graph
from .service import Server


def _default_output_dir():
    """Carpeta por defecto fuera de site-packages: ~/.pyvmote"""
    return os.path.join(os.path.expanduser("~"), ".pyvmote")


class Pyvmote:
    def __init__(self, output_dir=None):
        self.output_dir = os.path.abspath(output_dir or _default_output_dir())
        os.makedirs(self.output_dir, exist_ok=True)
        # Instanciamos Graph apuntando al output_dir externo.
        self.gr = Graph(output_dir=self.output_dir)
        # El Server recibe OBLIGATORIAMENTE la misma instancia de Graph
        # y el mismo output_dir → comparten estado en memoria y disco.
        self.sv = Server(graph=self.gr, output_dir=self.output_dir)

    # ------------------------------------------------------------------
    #  Configuración
    # ------------------------------------------------------------------
    def configure(self, output_dir=None):
        """Reconfigura el directorio de salida en caliente."""
        if output_dir is None:
            output_dir = _default_output_dir()
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.gr.configure(output_dir=self.output_dir)
        self.sv.configure(output_dir=self.output_dir)
        return self.output_dir

    # ------------------------------------------------------------------
    #  Servidor
    # ------------------------------------------------------------------
    def start_server(self, puerto):
        self.sv.start_server(puerto)

    def stop_server(self):
        self.gr.clear_history()
        self.sv.stop_server()

    # ------------------------------------------------------------------
    #  Gráficos
    # ------------------------------------------------------------------
    def _emit(self, plot_file):
        if self.sv.start:
            self.sv.notify_update()
        return plot_file

    def line_plot(self, x, y=None, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None, labels=None):
        return self._emit(self.gr.line_plot(x, y, xname, yname, title, interactive, color, linewidth, xlim, ylim, labels))

    def scatter_plot(self, x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None, labels=None):
        return self._emit(self.gr.scatter_plot(x, y, xname, yname, title, interactive, color, xlim, ylim, labels))

    def bar_plot(self, x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None, labels=None):
        return self._emit(self.gr.bar_plot(x, y, xname, yname, title, interactive, color, xlim, ylim, labels))

    def hist_plot(self, x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
        return self._emit(self.gr.hist_plot(x, xname, yname, title, bins, interactive, color, xlim, ylim))

    def box_plot(self, x=None, xname="", yname="Value", title="Box Plot", interactive=True, color=None, labels=None):
        return self._emit(self.gr.box_plot(x, xname, yname, title, interactive, color, labels))

    def density_plot(self, x=None, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None):
        return self._emit(self.gr.density_plot(x, xname, yname, title, interactive, color, xlim, ylim))

    def pie_plot(self, sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
        return self._emit(self.gr.pie_plot(sizes, labels, title, interactive, colors))

    def cluster_plot(self, data, labels=None, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None, color=None, xname=None, yname=None, series_labels=None):
        return self._emit(self.gr.cluster_plot(data, labels, title, interactive, cmap, xlim, ylim, color, xname, yname, series_labels))

    # ------------------------------------------------------------------
    #  Exportación / renombrado
    # ------------------------------------------------------------------
    def export_graph(self, title, extension="png", target_folder=None):
        if target_folder is None:
            target_folder = os.path.join(self.output_dir, "exports")
        return self.gr.save_as_format(title, extension=extension, target_folder=target_folder)

    def rename_graph(self, old_title, new_title):
        result = self.gr.rename_graph(old_title, new_title)
        if self.sv.start:
            self.sv.notify_update()
        return result
