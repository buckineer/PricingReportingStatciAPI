import os
import datetime as dt
from config import import_class
config = import_class(os.environ['APP_SETTINGS'])


MONTH_CODES_TO_NUMBERS = {
    "F": 1,
    "G": 2,
    "H": 3,
    "J": 4,
    "K": 5,
    "M": 6,
    "N": 7,
    "Q": 8,
    "U": 9,
    "V": 10,
    "X": 11,
    "Z": 12
}

MONTH_NUMBERS_TO_CODES = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z"
}

VINTAGE_DISCOUNT_FACTORS = {
    "2030": 1.0,
    "2029": 1.0,
    "2028": 1.0,
    "2027": 1.0,
    "2026": 1.0,
    "2025": 1.0,
    "2024": 1.0,
    "2023": 1.0,
    "2022": 1.0,
    "2021": 1.0,
    "2020": 0.93057946,
    "2019": 0.86115891,
    "2018": 0.79173837,
    "2017": 0.72231783,
    "2016": 0.65289729,
    "2015": 0.58347674,
    "2014": 0.5140562,
    "2013": 0.44463566,
    "2012": 0.37521512
}

VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS_LEGACY = {
    1: -0.07667456785799787,
    2: -0.037531686747401,
    3: -0.07684374043992846,
    4: -0.07667456785799787
}

VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS = {
    'afolu': -0.037531686747401,
    'eefs': -0.07667456785799787,
    'ga': -0.07684374043992846,
    're': -0.07667456785799787
}

INDEX_REFERENCE_DATE = dt.datetime(2019, 12, 30)
INDEX_HISTORY_REFERENCE_DATE = dt.datetime(2020, 1, 1)
FILL_FORWARD_LOOKBACK = 30
CO2_INDEX_LOOKBACK = 365

CORSIA_MIN_YEAR = 2016

EUA_SPOT_REFERENCE_USD = 31.33  # Q4 2020 spot EUA (EUR) x fx to convert in USD
SCALING_STD = 1.0
SCALING_INTERCEPT = 0.5

BIDASK_SIGMA_PCT = 0.15
BIDASK_SPREAD = 0.2
BIDASK_ADDON_SPREAD = 0.005

API_RESPONSE_ERROR_CODE_STRING = "error_code"
API_RESPONSE_ERROR_MESSAGE_STRING = "error_message"

OPERATION_SUCCESS_STATUS = "OK"

# error code
USER_LIMIT_ALREADY_EXIST = 20000
ORGANIZATION_LIMIT_ALREADY_EXIST = 20001
USERNAME_REQUIRED = 20002
ORGANIZATION_REQUIRED = 20003
USER_LIMIT_NOT_EXIST = 20004
ORGANIZATION_LIMIT_NOT_EXIST = 20005
LIMITED_ACCESS = 20006
LIMITED_DELETED = 20007

USER_SUBSCRIPTION_NOT_EXIST = 21000
ORGANIZATION_SUBSCRIPTION_NOT_EXIST = 21001

USER_DAILY_LIMIT_EXCEED = 21010
USER_MONTHLY_LIMIT_EXCEED = 21011
USER_LIFETIME_LIMIT_EXCEED = 21012
ORGANIZATION_DAILY_LIMIT_EXCEED = 21013
ORGANIZATION_MONTHLY_LIMIT_EXCEED = 21014
ORGANIZATION_LIFETIME_LIMIT_EXCEED = 21015

INSTRUMENT_DB_CREATE_ERROR = 22000
INSTRUMENT_KEY_CONFLICT = 22001
INSTRUMENT_NO_BID_OR_ASK = 22002

PRICING_CONFIG_DB_CREATE_ERROR = 23000
PRICING_CONFIG_DUPLICATED_KEY = 23001
PRICING_CONFIG_KEY_NOT_EXIST = 23002
PRICING_CONFIG_DB_UPDATE_ERROR = 23003
PRICING_CONFIG_DB_DELETE_ERROR = 23004
PRICING_CONFIG_CORSIA_MISSING = 23005
PRICING_CONFIG_VRE_MODEL_DRIFT_MISSING = 23006


# error strings
ERROR_STRINGS = {
    USER_LIMIT_ALREADY_EXIST: "User limit record already exists",
    ORGANIZATION_LIMIT_ALREADY_EXIST: "Organization limit record already exists",
    USERNAME_REQUIRED: "Username is required",
    ORGANIZATION_REQUIRED: "Orgname is required",
    USER_LIMIT_NOT_EXIST: "Limit record for user does not exist",
    ORGANIZATION_LIMIT_NOT_EXIST: "Limit record for organization does not exist",
    LIMITED_ACCESS: "No permission to the endpoint",
    LIMITED_DELETED: "Limit is deleted successfully",

    USER_SUBSCRIPTION_NOT_EXIST: f"It looks like you have no pricing subscription. "
                                 f"Please contact {config.CONTACT_EMAIL} for more information",
    ORGANIZATION_SUBSCRIPTION_NOT_EXIST: f"It looks like organization has no pricing subscription. "
                                 f"Please contact {config.CONTACT_EMAIL} for more information",

    INSTRUMENT_DB_CREATE_ERROR: "Failed to create instrument instance into database",
    INSTRUMENT_KEY_CONFLICT: "The given instrument has the same key as the existing one on the current database",
    INSTRUMENT_NO_BID_OR_ASK: "No bid or ask price is set in the database",

    PRICING_CONFIG_DB_CREATE_ERROR: "Failed to create pricing config",
    PRICING_CONFIG_DUPLICATED_KEY: "Duplicated pricing config primary key",
    PRICING_CONFIG_KEY_NOT_EXIST: "Pricing config key does not exist",
    PRICING_CONFIG_DB_UPDATE_ERROR: "Failed to update pricing config",
    PRICING_CONFIG_DB_DELETE_ERROR: "Failed to delete pricing config",
    PRICING_CONFIG_CORSIA_MISSING: "CORSIA is not set in the database",
    PRICING_CONFIG_VRE_MODEL_DRIFT_MISSING: "VRE MODEL DRIFT is not set in the database"
}


def get_error_string_by_error_code(error_code: int) -> str:
    """
    return error string by error code
    """
    return ERROR_STRINGS[error_code]


def get_limit_exceed_error_string(error_code: int, limit: int, utilization: int, projects_requested: int) -> str:
    """
    :param error_code:
    :param limit: daily/monthly/lifetime limit of user/organization
    :param utilization: daily/monthly/lifetime utilization of user/organization
    :param projects_requested: number of projects requested to be calculated
    :return: error string related to the params
    """
    if error_code == USER_DAILY_LIMIT_EXCEED:
        return f"Your daily limit is {limit}. You have already performed {utilization} pricings and " \
               f"your current request contains {projects_requested} project(s) to be priced"
    elif error_code == USER_MONTHLY_LIMIT_EXCEED:
        return f"Your monthly limit is {limit}. You have already performed {utilization} pricings and "\
               f"your current request contains {projects_requested} project(s) to be priced"
    elif error_code == USER_LIFETIME_LIMIT_EXCEED:
        return f"Your lifetime limit is {limit}. You have already performed {utilization} pricings and "\
               f"your current request contains {projects_requested} project(s) to be priced"
    elif error_code == ORGANIZATION_DAILY_LIMIT_EXCEED:
        return f"Organization daily limit is {limit}. Organization have already performed {utilization} pricings" \
               f" and organization current request contains {projects_requested} project(s) to be priced"
    elif error_code == ORGANIZATION_MONTHLY_LIMIT_EXCEED:
        return f"Organization monthly limit is {limit}. Organization have already performed {utilization} pricings" \
               f" and organization current request contains {projects_requested} project(s) to be priced"
    elif error_code == ORGANIZATION_LIFETIME_LIMIT_EXCEED:
        return f"Organization lifetime limit is {limit}. Organization have already performed {utilization} pricings" \
               f" and organization current request contains {projects_requested} project(s) to be priced"
