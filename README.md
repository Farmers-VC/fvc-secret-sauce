# fvc-secret-sauce

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

cp .envrc.default .envrc
direnv allow