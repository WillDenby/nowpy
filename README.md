# nowpy - Run Any Python File Instantly

![nowpyDemo](https://files.datasesa.me/nowpyDemo.gif)

**nowpy** combines ```python```, ```virtualenv```, and ```pip``` to launch a dedicated isolated environment, automatically figure out which packages are required, and then run your Python file - all with just **one** command. 

**nowpy** finds packages by performing a recursive lookup for a ```pyproject.toml``` OR a ```requirements.txt```, and cross-checks with any ```import``` statements inside the Python file. 

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install **nowpy**.

```bash
pip install nowpy
```

It might be the last time you have to ```pip install``` anything!

## Usage

Here's an example of what happens if you run **nowpy** on a Python file that imports ```requsts```. 

First run:

```bash
nowpy WorldTimeApi.py

Creating Virtualenv...
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

```bash
nowpy WorldTimeApi.py

Running Script...

Current Time in Europe/London
Date: 2024-01-30T22:08:52.854140+00:00
Timezone: Europe/London
```

**nowpy** creates a unique virtual environment for every directory you run ```nowpy``` from. It also removes unused ones automatically. But if you ever want to reset a particular one that you're using, just use the ```--reset``` option:

```bash
nowpy --reset
```

That's all!

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

Made and released by Will Denby under the [MIT](https://choosealicense.com/licenses/mit/) license