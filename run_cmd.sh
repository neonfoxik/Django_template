#!/bin/bash

ssh localhost -p222
cd ~/avito_reports/Django_template
source venv/bin/activate
python3 manage.py $@