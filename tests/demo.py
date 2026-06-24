"""Demo interactivo de PyVmote.

Levanta el servidor en http://localhost:8000/ y cada 10 segundos genera
un gráfico distinto recorriendo TODOS los tipos soportados, alternando
interactivo / no interactivo. Sigue corriendo hasta que pulses Ctrl+C
o cierres la terminal (en ese momento el servidor se detiene y limpia
la sesión automáticamente).

Ejecución:
    python tests/demo.py
"""

import os
import time
import math
import random
import signal
import sys

import numpy as np
import pyvmote as pyv

PORT = 8000
INTERVAL = 10  # segundos entre gráficos
OUTPUT_DIR = os.path.join(os.getcwd(), "demo_outputs")


# ---------------------------------------------------------------------------
# Generadores: cada uno devuelve un callable sin argumentos que crea el plot.
# Se alternan interactive=True / False usando el índice global.
# ---------------------------------------------------------------------------
def _line(i, interactive):
    x = np.linspace(0, 4 * math.pi, 120)
    y1 = np.sin(x + i * 0.3)
    y2 = np.cos(x + i * 0.3)
    pyv.line_plot(
        x=[x.tolist(), x.tolist()],
        y=[y1.tolist(), y2.tolist()],
        color=["#2563eb", "#f97316"],
        labels=["sin", "cos"],
        title=f"line_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _scatter(i, interactive):
    n = 80
    x = np.random.normal(loc=i, scale=1.0, size=n)
    y = np.random.normal(loc=-i, scale=1.0, size=n)
    pyv.scatter_plot(
        x=x.tolist(), y=y.tolist(),
        color="#10b981",
        title=f"scatter_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _bar(i, interactive):
    cats = ["A", "B", "C", "D", "E"]
    vals_a = [random.randint(1, 20) for _ in cats]
    vals_b = [random.randint(1, 20) for _ in cats]
    pyv.bar_plot(
        x=[cats, cats],
        y=[vals_a, vals_b],
        color=["#6366f1", "#ef4444"],
        labels=["serie A", "serie B"],
        title=f"bar_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _hist(i, interactive):
    data = np.random.normal(loc=i, scale=2.0, size=500).tolist()
    pyv.hist_plot(
        x=data, bins=25, color="#8b5cf6",
        title=f"hist_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _box(i, interactive):
    data = [np.random.normal(loc=i + k, scale=1.0, size=100).tolist() for k in range(3)]
    pyv.box_plot(
        x=data, labels=["g1", "g2", "g3"],
        title=f"box_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _density(i, interactive):
    data = np.concatenate([
        np.random.normal(loc=i, scale=1.0, size=200),
        np.random.normal(loc=i + 4, scale=0.8, size=200),
    ]).tolist()
    pyv.density_plot(
        x=data, color="#0ea5e9",
        title=f"density_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _pie(i, interactive):
    sizes = [random.randint(5, 30) for _ in range(4)]
    pyv.pie_plot(
        sizes=sizes,
        labels=["uno", "dos", "tres", "cuatro"],
        title=f"pie_{'int' if interactive else 'img'}_{i:02d}",
        interactive=interactive,
    )


def _cluster(i, interactive):
    try:
        from sklearn.datasets import make_blobs
        data, labels = make_blobs(
            n_samples=150, centers=3, n_features=2,
            random_state=i, cluster_std=1.0,
        )
        pyv.cluster_plot(
            data=data, labels=labels,
            title=f"cluster_{'int' if interactive else 'img'}_{i:02d}",
            interactive=interactive,
            cmap="viridis",
        )
    except Exception as exc:
        print(f"[demo] cluster_plot omitido: {exc}")


PLOTTERS = [_line, _scatter, _bar, _hist, _box, _density, _pie, _cluster]


def _shutdown(*_):
    print("\n[demo] señal recibida → parando servidor...")
    try:
        pyv.stop_server()
    finally:
        sys.exit(0)


def main():
    pyv.configure(output_dir=OUTPUT_DIR)
    print(f"[demo] output_dir = {OUTPUT_DIR}")
    pyv.start_server(PORT)
    print(f"[demo] abre http://localhost:{PORT}/  (Ctrl+C para salir)")

    # Ctrl+C → limpieza explícita (atexit también la haría).
    signal.signal(signal.SIGINT, _shutdown)
    try:
        signal.signal(signal.SIGTERM, _shutdown)
    except (ValueError, OSError):
        pass

    i = 0
    while True:
        plotter = PLOTTERS[i % len(PLOTTERS)]
        # Alternamos interactivo/no interactivo cada vuelta completa.
        interactive = (i // len(PLOTTERS)) % 2 == 0
        try:
            print(f"[demo] #{i:02d}  {plotter.__name__}  interactive={interactive}")
            plotter(i, interactive)
        except Exception as exc:
            print(f"[demo] error en {plotter.__name__}: {exc}")
        i += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
