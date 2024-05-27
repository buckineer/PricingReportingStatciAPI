from datetime import datetime
from sqlalchemy.orm import Session

from models import Benchmark, Forex
from schemas.request import RequestCreate, RequestType
import crud


def test_read_by_max_date(db: Session):
    benchmark: Benchmark = crud.benchmark.read_latest_benchmarks(db=db)
    assert benchmark is not None


def test_create_request(db: Session):
    request: RequestCreate = RequestCreate(
        request_type=RequestType.USER_REQUEST,
        username="test",
        body='{"body": "value"}',
        response='{"response": "value"}',
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        projects_requested_count=2,
        projects_priced_count=2
    )
    request_db = crud.request.create(db=db, request=request)
    assert request_db is not None
    assert request_db.username == request.username
    assert request_db.body == request.body
    assert request_db.response == request.response
    assert request_db.time == request.time
