"""PyVmote: fachada de alto nivel.

Uso típico:
    import pyvmote as pyv
    pyv.configure(output_dir="/ruta/personalizada")  # opcional
    pyv.start_server(8000)
    pyv.line_plot([1, 2, 3], [4, 5, 6], title="demo")
"""

from .core import Pyvmote

__version__ = "1.1.1"

# Instancia privada única. NO se reemplaza sys.modules — los linters y el
# autocompletado siguen viendo este módulo como un módulo normal.
_instance = Pyvmote()


def configure(output_dir=None):
    """Cambia en caliente el directorio de salida usado por la fachada."""
    return _instance.configure(output_dir=output_dir)


# Lista pública de métodos que se exponen como funciones a nivel de módulo.
_PUBLIC_METHODS = (
    "start_server",
    "stop_server",
    "line_plot",
    "scatter_plot",
    "bar_plot",
    "hist_plot",
    "box_plot",
    "density_plot",
    "pie_plot",
    "cluster_plot",
    "export_graph",
    "rename_graph",
)

# Clonamos los métodos de la instancia privada como atributos del módulo.
for _name in _PUBLIC_METHODS:
    globals()[_name] = getattr(_instance, _name)

__all__ = ("Pyvmote", "configure", "__version__", *_PUBLIC_METHODS)
