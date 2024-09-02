from fastapi import FastAPI, Form, Request, Depends, HTTPException, BackgroundTasks,Path,File,UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer
from database import SessionLocal, engine, Base
from models import User, Event, EventForm,Image
from schemas import UserSchema, EventCreate, EventResponse, EventFormCreate, EventFormResponse
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from io import BytesIO
from starlette.responses import StreamingResponse
# from PIL import  Image
from datetime import datetime


from datetime import datetime, timedelta
import jwt
from typing import Optional
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None



SECRET_KEY = "your-secret-key"  # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


from fastapi import Header


def get_current_user(request: Request):
    authorization: str = request.headers.get('Authorization')
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token is missing or invalid format")

    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid token")

    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=403, detail="User not found")

    return user_email


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="b436b7880fc6857423bb4be8")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

serializer = URLSafeTimedSerializer("b436b7880fc6857423bb4be8")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request):
    user_email = request.session.get('user_email')
    if not user_email:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return user_email

def get_eventid(request:Request):
    event_id=request.session.get('id')
    if not event_id:
        return "error"
    return event_id

@app.get("/", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def register_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already exists"})

    new_user = User(email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user and user.password == password:
        request.session['user_email'] = email
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.pop('user_email', None)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user_email = get_current_user(request)
    return templates.TemplateResponse("dashboard.html", {"request": request, "email": user_email})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_post(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "Email not found"})

    token = serializer.dumps(email, salt="password-reset-salt")
    reset_url = f"{request.url_for('reset_password')}?token={token}"
    background_tasks.add_task(send_reset_email, email, reset_url)
    return templates.TemplateResponse("forgot_password.html", {"request": request, "message": "Password reset link sent to your email."})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password(request: Request, token: str):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except Exception:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token"})

    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password_post(
    request: Request,
    password: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except Exception:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token"})

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password = password
        db.commit()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Something went wrong. Please try again."})

def send_reset_email(recipient_email: str, reset_url: str):
    sender_email = "bodavamshikrishna30@gmail.com"
    sender_password = "kayo eely essb yzxc"
    subject = "Password Reset Request"

    template_path = os.path.join(os.path.dirname(__file__), "templates", "reset_email_template.html")
    with open(template_path) as file_:
        template = Template(file_.read())

    html_content = template.render(reset_url=reset_url)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email

    part = MIMEText(html_content, "html")
    message.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())

@app.get("/events", response_class=HTMLResponse)
async def events(request: Request, db: Session = Depends(get_db)):
    user_email = get_current_user(request)  # Get the current user's email
    user = db.query(User).filter(User.email == user_email).first()  # Fetch the current user from the database

    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    user_events = db.query(Event).filter(Event.user_id == user.id).all()  # Fetch only events belonging to the user

    return templates.TemplateResponse("events.html", {"request": request, "email": user_email, "events": user_events})


@app.get("/create-event", response_class=HTMLResponse)
async def create_event(request: Request):
    return templates.TemplateResponse("create_event.html", {"request": request})

@app.post("/events/", response_class=HTMLResponse)
async def create_event_post(
    request: Request,
    event_name: str = Form(...),
    venue_address: str = Form(...),
    event_date: str = Form(...),
    audience: bool = Form(False),
    delegates: bool = Form(False),
    speaker: bool = Form(False),
    nri: bool = Form(False),
    db: Session = Depends(get_db)
):
    user_email = get_current_user(request)  # Get the current user's email
    user = db.query(User).filter(User.email == user_email).first()  # Fetch the current user from the database

    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    # Convert event_date string to a Python date object
    try:
        event_date_converted = datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

    new_event = Event(
        event_name=event_name,
        venue_address=venue_address,
        event_date=event_date_converted,  # Use the converted date object
        audience=audience,
        delegates=delegates,
        speaker=speaker,
        nri=nri,
        user_id=user.id  # Associate the event with the user's ID
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    eventn = event_name
    f = db.query(Event).filter(Event.event_name==eventn).first()
    event_id=f.id
    request.session['event_id']=event_id


    # Redirect to dashboard after event creation
    return templates.TemplateResponse("formlink.html",{"request": request, "event_id": event_id})

@app.get("/submit_form")
def getforms(request:Request):
    # event_id = request.session.get('event_id')
    # print("events",event_id)
    return templates.TemplateResponse("forms.html",{"request": request})


@app.post("/submit_form")
async def postforms(request:Request,event_name=Form(...),name:str=Form(...),email:str=Form(...),phoneno:str=Form(...),Dropdown:str=Form(...),
    file: UploadFile = File(...),db: SessionLocal = Depends(get_db)):
    id=1
    user=db.query(Event).filter(Event.event_name==event_name).first()
    event_id=user.id
    # event_id=request.session.get('event_id')
    # print("submit_form", event_id)
    image_data = await file.read() if file else None
    print(type(image_data))
    formuser=EventFormCreate(id=id,event_id=event_id,name=name,email=email,phoneno=phoneno,Dropdown=Dropdown,image=image_data)
    user=EventForm(name=formuser.name,event_id=formuser.event_id,email=formuser.email,phoneno=formuser.phoneno,Dropdown=formuser.Dropdown, image_data=formuser.image )
    db.add(user)
    db.commit()
    db.refresh(user)
    return "successful"


@app.get("/EventRegistrations")
def getEventRegistrations(request:Request):
    return templates.TemplateResponse("registrations.html",{"request": request})
@app.post("/EventRegistrations")
def getEventR(request:Request,event_name=Form(...),db: SessionLocal = Depends(get_db)):
    user_email = get_current_user(request)
    user=db.query(User).filter(User.email==user_email).first()
    r=db.query(Event).filter(Event.id==user.id).first()
    result=db.query(EventForm).filter(EventForm.event_id==r.id ).all()

    # rows = [row._asdict() for row in result]
    # print(rows)

    return "done"





@app.get("/edit-event", response_class=HTMLResponse)
async def edit_event(request: Request, db: Session = Depends(get_db)):
    event_id = request.query_params.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="Event ID is required")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return templates.TemplateResponse("edit_event.html", {"request": request, "event": event})

@app.post("/edit-event", response_class=HTMLResponse)
async def edit_event_post(
    request: Request,
    event_id: int = Form(...),
    event_name: str = Form(...),
    venue_address: str = Form(...),
    event_date: str = Form(...),
    audience: bool = Form(False),
    delegates: bool = Form(False),
    speaker: bool = Form(False),
    nri: bool = Form(False),
    db: Session = Depends(get_db)
):
    user_email = get_current_user(request)  # Get the current user's email
    user = db.query(User).filter(User.email == user_email).first()  # Fetch the current user from the database

    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    # Convert event_date string to a Python date object
    try:
        event_date_converted = datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

    # Fetch the event to update
    event_to_update = db.query(Event).filter(Event.id == event_id, Event.user_id == user.id).first()

    if not event_to_update:
        raise HTTPException(status_code=404, detail="Event not found or not authorized")

    # Update event details
    event_to_update.event_name = event_name
    event_to_update.venue_address = venue_address
    event_to_update.event_date = event_date_converted  # Use the converted date object
    event_to_update.audience = audience
    event_to_update.delegates = delegates
    event_to_update.speaker = speaker
    event_to_update.nri = nri

    db.commit()
    db.refresh(event_to_update)

    # Redirect to dashboard after event update
    return RedirectResponse(url="/events", status_code=303)

@app.post("/delete-event", response_class=HTMLResponse)
async def delete_event(
    request: Request,
    event_id: int = Form(...),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()
    return RedirectResponse(url="/events", status_code=303)


@app.get("/image/{image_id}")
async def get_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(EventForm).filter(EventForm.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return StreamingResponse(BytesIO(db_image.image_data), media_type="image/jpeg")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)