from os import getenv

from dotenv import load_dotenv

load_dotenv()

METAMORPH_DATABASE_NAME = getenv("METAMORPH_DATABASE_NAME")
METAMORPH_DATABASE_HOST = getenv("METAMORPH_DATABASE_HOST")
METAMORPH_DATABASE_PORT = getenv("METAMORPH_DATABASE_PORT")
METAMORPH_DATABASE_USER = getenv("METAMORPH_DATABASE_USER")
METAMORPH_DATABASE_PASSWORD = getenv("METAMORPH_DATABASE_PASSWORD")
