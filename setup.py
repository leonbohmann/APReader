import pathlib
from setuptools import setup
import setuptools



# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="apread",
    version="1.0.21",
    description="Import data from CatmanAP binary files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/leonbohmann/apreader",
    author="Leon Bohmann",
    author_email="info@leonbohmann.de",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    packages=['apread'],
    install_requires=['matplotlib', 'plotly', 'scipy', 'typing', 'tqdm', 'pandas'],
    include_package_data=True,
)