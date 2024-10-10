# nowpy - Run Any Python File Instantly

**nowpy** combines `python`, `venv`, and `pip` to launch a dedicated isolated environment, automatically figure out which packages are required, and then run your Python file - all with just **one** command. 

**nowpy** finds packages by performing a recursive lookup for a `requirements.txt` or a Poetry-flavoured `pyproject.toml`, and cross-checks with any `import` statements inside the Python file. 

[!NOTE] 
**nowpy** won't find a packages if its `import xyz` name is different to that on PyPI. 

## Installation

Install **nowpy** with `pip` or `pipx`. If you only really run scripts, this might be the last time you ever have to `pip install` anything...

```sh
pip install nowpy
# Even better
pipx install nowpy
```

## Usage

Here's an example of what happens if you run **nowpy** on a Python file that imports `requests`. 

First run:

```sh
nowpy WorldTimeApi.py

Creating venv...
Collecting requests
...
Installing collected packages: urllib3, idna, charset-normalizer, certifi, requests
Successfully installed certifi-2023.11.17 charset-normalizer-3.3.2 idna-3.6 requests-2.31.0 urllib3-2.2.0
Running Script...

Current Time in Europe/London
Date: 2024-01-30T22:08:52.854140+00:00
Timezone: Europe/London
```

All future runs:

```sh
nowpy WorldTimeApi.py

Running Script...

Current Time in Europe/London
Date: 2024-01-30T22:08:52.854140+00:00
Timezone: Europe/London
```

**nowpy** creates a unique virtual environment for every directory you run `nowpy` from. It also removes unused ones automatically. But if you ever want to reset the virtual environment in a directory that you're using, just use the `--reset` option:

```sh
nowpy --reset
```

That's all!

## Roadmap

- Stop **nowpy** from trying to treat "batteries included" imports (e.g. `import os`) as packages to be imported from PyPI. 
- Enable **nowpy** to find packages required by generic `pyproject.toml` files, not just "Poetry-flavoured" ones. 
- Allow **nowpy** to trace local imports.
- Make the venv clean operation simpler

## Contributing

Pull requests are welcome.

## License

Made and released under the [MIT](https://choosealicense.com/licenses/mit/) license.
