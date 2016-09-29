#!/bin/bash

sudo sphinx-apidoc -f -o source/ ../pygraphc
sudo make clean
sudo make html
