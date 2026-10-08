from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import config
from .db import get_db

ROLES = ("operativo", "admin", "analista")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_clave(clave):
    return bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode()


def verificar_clave(clave, hashed):
    return bcrypt.checkpw(clave.encode(), hashed.encode())


def crear_token(email, rol):
    exp = datetime.now(timezone.utc) + timedelta(hours=config.JWT_HORAS)
    return jwt.encode({"sub": email, "rol": rol, "exp": exp}, config.JWT_SECRET, algorithm="HS256")


def usuario_actual(token: str = Depends(oauth2)):
    try:
        datos = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o vencido")
    u = get_db().usuarios.find_one({"email": datos["sub"]}, {"_id": 0, "clave": 0})
    if not u:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return u


def requiere(*roles):
    def dep(u=Depends(usuario_actual)):
        if u["rol"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso para esta acción")
        return u
    return dep
