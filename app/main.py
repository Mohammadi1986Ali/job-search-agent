import os
from pathlib import Path
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl, ConfigDict, Field, field_validator
from sqlalchemy import create_engine, String, Boolean, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.exc import IntegrityError

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(250))
    name_key: Mapped[str] = mapped_column(String(500), unique=True)
    industry: Mapped[str | None] = mapped_column(String(250))
    website_url: Mapped[str | None] = mapped_column(String(2048))
    career_url: Mapped[str | None] = mapped_column(String(2048))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

class CompanyInput(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    industry: str | None = Field(default=None, max_length=250)
    website_url: HttpUrl | None = None
    career_url: HttpUrl | None = None
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if not value:
            raise ValueError("Company name is required")
        return value

class CompanyOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    industry: str | None
    website_url: str | None
    career_url: str | None
    enabled: bool

def create_app(database_url=None):
    engine = create_engine(database_url or os.environ.get("DATABASE_URL", "sqlite:///./companies.db"), pool_pre_ping=True)

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    api = FastAPI(title="Job Search Agent", lifespan=lifespan)

    def db():
        with Session(engine) as session:
            yield session

    def get_company(company_id, session):
        company = session.get(Company, company_id)
        if company is None or company.archived:
            raise HTTPException(404, "Company not found")
        return company

    def save(session, company, data):
        for key, value in data.model_dump(mode="json").items():
            setattr(company, key, value)
        company.name_key = data.name.casefold()
        session.add(company)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, "Company name already registered (including archived records)")
        session.refresh(company)
        return company

    @api.get("/", include_in_schema=False)
    def company_dashboard():
        return FileResponse(Path(__file__).parent / "static" / "index.html", media_type="text/html")

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/companies", response_model=list[CompanyOutput])
    def list_companies(session: Session = Depends(db)):
        return list(session.scalars(select(Company).where(Company.archived.is_(False)).order_by(Company.name)))

    @api.post("/companies", response_model=CompanyOutput, status_code=201)
    def add_company(data: CompanyInput, session: Session = Depends(db)):
        return save(session, Company(), data)

    @api.get("/companies/{company_id}", response_model=CompanyOutput)
    def read_company(company_id: str, session: Session = Depends(db)):
        return get_company(company_id, session)

    @api.put("/companies/{company_id}", response_model=CompanyOutput)
    def update_company(company_id: str, data: CompanyInput, session: Session = Depends(db)):
        return save(session, get_company(company_id, session), data)

    @api.delete("/companies/{company_id}", status_code=204)
    def delete_company(company_id: str, session: Session = Depends(db)):
        company = get_company(company_id, session)
        company.archived = True
        company.enabled = False
        session.commit()

    return api

app = create_app()
