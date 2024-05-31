from fastapi import FastAPI, HTTPException, Depends
from .auth import router, get_current_user
from .database import engine, db_type, Todos, SQLModel
from sqlmodel import select
from starlette import status
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating Tables...")
    SQLModel.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(router)


@app.post("/api/todo")
async def create_todo(todo: Todos, db: db_type, user=Depends(get_current_user)):
    try:
        new_todo = Todos(
            description=todo.description, email=user["email"], completed=False
        )
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return {"message": "Todo added successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_msg": str(e)},
        )


@app.get("/api/todo")
async def get_user_todos(db: db_type, user=Depends(get_current_user)):
    try:
        user_todos = db.exec(select(Todos).where(Todos.email == user["email"])).all()
        if user_todos:
            return {"todos": user_todos}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todos not Found!"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_msg": str(e)},
        )


@app.put("/api/todo/{todo_id}")
async def update_todo(
    todo_id: int,
    todo: Todos,
    db: db_type,
    user=Depends(get_current_user),
):
    try:
        db_todo = db.exec(select(Todos).where(Todos.id == todo_id)).first()
        if db_todo:
            if todo.completed:
                db_todo.completed = todo.completed
            if todo.description:
                db_todo.description = todo.description
            db.commit()
            return {"message": "Todo updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not Found!"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.delete("/api/todo/{todo_id}")
async def delete_todo(todo_id: int, db: db_type, user=Depends(get_current_user)):
    try:
        new_todo = db.exec(select(Todos).where(Todos.id == todo_id)).first()
        if new_todo:
            db.delete(new_todo)
            db.commit()
            return {"message": "Todo deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not Found!"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_msg": str(e)},
        )
