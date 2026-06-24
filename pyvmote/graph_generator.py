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
    def __init__(self, output_dir=None):
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.package_path = os.path.dirname(os.path.abspath(__file__))
        self.n_plot = 0
        self._apply_output_dir(output_dir)

    def _apply_output_dir(self, output_dir):
        if output_dir is None:
            output_dir = os.path.join(os.path.expanduser("~"), ".pyvmote")
        self.output_dir = os.path.abspath(output_dir)
        # Mantenemos `self.path` por compatibilidad con código existente,
        # pero ahora apunta SIEMPRE al directorio externo del usuario,
        # nunca dentro de site-packages.
        self.path = self.output_dir
        self.history_file = os.path.join(self.output_dir, "static", "graph_history.json")

        os.makedirs(os.path.join(self.output_dir, "static"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "static", "images"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "static", "html"), exist_ok=True)

        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def configure(self, output_dir=None):
        """Permite cambiar en caliente el directorio de salida."""
        self._apply_output_dir(output_dir)
        return self.output_dir

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
        if isinstance(arr, dict):
            return {str(k): self._ensure_list(v) for k, v in arr.items()}
        if isinstance(arr, range):
            return list(arr)
        if isinstance(arr, (list, tuple)):
            return [self._ensure_list(v) for v in arr]
        if hasattr(arr, "tolist"):
            return arr.tolist()
        if isinstance(arr, np.generic):
            return arr.item()
        return arr

    def _is_sequence(self, value):
        return isinstance(value, (list, tuple, np.ndarray, pd.Series)) and not isinstance(value, (str, bytes))

    def _is_nested_sequence(self, value):
        if isinstance(value, np.ndarray):
            return value.ndim > 1
        if isinstance(value, pd.Series) or not self._is_sequence(value):
            return False
        value = list(value)
        return bool(value) and self._is_sequence(value[0])

    def _dataset_to_dataframe(self, data):
        """Acepta DataFrame o datasets tipo sklearn (Bunch con .data/.target)."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if hasattr(data, "data"):
            values = np.asarray(data.data)
            if values.ndim != 2:
                return None
            columns = list(getattr(data, "feature_names", []) or [])
            if len(columns) != values.shape[1]:
                columns = [f"feature_{i}" for i in range(values.shape[1])]
            df = pd.DataFrame(values, columns=columns)
            if hasattr(data, "target"):
                df["target"] = np.asarray(data.target)
            return df
        return None

    def _get_column(self, df, column, default_index=0):
        if column is None or column == "":
            return df.iloc[:, default_index]
        if isinstance(column, int):
            return df.iloc[:, column]
        if column in df.columns:
            return df[column]
        raise ValueError(f"La columna '{column}' no existe en el dataset/DataFrame.")

    def _normalize_series_labels(self, labels, n):
        if labels is None:
            return [f"Serie {i + 1}" for i in range(n)]
        if isinstance(labels, str):
            return [labels] if n == 1 else [f"{labels} {i + 1}" for i in range(n)]
        labels = list(labels)
        if len(labels) < n:
            labels += [f"Serie {i + 1}" for i in range(len(labels), n)]
        return [str(label) for label in labels[:n]]

    def _normalize_colors(self, color, n):
        palette = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["blue"])
        if color is None:
            return [palette[i % len(palette)] for i in range(n)]
        if isinstance(color, str):
            return [color] * n
        colors = list(color)
        if not colors:
            return [palette[i % len(palette)] for i in range(n)]
        return [colors[i % len(colors)] for i in range(n)]

    def _normalize_xy_series(self, x, y=None, xname="X", yname="Y", labels=None):
        df = self._dataset_to_dataframe(x)
        if df is not None:
            y_columns = list(yname) if self._is_sequence(yname) and not isinstance(yname, str) else [yname]
            x_columns = list(xname) if self._is_sequence(xname) and not isinstance(xname, str) else [xname] * len(y_columns)
            if len(x_columns) == 1 and len(y_columns) > 1:
                x_columns *= len(y_columns)
            if len(x_columns) != len(y_columns):
                raise ValueError("xname e yname deben tener la misma cantidad de columnas para comparar series.")
            names = self._normalize_series_labels(labels, len(y_columns))
            normalized_x_columns = []
            normalized_y_columns = []
            for x_col, y_col in zip(x_columns, y_columns):
                if isinstance(x_col, str) and x_col not in df.columns and x_col.lower() == "x":
                    x_col = 0
                if isinstance(y_col, str) and y_col not in df.columns and y_col.lower() in ("y", "value"):
                    y_col = 1 if df.shape[1] > 1 else 0
                normalized_x_columns.append(x_col)
                normalized_y_columns.append(y_col)
            return [
                {
                    "x": self._ensure_list(self._get_column(df, x_col, 0)),
                    "y": self._ensure_list(self._get_column(df, y_col, 1)),
                    "label": names[i],
                }
                for i, (x_col, y_col) in enumerate(zip(normalized_x_columns, normalized_y_columns))
            ]

        if isinstance(y, dict):
            names = list(y.keys())
            y_values = list(y.values())
            if isinstance(x, dict):
                x_values = [x.get(name, range(len(vals))) for name, vals in zip(names, y_values)]
            elif x is None:
                x_values = [range(len(vals)) for vals in y_values]
            elif self._is_nested_sequence(x) and len(x) == len(y_values):
                x_values = list(x)
            else:
                x_values = [x] * len(y_values)
            labels = names if labels is None else labels
        elif y is None:
            y_values = list(x) if self._is_nested_sequence(x) else [x]
            x_values = [range(len(vals)) for vals in y_values]
        else:
            y_values = list(y) if self._is_nested_sequence(y) else [y]
            if self._is_nested_sequence(x) and len(x) == len(y_values):
                x_values = list(x)
            else:
                x_values = [x] * len(y_values)

        names = self._normalize_series_labels(labels, len(y_values))
        series = []
        for i, (x_vals, y_vals) in enumerate(zip(x_values, y_values)):
            x_list = self._ensure_list(x_vals)
            y_list = self._ensure_list(y_vals)
            if len(x_list) != len(y_list):
                raise ValueError(f"La serie '{names[i]}' tiene {len(x_list)} valores X y {len(y_list)} valores Y.")
            series.append({"x": x_list, "y": y_list, "label": names[i]})
        return series

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


    def _make_mpld3_responsive(self, html_path):
        """Inyecta CSS/JS para que mpld3 ocupe todo el iframe o visor grande."""
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        injection = """<style>
  html, body {
    margin:0 !important; padding:0 !important; width:100% !important; height:100% !important;
    min-width:0 !important; min-height:0 !important; overflow:hidden !important; background:#ffffff;
    font-family:-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  }
  body { position:relative !important; display:flex !important; align-items:center !important; justify-content:center !important; }
  body > div:not(.mpld3-tooltip), div.mpld3-figure {
    position:relative !important; margin:0 !important; padding:0 !important; overflow:visible !important;
    max-width:100% !important; max-height:100% !important;
  }
  /* Keep aspect ratio so mpld3 toolbar PNG icons stay crisp (no stretching) */
  svg.mpld3-figure, svg {
    display:block !important; max-width:100% !important; max-height:100% !important;
    overflow:visible !important; shape-rendering:geometricPrecision;
  }
  svg image { image-rendering: -webkit-optimize-contrast; image-rendering: auto; }
  .mpld3-toolbar { z-index:20 !important; }
  .mpld3-toolbar image { image-rendering: auto !important; }
  .mpld3-tooltip { z-index:30 !important; }
</style>
<script>
(function () {
  function fitMpld3() {
    var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    document.querySelectorAll('svg.mpld3-figure, svg').forEach(function (svg) {
      var w = parseFloat(svg.getAttribute('width'));
      var h = parseFloat(svg.getAttribute('height'));
      if (!svg.getAttribute('viewBox') && w && h) {
        svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
      }
      svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
      // Scale uniformly to fit the viewport while preserving aspect ratio
      if (w && h) {
        var scale = Math.min(vw / w, vh / h);
        var nw = Math.floor(w * scale);
        var nh = Math.floor(h * scale);
        svg.setAttribute('width', nw);
        svg.setAttribute('height', nh);
        svg.style.width = nw + 'px';
        svg.style.height = nh + 'px';
      }
    });
  }
  window.addEventListener('load', function () {
    fitMpld3();
    setTimeout(fitMpld3, 80);
    setTimeout(fitMpld3, 350);
    setTimeout(fitMpld3, 900);
  });
  window.addEventListener('resize', fitMpld3);
})();
</script>
"""
        if "</head>" in content:
            content = content.replace("</head>", injection + "</head>", 1)
        else:
            content = injection + content
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

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
            self._make_mpld3_responsive(html_path)
            fig.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history("html", title, meta)
        else:
            fig.savefig(image_path, dpi=300, bbox_inches='tight')
            self.save_graph_to_history("image", title, meta)

        plt.close()
        return os.path.basename(html_path if interactive else image_path)

    def line_plot(self, x, y=None, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None, labels=None):
        series = self._normalize_xy_series(x, y, xname, yname, labels)
        colors = self._normalize_colors(color, len(series))
        fig, ax = plt.subplots(figsize=(14, 8))
        plotted = []
        for i, serie in enumerate(series):
            line = ax.plot(serie["x"], serie["y"], marker='o', linestyle='-', color=colors[i], linewidth=linewidth, label=serie["label"])[0]
            plotted.append(line)
            if interactive:
                point_labels = [f"{serie['label']}: ({xi}, {yi})" for xi, yi in zip(serie["x"], serie["y"])]
                plugins.connect(fig, plugins.PointLabelTooltip(line, labels=point_labels))
        ax.set_xlabel(xname if isinstance(xname, str) else "X")
        ax.set_ylabel(yname if isinstance(yname, str) else "Y")
        ax.set_title(title)
        if len(series) > 1:
            ax.legend(loc="best")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": [s["x"] for s in series], "y": [s["y"] for s in series], "labels": [s["label"] for s in series], "xname": xname, "yname": yname, "color": colors, "linewidth": linewidth, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], plotted, "line", interactive, title, meta)

    def scatter_plot(self, x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None, labels=None):
        series = self._normalize_xy_series(x, y, xname, yname, labels)
        colors = self._normalize_colors(color, len(series))
        fig, ax = plt.subplots(figsize=(14, 8))
        scatters = []
        for i, serie in enumerate(series):
            scatter = ax.scatter(serie["x"], serie["y"], color=colors[i], label=serie["label"], s=42)
            scatters.append(scatter)
            if interactive:
                point_labels = [f"{serie['label']}: ({xi}, {yi})" for xi, yi in zip(serie["x"], serie["y"])]
                plugins.connect(fig, plugins.PointLabelTooltip(scatter, labels=point_labels))
        ax.set_xlabel(xname if isinstance(xname, str) else "X")
        ax.set_ylabel(yname if isinstance(yname, str) else "Y")
        ax.set_title(title)
        if len(series) > 1:
            ax.legend(loc="best")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": [s["x"] for s in series], "y": [s["y"] for s in series], "labels": [s["label"] for s in series], "xname": xname, "yname": yname, "color": colors, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], scatters, "scatter", interactive, title, meta)

    def bar_plot(self, x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None, labels=None):
        series = self._normalize_xy_series(x, y, xname, yname, labels)
        colors = self._normalize_colors(color, len(series))
        fig, ax = plt.subplots(figsize=(14, 8))
        containers = []
        max_len = max(len(s["y"]) for s in series)
        base = np.arange(max_len)
        width = min(0.8 / max(len(series), 1), 0.35)
        for i, serie in enumerate(series):
            offset = (i - (len(series) - 1) / 2) * width
            positions = np.arange(len(serie["y"])) + offset
            bars = ax.bar(positions, serie["y"], width=width, color=colors[i], label=serie["label"])
            containers.extend(list(bars))
            if interactive:
                for rect, xi, yi in zip(bars, serie["x"], serie["y"]):
                    plugins.connect(fig, plugins.LineLabelTooltip(rect, f"{serie['label']}: ({xi}, {yi})"))
        tick_labels = [str(v) for v in series[0]["x"][:max_len]]
        if len(tick_labels) < max_len:
            tick_labels += [str(i + 1) for i in range(len(tick_labels), max_len)]
        ax.set_xticks(base)
        ax.set_xticklabels(tick_labels, rotation=0)
        ax.set_xlabel(xname if isinstance(xname, str) else "X")
        ax.set_ylabel(yname if isinstance(yname, str) else "Y")
        ax.set_title(title)
        if len(series) > 1:
            ax.legend(loc="best")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)
        paths = self._prepare_paths(title)
        meta = {"x": [s["x"] for s in series], "y": [s["y"] for s in series], "labels": [s["label"] for s in series], "xname": xname, "yname": yname, "color": colors, "xlim": xlim, "ylim": ylim}
        return self._finalize_plot(fig, os.path.join(paths[0], paths[2]), os.path.join(paths[1], paths[3]), [], containers, "bar", interactive, title, meta)

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

    def box_plot(self, x, xname="", yname="Value", title="Box Plot", interactive=True, color=None, labels=None):
        df = self._dataset_to_dataframe(x)
        if df is not None:
            columns = list(xname) if self._is_sequence(xname) and not isinstance(xname, str) else ([xname] if xname else list(df.select_dtypes(include=[np.number]).columns[:4]))
            data = [self._ensure_list(self._get_column(df, col, i)) for i, col in enumerate(columns)]
            names = self._normalize_series_labels(labels or columns, len(data))
        else:
            data = list(x) if self._is_nested_sequence(x) else [x]
            names = self._normalize_series_labels(labels, len(data))
        colors = self._normalize_colors(color, len(data))
        fig, ax = plt.subplots(figsize=(14, 8))
        try:
            box = ax.boxplot(data, tick_labels=names, patch_artist=True)
        except TypeError:
            box = ax.boxplot(data, labels=names, patch_artist=True)
        for patch, box_color in zip(box.get("boxes", []), colors):
            patch.set_facecolor(box_color)
            patch.set_alpha(0.7)
        ax.set_ylabel(yname)
        ax.set_xlabel("Comparación" if not isinstance(xname, str) or not xname else xname)
        ax.set_title(title)
        paths = self._prepare_paths(title)
        meta = {"x": self._ensure_list(data), "labels": names, "xname": xname, "yname": yname, "color": colors}
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

    def cluster_plot(self, data, labels=None, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None, color=None, xname=None, yname=None, series_labels=None):
        df = self._dataset_to_dataframe(data)
        series = []

        if df is not None:
            numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
            target_col = "target" if "target" in df.columns else None
            feature_cols = [col for col in numeric_cols if col != target_col]
            if len(feature_cols) < 2:
                raise ValueError("El dataset necesita al menos dos columnas numéricas para cluster_plot.")
            x_col = xname if xname is not None else feature_cols[0]
            y_col = yname if yname is not None else feature_cols[1]
            coords = np.column_stack((self._get_column(df, x_col, 0), self._get_column(df, y_col, 1)))
            cluster_labels = np.asarray(labels if labels is not None else (df[target_col] if target_col else np.zeros(len(coords))))
            series.append({"data": coords, "labels": cluster_labels, "label": title})
        elif isinstance(data, dict):
            names = list(data.keys())
            label_values = list(labels.values()) if isinstance(labels, dict) else [None] * len(names)
            for name, values, lab in zip(names, data.values(), label_values):
                coords = np.asarray(values)
                if coords.ndim != 2 or coords.shape[1] < 2:
                    raise ValueError("Cada dataset de cluster_plot debe tener forma (n, 2) o más columnas.")
                series.append({"data": coords[:, :2], "labels": lab, "label": str(name)})
        else:
            data_list = list(data) if self._is_nested_sequence(data) else [data]
            first = np.asarray(data_list[0])
            if first.ndim == 1:
                data_list = [data]
            names = self._normalize_series_labels(series_labels, len(data_list))
            label_values = list(labels) if self._is_nested_sequence(labels) and len(labels) == len(data_list) else [labels] * len(data_list)
            for i, (values, lab) in enumerate(zip(data_list, label_values)):
                coords = np.asarray(values)
                if coords.ndim != 2 or coords.shape[1] < 2:
                    raise ValueError("El parámetro 'data' debe tener forma (n, 2), ser una lista de arrays (n, 2), un DataFrame o un dataset de sklearn.")
                series.append({"data": coords[:, :2], "labels": lab, "label": names[i]})

        colors = self._normalize_colors(color, len(series))
        fig, ax = plt.subplots(figsize=(14, 8))
        scatters = []
        for i, serie in enumerate(series):
            coords = np.asarray(serie["data"])
            lab = serie["labels"]
            if lab is not None and len(series) == 1 and color is None:
                scatter = ax.scatter(coords[:, 0], coords[:, 1], c=np.asarray(lab), cmap=cmap, label=serie["label"], s=42)
            else:
                scatter = ax.scatter(coords[:, 0], coords[:, 1], color=colors[i], label=serie["label"], s=42)
            scatters.append(scatter)
            if interactive:
                point_labels = [f"{serie['label']}: ({x:.3g}, {y:.3g})" for x, y in coords]
                plugins.connect(fig, plugins.PointLabelTooltip(scatter, labels=point_labels))

        ax.set_title(title)
        ax.set_xlabel(xname or "X")
        ax.set_ylabel(yname or "Y")
        if len(series) > 1:
            ax.legend(loc="best")
        if xlim: ax.set_xlim(xlim)
        if ylim: ax.set_ylim(ylim)

        paths = self._prepare_paths(title)
        meta = {
            "data": [self._ensure_list(s["data"]) for s in series],
            "labels": [self._ensure_list(s["labels"]) for s in series],
            "series_labels": [s["label"] for s in series],
            "cmap": cmap,
            "color": colors,
            "xname": xname,
            "yname": yname,
            "xlim": xlim,
            "ylim": ylim
        }

        return self._finalize_plot(fig,
            os.path.join(paths[0], paths[2]),
            os.path.join(paths[1], paths[3]),
            [], scatters, "cluster", interactive, title, meta)



    def rename_graph(self, old_title, new_title):
        safe_new_title = self._sanitize_title(new_title)
        safe_old_title = self._sanitize_title(old_title)

        with open(self.history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        updated = False
        stored_title = None

        for graph in history:
            if graph["title"] in (old_title, safe_old_title):
                stored_title = graph["title"]
                plot_type = graph.get("plot_type")
                interactive = graph.get("interactive", True)

                # Eliminar archivos anteriores usando el título tal como está en disco
                for ext in (".png", ".html"):
                    for folder in ("images", "html"):
                        path = os.path.join(
                            self.path, "static", folder, f"{stored_title}{ext}"
                        )
                        if os.path.exists(path):
                            try:
                                os.remove(path)
                            except OSError:
                                pass

                # Regenerar gráfico según tipo
                if plot_type == "line":
                    self.line_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        linewidth=graph.get("linewidth", 2),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"),
                        labels=graph.get("labels"))
                elif plot_type == "scatter":
                    self.scatter_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"),
                        labels=graph.get("labels"))
                elif plot_type == "bar":
                    self.bar_plot(graph["x"], graph["y"],
                        xname=graph.get("xname", "X"), yname=graph.get("yname", "Y"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"),
                        labels=graph.get("labels"))
                elif plot_type == "hist":
                    self.hist_plot(graph["x"],
                        xname=graph.get("xname", "Value"), yname=graph.get("yname", "Frequency"),
                        title=safe_new_title, bins=graph.get("bins", 20),
                        interactive=interactive, color=graph.get("color", "blue"),
                        xlim=graph.get("xlim"), ylim=graph.get("ylim"))
                elif plot_type == "box":
                    self.box_plot(graph["x"],
                        xname=graph.get("xname", ""), yname=graph.get("yname", "Value"),
                        title=safe_new_title, interactive=interactive,
                        color=graph.get("color"), labels=graph.get("labels"))
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
                        ylim=graph.get("ylim"),
                        color=graph.get("color"),
                        xname=graph.get("xname"),
                        yname=graph.get("yname"),
                        series_labels=graph.get("series_labels")
                    )
                else:
                    raise ValueError(f"Tipo de gráfico no soportado: {plot_type}")

                updated = True
                break

        if not updated:
            raise ValueError(f"Título no encontrado: {old_title}")

        # Eliminamos la entrada antigua del historial preservando el orden
        with open(self.history_file, "r", encoding="utf-8") as f:
            regenerated = json.load(f)

        cleaned = [g for g in regenerated if g["title"] != stored_title]

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f)



    def save_as_format(self, title, extension="png", target_folder=None):
        ext = extension.lower().lstrip(".")
        valid_exts = ["png", "jpg", "jpeg", "pdf"]

        if ext == "svg":
            raise ValueError("Formato SVG no soportado actualmente")
        if ext not in valid_exts:
            raise ValueError(f"Formato no soportado: {extension}")

        safe_title = self._sanitize_title(title)
        original_path = os.path.join(self.output_dir, "static", "images", f"{safe_title}.png")

        if not os.path.exists(original_path):
            raise FileNotFoundError(f"No se encontró el gráfico original: {original_path}")

        if target_folder is None:
            target_folder = os.path.join(self.output_dir, "exports")
        os.makedirs(target_folder, exist_ok=True)
        output_path = os.path.join(target_folder, f"{safe_title}.{ext}")

        if ext == "png":
            shutil.copyfile(original_path, output_path)
        else:
            with Image.open(original_path) as img:
                # JPG y PDF no soportan canal alfa → convertir a RGB.
                rgb = img.convert("RGB")
                if ext in ("jpg", "jpeg"):
                    rgb.save(output_path, "JPEG", quality=95)
                elif ext == "pdf":
                    rgb.save(output_path, "PDF", resolution=300.0)

        return output_path
