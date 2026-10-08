from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from .reglas import ESTADOS


class Registro(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    email: EmailStr
    clave: str = Field(min_length=8, max_length=128)


class TextoTicket(BaseModel):
    asunto: str = Field(default="", max_length=200)
    descripcion: str = Field(min_length=10, max_length=5000)


class CambioEstado(BaseModel):
    estado: Literal[ESTADOS]
    comentario: str = Field(default="", max_length=500)


class Reasignacion(BaseModel):
    equipo: str = Field(min_length=2, max_length=80)
    comentario: str = Field(default="", max_length=500)


class CambioRol(BaseModel):
    rol: Literal["operativo", "admin", "analista"]
