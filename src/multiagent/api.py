from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from multiagent.factory import build_manager_agent
from multiagent.logging_config import configure_logging
from multiagent.schemas import ManagerResponse, QualitativeResult, QuantitativeResult, QueryRequest

app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app_state["manager"] = build_manager_agent()
    yield
    app_state.clear()


app = FastAPI(
    title="Multi-Agent RAG System for Enterprise Documentation",
    version="1.0.0",
    lifespan=lifespan,
)


def get_manager():
    return app_state["manager"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=ManagerResponse)
def query(request: QueryRequest, manager=Depends(get_manager)):
    return manager.handle(request.query)


@app.post("/qualitative/query", response_model=QualitativeResult)
def qualitative_query(request: QueryRequest, manager=Depends(get_manager)):
    return manager.qualitative_agent.answer(request.query)


@app.post("/quantitative/query", response_model=QuantitativeResult)
def quantitative_query(request: QueryRequest, manager=Depends(get_manager)):
    return manager.quantitative_agent.answer(request.query)
