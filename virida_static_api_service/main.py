import os
import uvicorn

from api.api import app
from config import import_class
config = import_class(os.environ['APP_SETTINGS'])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.INTERNAL_PORT)
