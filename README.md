This is the future home of the Kvasir Hardware Description File Generator.

# Running the generator
This library depends on the kvasir::chip repository for it's svd files. This is included in this library as a submodule. To fetch the repo execute the following in your gitshell:

```
git submodule init
git submodule update
```

You also need to install Python and two dependencies: Beautiful Soup and EmPy.

```
pip install bs4 empy lxml
python2 setup.py install
mkdir build
cd build
cmake .. -DBUILD_TESTING=1
```

# Selecting specific boards

CMake will look for a directory defined in the CmakeLists.txt for the svd files.

However, this introduces a *lot* of build targets for this generator. To narrow down which board to generate headers for, you can specify two kinds of regexes to CMake.

For example, `cmake .. -DVENDORS="Atmel"` will only generate headers for Atmel boards. (Actually, it will only generate headers for svd files under the directory called "data/Atmel".)

`cmake .. -DBOARDS="STM32F7*"` will build all STM32F7-family boards. (Actually, it will search the "data" directory for any svd files starting with the token `STM32F7`.)
