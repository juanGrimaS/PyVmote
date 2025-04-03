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
  - Curvas de densidad (KDE)

- 🌐 Servidor web integrado con FastAPI
- ⚡ Recarga automática de gráficos mediante WebSocket
- 🌍 Visualización remota con un simple túnel SSH
- 🖱️ Soporte para gráficos **interactivos** con `mpld3`
- 📸 Exportación de gráficos a formatos `png`, `jpg`, `svg`, `pdf`, etc.
- 🧠 Historial de gráficos generado automáticamente

---

## 🚀 Fujo de trabajo
- import Pyvmote as p
- p.start_server(port) port exameple 3000
- p.line_plot(), p.scatter_plot(), p.box_plot(), p.bar_plot(), p.hist_plot(), p.density_plot() this will generate the graphs in the web server
- p.export_graph(title, extension, target_folder) title is also the name of the file image, extension = ["png", "jpg", "jpeg", "svg", "pdf"], target_folder = where do you want to save the photo
- p.stop_server()
