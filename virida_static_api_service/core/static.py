API_RESPONSE_ERROR_CODE_STRING = "error_code"
API_RESPONSE_ERROR_MESSAGE_STRING = "error_message"

LIMITED_ACCESS = 20006

DEFAULT_MAPPING_VERSION = 3

# error strings
ERROR_STRINGS = {
    LIMITED_ACCESS: "No permission to the endpoint"
}


def get_error_string_by_error_code(error_code: int) -> str:
    """
    return error string by error code
    """
    return ERROR_STRINGS[error_code]
