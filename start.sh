#!/bin/bash
cd Green_Burn
python manage.py collectstatic --noinput
gunicorn Green_Burn.wsgi