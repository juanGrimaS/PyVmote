from setuptools import setup, find_packages

setup(
    name="Pyvmote",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "jinja2",
        "matplotlib",
        "mpld3",
        "scipy",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "pyvmote=Pyvmote.pyvmote:main",
        ]
    },
    author="Juan Grima Sanchez",
    author_email="juan.grimasanchez5@gmail.com",
    description="Librería para generar gráficos y visualizar imágenes en tiempo real en remoto",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
