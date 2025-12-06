venv\Scripts\Activate.ps1
$env:FLASK_APP = "run.py"
$env:FLASK_ENV = "development"
flask run
