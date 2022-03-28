import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    token: str = os.environ['TOKEN']
    mongo_url: str = os.environ['MONGO_URL']