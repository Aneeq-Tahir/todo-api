from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .database import db_type, Users
from .settings import JWT_ALGORITHM, JWT_SECRET_KEY
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from starlette import status
from typing import cast

router = APIRouter(prefix="/api/auth")

bcrypt_context = CryptContext(schemes=["bcrypt"])
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user: Users, res: Response, db: db_type):
    try:
        new_user = Users(
            email=user.email,
            hashed_password=bcrypt_context.hash(secret=user.hashed_password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        generate_access_token(
            email=new_user.email, user_id=cast(int, new_user.id), response=res
        )
        return {"message": "User created successfully"}
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: db_type,
    res: Response,
    formdata: OAuth2PasswordRequestForm = Depends(),
):
    try:
        user = authenticate_user(formdata.username, formdata.password, db)
        if user:
            token = generate_access_token(user.email, user.id, response=res)
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(
            token, str(JWT_SECRET_KEY), algorithms=[str(JWT_ALGORITHM)]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if not email or not user_id:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Incorrect Email or Password"
            )
        return {"email": email, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been expired"
        )


def authenticate_user(email: str, password: str, db: db_type):
    user = db.exec(select(Users).where(Users.email == email)).first()

    if user:
        if not bcrypt_context.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        else:
            return user
    else:
        return None


def generate_access_token(email: str, user_id: int, response: Response | None = None):
    expires = datetime.now(timezone.utc) + timedelta(minutes=20)

    encode = {"sub": email, "id": user_id, "exp": expires}
    token = jwt.encode(encode, str(JWT_SECRET_KEY), algorithm=str(JWT_ALGORITHM))
    if response:
        response.set_cookie(
            key="token",
            value=token,
            expires=expires,
            httponly=True,
            secure=True,
        )
    return token
