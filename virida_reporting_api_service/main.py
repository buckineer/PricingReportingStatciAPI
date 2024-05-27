import os
import uvicorn

from api.api import app
from config import config

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.INTERNAL_PORT)