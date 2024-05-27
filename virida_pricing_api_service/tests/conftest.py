import os
from datetime import datetime
from typing import Generator, List
from functools import wraps

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from aiohttp import ClientSession, ClientTimeout
import pytest

from main import app
from models import Forex, BlockedAPIKey
from schemas.api_key import BlockedAPIKeyCreate
from schemas.forex import ForexCreate
from schemas.limit import LimitCreate, LimitType
from database import SessionLocal, DatabaseContextManager
import crud

from config import import_class
config = import_class(os.environ['APP_SETTINGS'])

FOREX = ForexCreate(date="2050-01-01", currency="EUR", close=0, timestamp=2500000000)

USER_LIMIT = LimitCreate(limit_type=LimitType.USER_LIMIT, username="test", daily=2, monthly=2, lifetime=2,
                         lifetime_reset_date=datetime.today().replace(hour=0, minute=0, second=0)
                         .strftime("%Y-%m-%d %H:%M:%S"))
ORGANIZATION_LIMIT = LimitCreate(limit_type=LimitType.ORGANIZATION_LIMIT, orgname="test_org", daily=10, monthly=30,
                                 lifetime=100, lifetime_reset_date=datetime.today().replace(hour=0, minute=0, second=0)
                                 .strftime("%Y-%m-%d %H:%M:%S"))
EXPIRED_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ0ZXN0Iiwia2V5X3R5cGUiOiJ1c2VyIiwiaWF0IjoxNjE3ODA1MDcwLCJleHAiOjE2MTc4MDUwNzEsInBlcm1pc3Npb25zIjp7ImlzX2FkbWluIjpmYWxzZX19.YJFvx1mMgAPWZXHTROQOGZZ7cDbNIoZk3UKnBXLMuHAWZyxQ7SzMjnuXoKcs_ahweg4qKvq3JpjBgYyYF5NXBifutIKGROBULLbzF_6hNvViUK84Xn_wiRRJAi9uBwl6KnWB22OpyueFt26TfUDLKUw2JaFs28rcxVmKkB0y6eo4muhTtwnq4tGucfKMxResTTO10eFEBP7xxeAY9TJNWjY1NK4TwIQ1tO8kfWp84PyPhh52v8dsm-ytYQCggwwqfjlo8jKH1_zdoRSKkQaj956WQu7kf4dM_nggcwkbaZ6Y7OEh6P8FE7F56DO4j-8uyhWUIYhkuO1ipA4vBDv6Mg"
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ0ZXN0Iiwia2V5X3R5cGUiOiJ1c2VyIiwiaWF0IjoxNjE3ODA1MTcxLCJleHAiOjE2NTMxMTY0MDAsInBlcm1pc3Npb25zIjp7ImlzX2FkbWluIjpmYWxzZX19.wLPncXPf0N5pU45vz6IjJsypWjuy5lPeR-xZnbTmZEQUSGsAOznR_-pxXbPUaY0_7vZDfw77mBil7Yw64vmrF1D2NiOKtCO9Q2fsaHMnC_TV9GJgeMQRHXtBzdmM01CBc9Z_cprmBAZklmAhrABBvEHwL8ZQIW7GeD1TOC3cDcEFeKtD2Z1JoXOvJ2eJ-bFTom0LzOg8ZlRHxIc9WktIvko8506aFcntVRqFqxnhBkfVNi6nZ3LLFqwfighDevNcLQp8U0Zbb_LHMnmeZ_eA9TUHieazMWxS4rRf-JSW_ciaFAEWB1BCz7Fj6V8K_f5jIvforiHDOq4xEvbNocls8g"

EXPIRED_AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsInBhc3N3b3JkX3Jlc2V0X3JlcXVpcmVkIjp0cnVlLCJvcmduYW1lIjoidmlyaWRhIDIiLCJpYXQiOjE2MTc4MDkzMDAsImV4cCI6MTYxNzgwOTMwMH0.WZRvXKrtHYxkuPvQwcVtVEc7l5nx2RTbeS9q6Qdx0wg5zoMZiVWgVwrxeRMGktPbloeEawBzs-dyOoNT2jaxdRIsrThPaQqZvSEk8FUuRLex0lPxuxMNJ6vVS75MKKA0_61KQV9OCLHTZgscNSQ1A-HqUgy9homC_CJxqkB-BwSWtKFt5TSk0r-j8gqn77gOC32rHwce8E1IKp64Wk7vH9007w0koHr9lY-RI1b4uAx3R375Vg-F8mT7n730qkrnPxjMmIgtwHwsV4DJdU3vHQq9dbqGsOUJGurHF5wyRZvG7nBM1i7cOIMDMFR_C_P5j1JTudB8jY0EyerUk_rqAA"
AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsInBhc3N3b3JkX3Jlc2V0X3JlcXVpcmVkIjp0cnVlLCJvcmduYW1lIjoidmlyaWRhIDIiLCJpYXQiOjE2MTc4MDkzNDUsImV4cCI6MTYyMDQwMTM0NX0.oh0Ov5ksVT2s1asbEcV2ReCxatD5FEVMayYmuBH3f2KvIsrVAxHTL9B9ubcJl9nWWXkiPUmxyEZNhxVmO3MpdUbV2r0m-mMCdOzAaVS8mbURaMGgJ8391JBQhezik8Iv2hNyVSbVVPUvy-QRvpMU1smIdcmwtLAp5FyTk55TbieeliQxdppvAg5WXOY2NODhxmOxLGzEcchOa2loX75z5Z681arOgjhFo-F8TrmsIy0jFlWQM7AdE8ottbdEkscHvrUk4WWvQHN_YGJ8QCHaizr7l7WVwsxQsU4NiSzgxxh99sqDyMqpfCtflcILtkTkl8zmR47yCZkO0jvP1gu-nQ"

ADMIN_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VybmFtZSI6ImZpcnN0YWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwicGFzc3dvcmRfcmVzZXRfcmVxdWlyZWQiOnRydWUsIm9yZ25hbWUiOm51bGwsImlhdCI6MTYxNzgxNjgwOCwiZXhwIjoxNjIwNDA4ODA4fQ.lABE3Yoa8j_UlRwi_leuFvQbK1ZK2Wa4soTutwRjMA-X2fQs01bRaSxfa8yFRTr2oE4yuBV87jYR9agXWNxztx61_kTx14nA8rzsLsj5AmvhjEq3G9mz9TTKXVPRUjsmF2X3enrMPSIgAL4Z_AfVzshndNI_i9T5Q9WboCv88AIowvoCCchHIEABJiXVv80i-EtIYRjiTX_m7qSaE7coFee-jV_CslOJ5bMn1Cn4BOMfzlCcAepKindMbpS3jG_sGuN8umEjiZdEX6Hi1PoaaEdgxTAvX3OEieFjBVtKG1mZVHVI9l0q350t5nPy7ja_UZ2z4UrXU3AuudbLoLajlg"

APIKEY_BLACKLIST_ONE = [
    BlockedAPIKeyCreate(api_key="test_api_key_1")
]

APIKEY_BLACKLIST_TWO = [
    BlockedAPIKeyCreate(api_key="test_api_key_2"),
    BlockedAPIKeyCreate(api_key="test_api_key_3")
]

VALID_PROJECT = {
    "version": 2,
    "standard": ["verra"],
    "project": ["afolu.01"],
    "sdg": ["13"],
    "vintage": "2021",
    "country": ["CD"],
    "corsia": 0,
    "region": None,
    "subregion": None
}

INVALID_PROJECT = {
    "version": 2,
    "corsia": 0,
    "standard": ["abc"],
    "project": ["11"],
    "sdg": ["1", "10", "1"],
    "vintage": "2020",
    "country": ["AD"],
    "region": ["Africa"],
    "subregion": ["Australia and New Zealand"]
}

VALID_PROJECT_VALIDATION = {
    "project": VALID_PROJECT,
    "status": "NOK",
    "description": ""
}

INVALID_PROJECT_VALIDATION = {
    "project": INVALID_PROJECT,
    "status": "NOK",
    "description": "region and sub-region are not allowed, kindly use country only"
}

VALID_PROJECT_MAPPING = {
    "project": VALID_PROJECT,
    "status": "OK",
    "description": "",
    "mapping": {
        "standard": [0, 0, 1],
        "project": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "sdg": [2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "vintage": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "country": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "region": [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
        "subregion": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
}

INVALID_PROJECT_MAPPING = {
    "project": INVALID_PROJECT,
    "status": "NOK",
    "description": "standard value: 'abc' is wrong.",
    "mapping": None
}

VALID_PROJECT_PRICING = {
    "project": VALID_PROJECT,
    "horizon": "spot",
    "status": "OK",
    "description": "",
    "formula": 1,
    "sigma": 0.5807005167007446,
    "beta": 0.3128401041030884,
    "mid": 2.7844592265887997,
    "bid": 6.049233956714127,
    "ask": 6.511506785503963,
    "vintage_discount_factor": 0.93057946,
    "eua": 33.22796759194329,
    "model_id": "800-8x800-2_v5b_weights"
}

INVALID_PROJECT_PRICING = {
    "project": INVALID_PROJECT,
    "horizon": "spot",
    "status": "NOK",
    "description": "region and sub-region are not allowed, kindly use country only",
    "formula": None,
    "sigma": None,
    "beta": None,
    "mid": None,
    "bid": None,
    "ask": None,
    "vintage_discount_factor": None,
    "eua": None,
    "model_id": None
}


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def aiohttp_session():
    session: ClientSession = ClientSession(timeout=ClientTimeout(total=config.HTTP_CLIENT_TIMEOUT_SECONDS))
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def username() -> str:
    return USER_LIMIT.username


@pytest.fixture
def orgname() -> str:
    return ORGANIZATION_LIMIT.orgname


@pytest.fixture
def user_limit() -> LimitCreate:
    return USER_LIMIT


@pytest.fixture
def organization_limit() -> LimitCreate:
    return ORGANIZATION_LIMIT


@pytest.fixture(scope="module")
def api_key() -> str:
    return API_KEY


@pytest.fixture(scope="module")
def expired_api_key() -> str:
    return EXPIRED_API_KEY


@pytest.fixture(scope="module")
def auth_token() -> str:
    return AUTH_TOKEN


@pytest.fixture(scope="module")
def expired_auth_token() -> str:
    return EXPIRED_AUTH_TOKEN


@pytest.fixture(scope="module")
def token_auth_header() -> dict:
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


@pytest.fixture(scope="module")
def admin_auth_header() -> dict:
    return {"Authorization": f"Bearer {ADMIN_TOKEN}"}


@pytest.fixture(scope="module")
def admin_auth_token() -> str:
    return ADMIN_TOKEN


@pytest.fixture(scope="module")
def authorization_header() -> dict:
    return {"X-API-KEY": API_KEY}


@pytest.fixture(scope="module")
def valid_project() -> dict:
    return VALID_PROJECT


@pytest.fixture(scope="module")
def invalid_project() -> dict:
    return INVALID_PROJECT


@pytest.fixture(scope="module")
def valid_project_validations() -> List[dict]:
    return [VALID_PROJECT_VALIDATION, VALID_PROJECT_VALIDATION]


@pytest.fixture(scope="module")
def invalid_project_validations() -> List[dict]:
    return [INVALID_PROJECT_VALIDATION, INVALID_PROJECT_VALIDATION]


@pytest.fixture(scope="module")
def valid_and_invalid_project_validations() -> List[dict]:
    return [VALID_PROJECT_VALIDATION, INVALID_PROJECT_VALIDATION]


@pytest.fixture(scope="module")
def valid_project_mappings() -> List[dict]:
    return [VALID_PROJECT_MAPPING, VALID_PROJECT_MAPPING]


@pytest.fixture(scope="module")
def invalid_project_mappings() -> List[dict]:
    return [INVALID_PROJECT_MAPPING, INVALID_PROJECT_MAPPING]


@pytest.fixture(scope="module")
def valid_and_invalid_project_mappings() -> List[dict]:
    return [VALID_PROJECT_MAPPING, INVALID_PROJECT_MAPPING]


@pytest.fixture(scope="module")
def valid_project_pricings() -> List[dict]:
    return [VALID_PROJECT_PRICING, VALID_PROJECT_PRICING]


@pytest.fixture(scope="module")
def invalid_project_pricings() -> List[dict]:
    return [INVALID_PROJECT_PRICING, INVALID_PROJECT_PRICING]


@pytest.fixture(scope="module")
def valid_and_invalid_project_pricings() -> List[dict]:
    return [VALID_PROJECT_PRICING, INVALID_PROJECT_PRICING]


@pytest.fixture
def apikey_blacklist_one() -> List[BlockedAPIKeyCreate]:
    return APIKEY_BLACKLIST_ONE


@pytest.fixture
def apikey_blacklist_two() -> List[BlockedAPIKeyCreate]:
    return APIKEY_BLACKLIST_TWO


def reinit_limit():
    with DatabaseContextManager() as db:
        crud.limit.delete_by_username(db=db, username=USER_LIMIT.username)
        crud.limit.delete_by_orgname(db=db, orgname=ORGANIZATION_LIMIT.orgname)

        crud.limit.create(db=db, limit=USER_LIMIT)
        crud.limit.create(db=db, limit=ORGANIZATION_LIMIT)

        crud.request.delete_by_username(db=db, username=USER_LIMIT.username)
        crud.request.delete_by_orgname(db=db, orgname=ORGANIZATION_LIMIT.orgname)


def reinit_apikey_blacklist():
    with DatabaseContextManager() as db:
        db.query(BlockedAPIKey).delete()


def reinit(*entities):
    def inner(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            reinit_entities(*entities)
            return result
        return wrapper
    return inner


def reinit_entities(*entities):
    for entity in entities:
        if entity == "limit":
            reinit_limit()
        elif entity == "apikey_blacklist":
            reinit_apikey_blacklist()


def pytest_sessionstart(session):
    reinit_entities("limit")
    reinit_entities("apikey_blacklist")


def pytest_sessionfinish(session):
    # remove limits
    with DatabaseContextManager() as db:
        crud.limit.delete_by_username(db=db, username=USER_LIMIT.username)
        crud.limit.delete_by_orgname(db=db, orgname=ORGANIZATION_LIMIT.orgname)
        crud.limit.delete_by_username(db=db, username="test1")
        db.query(BlockedAPIKey).filter_by(api_key=APIKEY_BLACKLIST_ONE[0])
        db.query(BlockedAPIKey).filter_by(api_key=APIKEY_BLACKLIST_TWO[0])
        db.query(BlockedAPIKey).filter_by(api_key=APIKEY_BLACKLIST_TWO[1])
