# Catman AP Reader
> Read binary files produced from catmanAP projects directly into python.

CatmanAP procudes .bin files after each measurement. While it is possible to export as a different format (i.e. txt or asc) it's not efficient because one has to change the export format after every measurement. Here comes the treat: Just export as binary and use this package to work with binary files directly.

## Installation

Anywhere with python:

```sh
pip install apreader
```


## Usage example

Lets say you produced a file called `measurements.bin` and you put it in the directory of your python script.

```python
from apreader import APReader

reader = APReader('measurements.bin')
``` 
It's that simple.



## Release History

* Version 1.0.0
    * Convert catman files

## Meta

Leon Bohmann – leon.bohmann@mepla.net

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/leonbohmann/apreader](https://github.com/leonbohmann/apreader)