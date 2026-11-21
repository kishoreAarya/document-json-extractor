
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Resume(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None
    email: EmailStr | None
    phone: str | None

    skills: list[str]

    experience_years: float | None = Field(ge=0)

    education: str | None
