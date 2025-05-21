import matplotlib
matplotlib.use("Agg")

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
import pandas as pd
from PIL import Image
from pathlib import Path

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

    def save_graph_to_history(self, graph_type, title, meta=None):
        title = self._sanitize_title(title)

        with open(self.history_file, "r") as f:
            history = json.load(f)

        for graph in history:
            if graph["title"] == title and graph["type"] == graph_type:
                return

        entry = {"type": graph_type, "title": title}
        if meta:
            entry.update(meta)

        history.append(entry)
        with open(self.history_file, "w") as f:
            json.dump(history, f)

    def _sanitize_title(self, title):
        return re.sub(r'[^a-zA-Z0-9_-]', '_', title.replace(' ', '_'))
    
    def _ensure_list(self, arr):
        return arr.tolist() if hasattr(arr, "tolist") else arr

    def _prepare_paths(self, title):
        images_dir = os.path.join(self.path, "static", "images")
        html_dir = os.path.join(self.path, "static", "html")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)

        safe_title = self._sanitize_title(title)
        return images_dir, html_dir, f"{safe_title}.png", f"{safe_title}.html"

    def _extract_from_dataframe(self, data, xname, yname):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("El objeto no es un DataFrame")
        if xname not in data.columns or yname not in data.columns:
            raise ValueError(f"Columnas '{xname}' o '{yname}' no están en el DataFrame.")
        return data[xname], data[yname]

    def _finalize_plot(self, fig, image_path, html_path, labels, scatter, plot_type, interactive, title, meta=None):
        meta = meta or {}
        meta.update({"plot_type": plot_type, "interactive": interactive})

        if interactive:
            if labels and plot_type in ["line", "scatter", "bar", "density"]:
                if plot_type == "bar":
                    for rect, label in zip(scatter, labels):
                        plugins.connect(fig, plugins.LineLabelTooltip(rect, label))
                else:
                    plugins.connect(fig, plugins.PointLabelTooltip(scatter[0], labels=labels))

            mpld3.save_html(fig, html_path)
            fig.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history("html", title, meta)
        else:
            fig.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history("image", title, meta)

        plt.close()
        return os.path.basename(html_path if interactive else image_path)

    def line_plot(self, x, y=None, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None):
        if isinstance(x, pd.DataFrame):
            x, y = self._extract_from_dataframe(x, xname, yname)
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.plot(x, y, marker='o', linestyle='-', color=color, linewidth=linewidth)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "y": self._ensure_list(y), "xname": xname, "yname": yname, "color": color, "linewidth": linewidth, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), labels, scatter, "line", interactive, title, meta)

    def scatter_plot(self, x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None):
        if isinstance(x, pd.DataFrame):
            x, y = self._extract_from_dataframe(x, xname, yname)
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.scatter(x, y, color=color)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "y": self._ensure_list(y), "xname": xname, "yname": yname, "color": color, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), labels, [scatter], "scatter", interactive, title, meta)

    def bar_plot(self, x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None):
        if isinstance(x, pd.DataFrame):
            x, y = self._extract_from_dataframe(x, xname, yname)
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.bar(x, y, color=color)
        labels = [f"({xi}, {yi})" for xi, yi in zip(x, y)]
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "y": self._ensure_list(y), "xname": xname, "yname": yname, "color": color, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), labels, scatter, "bar", interactive, title, meta)

    def hist_plot(self, x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
        if isinstance(x, pd.DataFrame):
            x = x[xname]
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.hist(x, bins=bins, edgecolor='black', color=color)
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.set_title(title)
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "xname": xname, "yname": yname, "bins": bins, "color": color, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], [], "hist", interactive, title, meta)

    def box_plot(self, x, xname="", yname="Value", title="Box Plot", interactive=True):
        if isinstance(x, pd.DataFrame):
            x = x[x.columns[0]]
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.boxplot(x)
        ax.set_ylabel(yname)
        ax.set_xlabel(xname)
        ax.set_title(title)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "xname": xname, "yname": yname}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], [], "box", interactive, title, meta)

    def density_plot(self, x, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None):
        if isinstance(x, pd.DataFrame):
            x = x[xname]
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
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(x), "xname": xname, "yname": yname, "color": color, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), labels, scatter, "density", interactive, title, meta)

    def pie_plot(self, sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title(title)
        paths = self._prepare_paths(title)
        meta = {"sizes": sizes, "labels": labels, "colors": colors}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], [], "pie", interactive, title, meta)

    def cluster_plot(self, data, labels, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None):
        data = np.array(data)
        labels = np.array(labels)

        if data.ndim != 2 or data.shape[1] != 2:
            raise ValueError("El parámetro 'data' debe tener forma (n, 2) con coordenadas X e Y.")
        
        fig, ax = plt.subplots(figsize=(12, 7))
        scatter = ax.scatter(data[:, 0], data[:, 1], c=labels, cmap=cmap)
        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)

        if interactive:
            point_labels = [f"({x:.2f}, {y:.2f})" for x, y in data]
            plugins.connect(fig, plugins.PointLabelTooltip(scatter, labels=point_labels))

        paths = self._prepare_paths(title)
        meta = {
            "data": self._ensure_list(data), 
            "labels": self._ensure_list(labels),
            "cmap": cmap,
            "xlim": xlim,
            "ylim": ylim
        }

        return self._finalize_plot(fig,
            os.path.join(paths[0], paths[2]),
            os.path.join(paths[1], paths[3]),
            [], [scatter], "cluster", interactive, title, meta)



    def rename_graph(self, old_title, new_title):
        safe_new_title = self._sanitize_title(new_title)

        with open(self.history_file, "r") as f:
            history = json.load(f)

        updated = False

        for graph in history:
            if graph["title"] == old_title:
                plot_type = graph.get("plot_type")
                interactive = graph.get("interactive", True)

                # Eliminar archivos anteriores
                for ext in [".png", ".html"]:
                    for folder in ["images", "html"]:
                        path = os.path.join(self.path, "static", folder, f"{old_title}{ext}")
                        if os.path.exists(path):
                            os.remove(path)

                # Regenerar gráfico según tipo
                if plot_type == "line":
                    self.line_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        linewidth=graph.get("linewidth", 2),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "scatter":
                    self.scatter_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "bar":
                    self.bar_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "hist":
                    self.hist_plot(graph["x"],
                        xname=graph.get("xname", "Value"), yname=graph.get("yname", "Frequency"),
                        title=safe_new_title, bins=graph.get("bins", 20),
                        interactive=interactive, color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "box":
                    self.box_plot(graph["x"],
                        xname=graph.get("xname", ""), yname=graph.get("yname", "Value"),
                        title=safe_new_title, interactive=interactive)
                elif plot_type == "density":
                    self.density_plot(graph["x"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Density"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "pie":
                    self.pie_plot(graph["sizes"],
                        labels=graph.get("labels"), title=safe_new_title,
                        interactive=interactive, colors=graph.get("colors"))
                elif plot_type == "cluster":
                    data = np.array(graph.get("data") or graph.get("x")) 
                    labels = np.array(graph["labels"])
                    self.cluster_plot(
                        data,
                        labels=labels,
                        title=safe_new_title,
                        interactive=interactive,
                        cmap=graph.get("cmap", "viridis"),
                        xlim=graph.get("xlim"),
                        ylim=graph.get("ylim")
                    )
                else:
                    raise ValueError(f"Tipo de gráfico no soportado: {plot_type}")

                updated = True
                break  # Ya hemos procesado el gráfico

        if not updated:
            raise ValueError(f"Título no encontrado: {old_title}")

        with open(self.history_file, "r") as f:
            regenerated = json.load(f)

        cleaned = [g for g in regenerated if g["title"] != old_title]

        with open(self.history_file, "w") as f:
            json.dump(cleaned, f)


    def save_as_format(self, title, extension="png", target_folder="exports"):
        valid_exts = ["png", "jpg", "jpeg", "svg", "pdf"]
        if extension.lower() not in valid_exts:
            raise ValueError(f"Formato no soportado: {extension}")

        safe_title = self._sanitize_title(title)
        original_path = os.path.join(self.path, "static", "images", f"{safe_title}.png")

        if not os.path.exists(original_path):
            raise FileNotFoundError(f"No se encontró el gráfico original: {original_path}")

        os.makedirs(target_folder, exist_ok=True)
        output_path = os.path.join(target_folder, f"{safe_title}.{extension}")

        if extension.lower() == "png":
            shutil.copyfile(original_path, output_path)
        else:
            from PIL import Image
            with Image.open(original_path) as img:
                # Mapeo de extensiones a formatos válidos para Pillow
                format_map = {
                    "jpg": "JPEG",
                    "jpeg": "JPEG",
                    "png": "PNG",
                    "pdf": "PDF",
                    "svg": "SVG"
                }
                img_format = format_map.get(extension.lower())
                if not img_format:
                    raise ValueError(f"Formato no soportado: {extension}")
                img.convert("RGB").save(output_path, img_format)

        return output_path
