import os
import sys
import traceback
from datetime import datetime

from schemas.email import AlertEmailTemplate

environment = os.environ["APP_SETTINGS"].replace("config.", "").replace("Config", "").lower()


def get_object() -> AlertEmailTemplate:
    """Get alert object

    Must only be called from inside an exception handler.

    :returns: An AlertEmailTemplate object
    """
    err_info: tuple = sys.exc_info()
    err_module: str = err_info[0].__module__
    err_name: str = err_info[0].__name__
    err_type: str = err_name if err_module == "__main__" else f"{err_module}.{err_name}"
    err_file = os.path.split(err_info[2].tb_frame.f_code.co_filename)[1]
    err_line = err_info[2].tb_lineno
    err_message: str = str(sys.exc_info()[1])
    return AlertEmailTemplate(
        err_type=err_type,
        err_message=err_message,
        err_location=f"{err_file}:{err_line}",
        err_time=str(datetime.now()),
        stacktrace=traceback.format_exc(),
        environment=environment
    )
