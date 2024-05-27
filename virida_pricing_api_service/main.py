import uvicorn

from api.api import app
import core.weights as weights
from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])

if __name__ == "__main__":
    weights.load()
    uvicorn.run(app, host="0.0.0.0", port=config.INTERNAL_PORT)
