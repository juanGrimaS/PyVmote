# 📊 PyVmote

**PyVmote** es una librería de Python para la **generación y visualización remota de gráficos**, estáticos o interactivos, sobre un servidor FastAPI integrado. Permite ver gráficas en el navegador incluso cuando trabajas vía SSH gracias a su sistema de WebSocket en tiempo real.

> Versión actual: **1.1.1**

---

## 🚀 Características

- Tipos de gráfico: line, scatter, bar, hist, box, density (KDE), pie, cluster.
- Servidor web integrado con FastAPI.
- Recarga automática vía WebSocket.
- Gráficos interactivos con `mpld3` (`interactive=True`).
- Exportación a `png`, `jpg`/`jpeg`, `pdf` mediante Pillow.
- Historial automático y vista *preview* en el navegador.
- Compatible con `pandas.DataFrame` y datasets tipo `sklearn.datasets.load_*()`.

---

## 📦 Instalación

```bash
pip install pyvmote
```

Las dependencias (FastAPI, uvicorn, matplotlib, mpld3, pandas, scikit-learn, **Pillow**, ...) se instalan automáticamente.

---

## 🧭 Arquitectura: fachada limpia

A partir de la 1.1.1 PyVmote expone una **fachada** real a nivel de módulo. Ya **no** se reemplaza `sys.modules` con una instancia, por lo que el autocompletado y los linters funcionan correctamente.

```python
import pyvmote as pyv
```

Internamente se crea una única instancia privada de `Pyvmote()` y sus métodos se exponen como funciones del módulo (`pyv.line_plot`, `pyv.start_server`, etc.).

---

## 📁 Directorio de salida

Por defecto PyVmote escribe imágenes, páginas HTML interactivas e historial en:

```
~/.pyvmote/
    static/
        images/
        html/
        graph_history.json
    exports/
```
Puedes cambiarlo con `configure(...)` antes de iniciar el servidor:

```python
import pyvmote as pyv
pyv.configure(output_dir="/tmp/mis_graficos")
pyv.start_server(8000)
```

O instanciando directamente la clase:

```python
from pyvmote import Pyvmote
app = Pyvmote(output_dir="/tmp/mis_graficos")
```

---

## Flujo de trabajo
### Importacion
Pyvmote funciona como una clase fachada que te permite usar todas las funciones a tarves de un objeto. 
```
import pyvmote as pyv
```

### Iniciar servidor
podras elegir en que puerto se inicia el servidor
```
start_server(puerto)
```

### Creacion de Gráficos
Una vez que hayas iniciado el servidor podras ir a tu browser de confianza y empezar a ver graficos mientras los generes en tu http://localhost:port/
Los graficos se hacen con soporte de matplotlib por lo cual todos los parametros de los graficos presentes en esta libreria funcionan con los mismos parametros de matplotlib.

En cada grafico generado de aqui puede definir con un parametro que interative = True -> (Gráfico interactivo) o interactive = False -> (Imagen).

- Line plots ⇒ **x** e **y** aceptan listas simples, listas de listas, diccionarios, DataFrames o datasets de sklearn. Usa `color=[...]` para dar un color distinto a cada serie.

  ```
  pyv.line_plot(
      x=[[1, 2, 3, 4], [2, 5, 6, 7, 8]],
      y=[[4, 3, 2, 1], [1, 4, 7, 8, 9]],
      color=["red", "green"],
      labels=["grupo A", "grupo B"],
      title="comparación"
  )
  ```

- Scatter plots ⇒ mismas entradas comparativas que line_plot
  ```
  pyv.scatter_plot(x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color=['blue', 'orange'], xlim=None, ylim=None, labels=None)
  ```

- Bar Plots ⇒ permite barras agrupadas para comparar varias series
  ```
  pyv.bar_plot(x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color=['blue', 'orange'], xlim=None, ylim=None, labels=None)
  ```

- Historigram ⇒ **x** puede ser una lista y puede ser un dataframe de pandas
  ```
  pyv.hist_plot(x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
  ```

- Box plot ⇒ acepta una lista, listas de listas, DataFrame o dataset de sklearn para comparar distribuciones
  ```
  pyv.box_plot(x, xname="", yname="Value", title="Box Plot", interactive=True, color=None, labels=None)
  ```

- Density plots **(KDE)** ⇒ **x** puede ser una lista y puede ser un dataframe de pandas
  ```
  pyv.density_plot(x, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None)
  ```

- Pie Graph ⇒ **sizes** es una lista de porcentages que sumen 100% y **labels** es una lista de titulos para cada uno de klos trozos de tarta
  ```
  pyv.pie_plot(sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
  ```

- cluster plot ⇒ **data** puede ser una matriz de puntos 2D, varias matrices, un DataFrame o un dataset de sklearn. `labels` es opcional si el dataset trae `target`.
  ```
  from sklearn.datasets import make_blobs, load_iris

  data, labels = make_blobs(n_samples=100, centers=3, n_features=2)
  pyv.cluster_plot(data, labels, title="Cluster Plot", interactive=True, cmap='viridis')

  iris = load_iris()
  pyv.scatter_plot(iris, xname="sepal length (cm)", yname=["sepal width (cm)", "petal length (cm)"], color=["red", "green"])
  pyv.box_plot(iris, xname=["sepal length (cm)", "petal length (cm)"], color=["red", "green"])
  pyv.cluster_plot(iris, title="Iris clusters")
  ```

Todos aceptan `interactive=True|False`.

### Exportación de formatos

```python
pyv.export_graph("titulo", extension="png")   # copia directa
pyv.export_graph("titulo", extension="jpg")   # convierte a RGB y guarda JPEG
pyv.export_graph("titulo", extension="pdf")   # convierte a RGB y guarda PDF 
# ❌ ValueError: SVG no soportado
```

---

## ⛔ Detener el servidor

```python
pyv.stop_server()
```

> ⚠️ **Aviso:** al detenerse el servidor se hace una **limpieza automática** de la sesión: se vacían las carpetas `static/images/` y `static/html/` y se reinicia `graph_history.json` dentro del `output_dir` configurado. Si quieres conservar algún gráfico, expórtalo con `pyv.export_graph(...)` antes de parar el servidor.

Esta limpieza también se ejecuta de forma automática al terminar el proceso (vía `atexit` y los handlers de `SIGINT`/`SIGTERM`).

---

## 🧪 Tests

```bash
pip install -e ".[test]"
pytest
```

Los tests verifican que la fachada expone la API correcta, que `configure(output_dir=...)` aísla cada sesión y que la exportación de formatos se comporta según lo prometido (incluido el `ValueError` para SVG).
