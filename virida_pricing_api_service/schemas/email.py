from pydantic import BaseModel


class AlertEmailTemplate(BaseModel):
    err_type: str
    err_message: str
    err_location: str
    err_time: str
    stacktrace: str
    environment: str


class BenchmarkIndexEmailTemplate(BaseModel):
    date: str
    subject: str
    benchmarks_table: str
    table: str
    errors: str
