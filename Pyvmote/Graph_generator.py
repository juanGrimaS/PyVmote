import matplotlib.pyplot as plt
import os

"""
Clase que se encarga de la generación de imagenes a partir de graficos
"""
class Graph:

    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.n_plot = 0


    def plot(self, x, y, xname="X", yname="Y", title="graph"):

        images_dir = os.path.join(self.path, "static", "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        # Creamos el plot y lo configuramos
        plt.plot(x, y, marker='o', linestyle='-')

        plt.xlabel(xname)
        plt.ylabel(yname)
        plt.title(title)

        # Configuración y creación de la imagen del plot en la ruta preseleccionada
        image_name = "grafico" + str(self.n_plot) + ".png"
        self.n_plot += 1
        ruta_archivo = os.path.join(images_dir , image_name)
        print(ruta_archivo)

        # Guardar la imagen
        plt.savefig(ruta_archivo, dpi=300, bbox_inches='tight')

        # Cerrar el gráfico para liberar memoria
        plt.close()

        print("Grafico Creado con exito")