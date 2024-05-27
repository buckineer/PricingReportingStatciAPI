from typing import List

from conftest import reinit
from sqlalchemy.orm import Session

import crud
from schemas.api_key import BlockedAPIKeyCreate


@reinit("apikey_blacklist")
def test_refresh_apikey_blacklist(db: Session, apikey_blacklist_one: List[BlockedAPIKeyCreate],
                                  apikey_blacklist_two: List[BlockedAPIKeyCreate]):
    apikey_blacklist = crud.api_key.refresh_apikey_blacklist(db=db, apikey_blacklist=apikey_blacklist_one)
    assert apikey_blacklist
    assert len(apikey_blacklist) == len(apikey_blacklist_one)
    assert apikey_blacklist[0].api_key == apikey_blacklist_one[0].api_key

    apikey_blacklist = crud.api_key.refresh_apikey_blacklist(db=db, apikey_blacklist=apikey_blacklist_two)
    assert apikey_blacklist
    assert len(apikey_blacklist) == len(apikey_blacklist_two)
    for index in range(len(apikey_blacklist)):
        assert apikey_blacklist[index].api_key == apikey_blacklist_two[index].api_key
