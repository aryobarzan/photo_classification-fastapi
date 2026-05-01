from fastapi import FastAPI
from dotenv import load_dotenv
from routes.user import router as user_router
from routes.admin import router as admin_router

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.include_router(user_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# TODO: rate limiting profile update
# TODO: nsfw check
