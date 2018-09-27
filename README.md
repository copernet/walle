## walle
Modify rpc password in 'conf/coperctl.conf'.

## quick start

Install dependencies

you should install python3 first

On MacOS
```
brew install python3
```

We use **pipenv** to manage source code and environment
```
pip3 install pipenv
```

Download code and create virtual environment
```
$ git clone git@github.com:copernet/walle.git
$ cd walle
$ mkdir .venv
$ pipenv --python 3.7
# pipenv install 
```

Run test case
```
pipenv run python abc-rpc.py
```

