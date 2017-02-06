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

