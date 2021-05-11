@echo off
echo Removing egg
rmdir /Q /S apread.egg-info
echo Removing dist
rmdir /Q /S dist
echo Removing build
rmdir /Q /S build
python setup.py sdist bdist_wheel