from enum import Enum


class Permission(str, Enum):
    USER_ADMINISTRATION = "api_user_administration"
    BENCHMARK = "api_benchmark"
    FOREX = "api_forex"
    VRE = "api_price_vre"
    PLATTS = "api_price_platts"
    ADVANCED = "api_advanced"
