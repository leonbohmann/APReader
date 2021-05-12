@echo off
echo Removing egg
rmdir /Q /S apread.egg-info
echo Removing dist
rmdir /Q /S dist
echo Removing build
rmdir /Q /S build
python setup.py sdist bdist_wheel


pdoc --html --output-dir docs apread --force
xcopy /e /k /h /i /q /s /y .\docs\apread .\docs
rmdir .\docs\apread /Q /S
