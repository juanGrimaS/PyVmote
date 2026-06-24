from setuptools import setup, find_packages

setup(
    name="pyvmote",
    version="1.1.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "jinja2",
        "matplotlib",
        "mpld3",
        "scipy",
        "numpy",
        "pandas",
        "scikit-learn",
        "pillow>=10.0.0",
    ],
    extras_require={"test": ["pytest>=7.0"]},
    author="Juan Grima Sanchez",
    author_email="juan.grimasanchez5@gmail.com",
    description="Librería para generar gráficos y visualizar imágenes en tiempo real en remoto",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
