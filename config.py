import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


DATABASE_NAME  = 'fyyur'
username = 'postgres'
password = 'postgres'
url = 'localhost:5432'
SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}/{}'.format(username,password, url, DATABASE_NAME)

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
