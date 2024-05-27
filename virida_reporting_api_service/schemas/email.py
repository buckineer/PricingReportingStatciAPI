from pydantic import BaseModel


class BaseEmailTemplate(BaseModel):
    pass


class ReportsEmailTemplate(BaseEmailTemplate):
    date: str
    day: str
    subject: str
    reports_html: str
    errors: str
