@echo off
set DB_NAME=dof_db_dev
python -m waitress --listen=0.0.0.0:5000 wsgi:app