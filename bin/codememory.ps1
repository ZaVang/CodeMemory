$env:PYTHONPATH = "$PSScriptRoot\..\src;$env:PYTHONPATH"
python -m codememory.cli @args
