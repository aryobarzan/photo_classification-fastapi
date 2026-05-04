from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.user import router as user_router
from routes.admin import router as admin_router

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.include_router(user_router)
app.include_router(admin_router)

# Allow CORS for all origins (should be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# TODO: rate limiting profile update
# TODO: paging for get_user_profiles
# TODO: polling / SSE for profile picture classification result
