from setuptools import setup, find_packages

setup(
    name="speedy",
    version="0.1.0",
    description="Fast and easy-to-use package for data science",
    author="AnhVTH",
    author_email="anhvth.226@gmail.com",
    url="https://github.com/anhvth/speedy",
    packages=find_packages(),  # Automatically find all packages in the directory
    install_requires=[  # List any dependencies your package requires
        "numpy",
        "requests",
        "xxhash",
        "loguru",
        "fastcore",
        "debugpy",
        "ipywidgets",
        "jupyterlab",
        "ipdb",
        "scikit-learn",
        "matplotlib",
        "pandas",
        "tabulate",
    ],
)
