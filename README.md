For add-on description, please see [AnkiWeb page](https://ankiweb.net/shared/info/1928346827)

# Development

## Setup

After cloning the project, run the following command to install [ankiaddonconfig](https://github.com/BlueGreenMagick/ankiaddonconfig/) as a git submodule.

```
git submodule update --init --recursive
```

## Tests & Formatting

This project uses [black], [mypy](https://github.com/python/mypy), and [pytest].

```shell
black .
mypy .
# pytest . (pytest no longer works)
```

You will need to install the following python packages to run black, mypy and pytest:

```
pip install aqt pyqt5-stubs mypy black pytest
```

# Building ankiaddon file

After cloning the repo, go into the repo directory and run the following command to install the git submodule [ankiaddonconfig](https://github.com/BlueGreenMagick/ankiaddonconfig/)

```
git submodule update --init addon/ankiaddonconfig
```

After installing the git submodule, run the following command to create an `review_hotmouse.ankiaddon` file

```
cd addon ; zip -r ../review_hotmouse.ankiaddon * ; cd ../
```
