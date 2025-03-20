import matplotlib.pyplot as plt
import mpld3
from mpld3 import plugins
import os
import json

class Graph:
    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.n_plot = 0
        self.history_file = os.path.join(self.path, "static", "graph_history.json")

        # Crear archivo de historial si no existe
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def save_graph_to_history(self, graph_name, graph_type):
        """Guarda el gráfico en la lista en el orden en que se generó."""
        with open(self.history_file, "r") as f:
            history = json.load(f)

        history.append({"name": graph_name, "type": graph_type})

        with open(self.history_file, "w") as f:
            json.dump(history, f)

    def clear_history(self):
        """Borra el archivo de historial al cerrar el servidor."""
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def plot(self, x, y, xname="X", yname="Y", title="graph", interactive=False):
        images_dir = os.path.join(self.path, "static", "images")
        html_dir = os.path.join(self.path, "static", "html")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        fig, ax = plt.subplots(figsize=(12, 7))  # Asegurar tamaño grande del gráfico
        scatter = ax.plot(x, y, marker='o', linestyle='-')

        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)

        # Agregar tooltips interactivos
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        tooltip = plugins.PointLabelTooltip(scatter[0], labels=labels)
        plugins.connect(fig, tooltip)

        image_name = f"grafico{self.n_plot}.png"
        html_name = f"grafico{self.n_plot}.html"
        self.n_plot += 1
        image_path = os.path.join(images_dir, image_name)
        html_path = os.path.join(html_dir, html_name)

        if interactive:
            mpld3.save_html(fig, html_path)
            self.save_graph_to_history(html_name, "html")
            plt.close()
            return html_name  # Devuelve el nombre del archivo HTML
        else:
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history(image_name, "image")
            plt.close()
            return image_name  # Devuelve el nombre del archivo de imagen
