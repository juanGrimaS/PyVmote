"""Tests de la fachada PyVmote.

Verifican:
  * la API pública expuesta a nivel de módulo,
  * que `configure(output_dir=...)` aísla la salida,
  * que los gráficos se materializan dentro del directorio configurado,
  * que `export_graph` soporta png/jpg/pdf y rechaza svg con ValueError.
"""

import os
import importlib

import pytest


@pytest.fixture
def pyv(tmp_path, monkeypatch):
    # Re-importamos en limpio para no arrastrar estado de otras suites.
    if "pyvmote" in list(importlib.sys.modules):
        del importlib.sys.modules["pyvmote"]
    mod = importlib.import_module("pyvmote")
    mod.configure(output_dir=str(tmp_path))
    yield mod


def test_public_api_exposed(pyv):
    expected = {
        "configure", "start_server", "stop_server",
        "line_plot", "scatter_plot", "bar_plot", "hist_plot",
        "box_plot", "density_plot", "pie_plot", "cluster_plot",
        "export_graph", "rename_graph", "__version__",
    }
    missing = expected - set(dir(pyv))
    assert not missing, f"Faltan en la fachada: {missing}"
    assert pyv.__version__ == "1.1.1"


def test_module_is_a_real_module(pyv):
    import types
    assert isinstance(pyv, types.ModuleType), \
        "pyvmote ya no debe sustituir sys.modules por una instancia"


def test_configure_isolates_output(tmp_path, pyv):
    target = tmp_path / "salida_personalizada"
    pyv.configure(output_dir=str(target))
    pyv.line_plot([1, 2, 3], [4, 5, 6], title="grafico_test", interactive=False)
    png = target / "static" / "images" / "grafico_test.png"
    history = target / "static" / "graph_history.json"
    assert png.exists(), f"No se generó el PNG en {png}"
    assert history.exists(), f"No se creó el historial en {history}"


def test_export_graph_formats(tmp_path, pyv):
    pyv.configure(output_dir=str(tmp_path))
    pyv.line_plot([1, 2, 3], [4, 5, 6], title="export_test", interactive=False)

    for ext in ("png", "jpg", "pdf"):
        out = pyv.export_graph("export_test", extension=ext)
        assert os.path.exists(out)
        assert out.lower().endswith("." + ext)


def test_export_graph_svg_raises(tmp_path, pyv):
    pyv.configure(output_dir=str(tmp_path))
    pyv.line_plot([1, 2, 3], [4, 5, 6], title="svg_test", interactive=False)
    with pytest.raises(ValueError, match="SVG"):
        pyv.export_graph("svg_test", extension="svg")


def test_server_and_graph_share_instance(pyv):
    # La fachada usa una sola Graph para core y Server.
    from pyvmote.core import Pyvmote
    instance = Pyvmote()
    assert instance.sv.graph is instance.gr
    assert instance.sv.output_dir == instance.gr.output_dir
