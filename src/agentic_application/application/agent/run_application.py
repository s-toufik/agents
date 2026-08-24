from fastapi import FastAPI

from agentic_application.application.agent.create_application import create_application

app: FastAPI = create_application()
