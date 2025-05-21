# 📊 PyVmote

**PyVmote** es una librería de Python para la **generación y visualización remota de gráficos**, tanto estáticos como interactivos, usando un servidor FastAPI. Permite visualizar gráficas directamente desde tu navegador incluso cuando trabajas en un entorno remoto (como SSH), gracias a su sistema de forwarding de puertos y WebSocket en tiempo real.

---

## 🚀 Características principales

- 📈 Soporte para múltiples tipos de gráficos:
  - Line plot
  - Scatter plot
  - Bar plot
  - Histogram
  - Boxplot
  - Density plot (KDE)
  - Clusters
  - Pie Graphs

- 🌐 Servidor web integrado con FastAPI
- ⚡ Recarga automática de gráficos mediante WebSocket
- 🌍 Visualización remota con un simple túnel SSH
- 🖱️ Soporte para gráficos **interactivos** con `mpld3`
- 📸 Exportación de gráficos a formatos `png`, `jpg`, `svg`, `pdf`, etc.
- 🧠 Historial de gráficos generado automáticamente

---

## Instalacion
para instalar la libreria simplemente cree un entorno de desarrollo con python y venv he instale la libreria usando pip
```
pip install pyvmote
```

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

- Line plots ⇒ **x** e **y** son listas de numeros y **x** puede ser un dataframe de pandas
  ```
  pyv.line_plot(x, y=None, xname="X", yname="Y", title="Line Graph", interactive=True, color='blue', linewidth=2, xlim=None, ylim=None)
  ```

- Scatter plots ⇒ **x** e **y** son listas de numeros y **x** puede ser un dataframe de pandas
  ```
  pyv.scatter_plot(x, y=None, xname="X", yname="Y", title="Scatter Plot", interactive=True, color='blue', xlim=None, ylim=None)
  ```

- Bar Plots ⇒ **x** e **y** son listas de numeros y **x** puede ser un dataframe de pandas
  ```
  pyv.bar_plot(x, y=None, xname="X", yname="Y", title="Bar Plot", interactive=True, color='blue', xlim=None, ylim=None):
  ```

- Historigram ⇒ **x** puede ser una lista y puede ser un dataframe de pandas
  ```
  pyv.hist_plot(x, xname="Value", yname="Frequency", title="Histogram", bins=20, interactive=True, color='blue', xlim=None, ylim=None):
  ```

- Box plot ⇒ **x** puede ser una lista y puede ser un dataframe de pandas
  ```
  pyv.box_plot(x, xname="", yname="Value", title="Box Plot", interactive=True):
  ```

- Density plots **(KDE)** ⇒ **x** puede ser una lista y puede ser un dataframe de pandas
  ```
  pyv.density_plot(x, xname="X", yname="Density", title="Density Plot", interactive=True, color='blue', xlim=None, ylim=None)
  ```

- Pie Graph ⇒ **sizes** es una lista de porcentages que sumen 100% y **labels** es una lista de titulos para cada uno de klos trozos de tarta
  ```
  pyv.pie_plot(sizes, labels=None, title="Pie Chart", interactive=True, colors=None):
  ```

- cluster plot ⇒ **data** es una lista de puntos 2D y **labels** es una lista de numeros que marcan de que punto es cada cluster
  ```
  import numpy as np
  from sklearn.datasets import make_blobs
  data, labels = make_blobs(n_samples=100, centers=3, n_features=2)
  pyv.cluster_plot(self, data, labels, title="Cluster Plot", interactive=True, cmap='viridis', xlim=None, ylim=None):
  ```

## Descargar Gráficos
Puedes descargar los graficos en formato png desde la pestaña preview o con el formato que quieras usando. El parametro title se refiere al titulo del grafico
```
plt.export_graph(self, title, extension="jpg", target_folder="exports")
```

## Cerrar Servidor
Esto se hace de forma automatica cuandos se acaba el programa o cierras la linea de comandos pero si quieres hacerlo antes
```
pyv.stop_server()
```
⚠️ **Warning:** Esto no solo cerrara el servidor sino tambien borrara todas las imagenes creadas y todo el historial, por ello si quieres conservar alguna imagen recuerda descargarla en la pestaña preview