import matplotlib.pyplot as plt
import mpld3
from mpld3 import plugins
import os
import json
from scipy.stats import gaussian_kde
import numpy as np
import re
import shutil
import warnings

class Graph:
    def __init__(self):
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.path = os.path.dirname(os.path.abspath(__file__))
        self.n_plot = 0
        self.history_file = os.path.join(self.path, "static", "graph_history.json")

        if not os.path.exists(self.history_file):
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def clear_history(self):
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def save_graph_to_history(self, graph_name, graph_type, title):
        with open(self.history_file, "r") as f:
            history = json.load(f)

        # Verifica si ya existe un gráfico con ese título
        for graph in history:
            if graph["title"] == title:
                raise ValueError(f"Ya existe un gráfico con el título '{title}'. Usa uno diferente.")

        history.append({"name": graph_name, "type": graph_type, "title": title})

        with open(self.history_file, "w") as f:
            json.dump(history, f)

    def _sanitize_title(self, title):
        return re.sub(r'[^a-zA-Z0-9_-]', '_', title.replace(' ', '_'))

    def _prepare_paths(self, title):
        images_dir = os.path.join(self.path, "static", "images")
        html_dir = os.path.join(self.path, "static", "html")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)

        safe_title = self._sanitize_title(title)
        image_name = f"{safe_title}.png"
        html_name = f"{safe_title}.html"

        return images_dir, html_dir, image_name, html_name

    def _finalize_plot(self, fig, image_path, html_path, labels, scatter, plot_type, interactive, title):
        if interactive:
            if labels and plot_type in ["line", "scatter", "bar", "density"]:
                if plot_type == "bar":
                    for rect, label in zip(scatter, labels):
                        plugins.connect(fig, plugins.LineLabelTooltip(rect, label))
                else:
                    plugins.connect(fig, plugins.PointLabelTooltip(scatter[0], labels=labels))

            mpld3.save_html(fig, html_path)
            self.save_graph_to_history(os.path.basename(html_path), "html", title)
            plt.close()
            return os.path.basename(html_path)
        else:
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history(os.path.basename(image_path), "image", title)
            plt.close()
            return os.path.basename(image_path)

    def save_as_format(self, fig, title, extension="png"):
        valid_exts = ["png", "jpg", "jpeg", "svg", "pdf"]
        if extension not in valid_exts:
            raise ValueError(f"Formato no soportado: {extension}")

        output_dir = os.path.join(self.path, "static", "images")
        os.makedirs(output_dir, exist_ok=True)
        safe_title = self._sanitize_title(title)
        output_path = os.path.join(output_dir, f"{safe_title}.{extension}")
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        return output_path

    def line_plot(self, x, y, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.plot(x, y, marker='o', linestyle='-', color=color, linewidth=linewidth)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), labels, scatter, "line", interactive, title)


    def scatter_plot(self, x, y, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.scatter(x, y, color=color)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), labels, [scatter], "scatter", interactive, title)

    def bar_plot(self, x, y, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.bar(x, y, color=color)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), labels, scatter, "bar", interactive, title)

    def hist_plot(self, x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.hist(x, bins=bins, edgecolor='black', color=color)
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), [], [], "hist", interactive, title)

    def box_plot(self, x, xname="", yname="Value", title="Box Plot", interactive=True):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.boxplot(x)
        ax.set_ylabel(yname)
        ax.set_xlabel(xname)
        ax.set_title(title)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), [], [], "box", interactive, title)

    def density_plot(self, x, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        kde = gaussian_kde(x)
        x_vals = np.linspace(min(x), max(x), 200)
        y_vals = kde(x_vals)
        scatter = ax.plot(x_vals, y_vals, color=color)
        labels = [f"({xi:.2f}, {yi:.2f})" for xi, yi in zip(x_vals, y_vals)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), labels, scatter, "density", interactive, title)
    
    def pie_plot(self, sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title(title)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), [], [], "pie", interactive, title)
    
    def cluster_plot(self, data, labels, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None):
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.scatter(data[:, 0], data[:, 1], c=labels, cmap=cmap)
        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        images_dir, html_dir, image_name, html_name = self._prepare_paths(title)
        return self._finalize_plot(fig, os.path.join(images_dir, image_name), os.path.join(html_dir, html_name), [], [scatter], "cluster", interactive, title)

# 4. Personalización en otros gráficos

    
    def save_as_format(self, title, extension="png", target_folder="exports"):
    
        valid_exts = ["png", "jpg", "jpeg", "svg", "pdf"]
        if extension not in valid_exts:
            raise ValueError(f"Formato no soportado: {extension}")

        safe_title = self._sanitize_title(title)
        original_path = os.path.join(self.path, "static", "images", f"{safe_title}.png")
    
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"No se encontró el gráfico original: {original_path}")

        # Crear carpeta destino si no existe
        os.makedirs(target_folder, exist_ok=True)
        output_path = os.path.join(target_folder, f"{safe_title}.{extension}")

        # Si el formato es el mismo, simplemente copiar
        if extension == "png":
            shutil.copyfile(original_path, output_path)
        else:
            # Leer imagen y volver a guardarla en nuevo formato
            from PIL import Image
            with Image.open(original_path) as img:
                format_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "pdf": "PDF", "svg": "SVG"}
                img.convert("RGB").save(output_path, format_map[extension.lower()])

        return output_path