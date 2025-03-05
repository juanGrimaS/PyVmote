from .pyvmote import Pyvmote

__version__ = "0.1.0"

# Creamos una instancia de Pyvmote para que al importar el paquete se obtenga directamente el objeto
_instance = Pyvmote()
import sys
sys.modules[__name__] = _instance
