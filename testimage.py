# main.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from models import SessionLocal, init_db, Image
from io import BytesIO
from starlette.responses import StreamingResponse, HTMLResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Initialize database
init_db()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Dependency to get the SQLAlchemy session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_form(request: Request):
    return templates.TemplateResponse("testimage.html", {"request": request})

@app.post("/upload/")
async def upload_image(
    eventname: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        image_data = await file.read()
        db_image = Image(eventname=eventname, image_data=image_data)
        db.add(db_image)
        db.commit()
        return {"filename": file.filename, "id": db_image.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image/{image_id}")
async def get_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(Image).filter(Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return StreamingResponse(BytesIO(db_image.image_data), media_type="image/jpeg")

@app.get("/image/{image_id}/info")
async def get_image_info(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(Image).filter(Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"id": db_image.id, "eventname": db_image.eventname}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)