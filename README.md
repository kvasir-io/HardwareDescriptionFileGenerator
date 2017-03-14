This is the future home of the Kvasir Hardware Description File Generator.

# Running the generator
You need to install Python and two dependencies: Beautiful Soup and EmPy.

```
pip install bs4 empy lxml
python2 setup.py install
mkdir build
cd build
cmake .. -DBUILD_TESTING=1
```

# Selecting specific boards

By default, CMake will look for a directory called "data" and then generate headers for all ".svd" files in the subtree rooted at "data".

We don't clone svd files into the repository yet, so this will do nothing if you don't provide SVD files. You can clone Peter Osborne's [cmsis_svd](github.com/posborne/cmsis-svd) repository and symlink the "data" directory into this repository.

However, this introduces a *lot* of build targets for this generator. To narrow down which board to generate headers for, you can specify two kinds of regexes to CMake.

For example, `cmake .. -DVENDORS="Atmel"` will only generate headers for Atmel boards. (Actually, it will only generate headers for svd files under the directory called "data/Atmel".)

`cmake .. -DBOARDS="STM32F7*"` will build all STM32F7-family boards. (Actually, it will search the "data" directory for any svd files starting with the token `STM32F7`.)
