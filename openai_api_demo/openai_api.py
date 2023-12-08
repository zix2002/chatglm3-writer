# coding=utf-8
# Implements API for ChatGLM3-6B in OpenAI's format. (https://platform.openai.com/docs/api-reference/chat)
# Usage: python openai_api.py
# Visit http://localhost:8000/docs for documents.

# 在OpenAI的API中，max_tokens 等价于 HuggingFace 的 max_new_tokens 而不是 max_length，。
# 例如，对于6b模型，设置max_tokens = 8192，则会报错，因为扣除历史记录和提示词后，模型不能输出那么多的tokens。

import os
import time
from contextlib import asynccontextmanager
from turtle import st
from typing import List, Literal, Optional, Union, Dict

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from transformers import AutoTokenizer, AutoModel

import writer as writer
from writer import BookList, BookDetail, ChapterList, ChapterDetail, BookType, ChapterType

import session
from session import SessionType, MessageType, SessionList, MessageList, SessionDetail


from utils import process_response, generate_chatglm3, generate_stream_chatglm3

MODEL_PATH = os.environ.get(
    'MODEL_PATH', '/Users/zix/workspace/llm/ChatGLM3/models/chatglm3-6b')
TOKENIZER_PATH = os.environ.get("TOKENIZER_PATH", MODEL_PATH)
DEVICE = 'cuda' if torch.cuda.is_available() else 'mps'


@asynccontextmanager
async def lifespan(app: FastAPI):  # collects GPU memory
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # 处理异常
    logger.error(exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc)
        },
    )


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "owner"
    root: Optional[str] = None
    parent: Optional[str] = None
    permission: Optional[list] = None


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard] = []


class FunctionCallResponse(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "function"]
    content: str = ''
    name: Optional[str] = None
    function_call: Optional[FunctionCallResponse] = None


class DeltaMessage(BaseModel):
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None
    function_call: Optional[FunctionCallResponse] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.8
    top_p: Optional[float] = 0.8
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    functions: Optional[Union[dict, List[dict]]] = None
    # Additional parameters
    repetition_penalty: Optional[float] = 1.1


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "function_call"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length", "function_call"]]


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0
    completion_tokens: Optional[int] = 0


class ChatCompletionResponse(BaseModel):
    model: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    choices: List[Union[ChatCompletionResponseChoice,
                        ChatCompletionResponseStreamChoice]]
    created: Optional[int] = Field(default_factory=lambda: int(time.time()))
    usage: Optional[UsageInfo] = None


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    model_card = ModelCard(id="chatglm3-6b")
    return ModelList(data=[model_card])


######################
# 书籍相关接口
######################
# 获取书籍列表
@app.get("/v1/books", response_model=BookList)
async def fetchBooks():
    books = writer.get_books()
    return BookList(data=books)


# 创建书籍
@app.post("/v1/books", response_model=BookList)
async def createBook():

    books = writer.create_book()
    return BookList(data=books)


# 更新书籍
@app.put("/v1/books/{book_id}", response_model=BookDetail)
async def updateBook(book_id: str, request: BookType):
    book_detail = writer.update_book(book_id, request)

    return BookDetail(data=book_detail)  # type: ignore


# 删除书籍
@app.delete("/v1/books/{book_id}", response_model=BookList)
async def deleteBook(book_id: str):
    books = writer.delete_book(book_id)
    return BookList(data=books)


######################
# 章节相关接口
######################

# 获取章节详情
@app.get("/v1/books/{book_id}/chapters/{chapter_id}", response_model=ChapterDetail)
async def fetchChapter(book_id: str, chapter_id: str):

    chapter_detail = writer.get_chapter(book_id, chapter_id)

    return ChapterDetail(data=chapter_detail)


# 创建章节
@app.post("/v1/books/{book_id}/chapters", response_model=BookList)
async def create_chapter(book_id: str, request: ChapterType):
    book_list = writer.create_chapter(book_id, request)
    return BookList(data=book_list)


# 更新章节
@app.put("/v1/books/{book_id}/chapters/{chapter_id}", response_model=BookList)
async def update_chapter(book_id: str, chapter_id: str, request: ChapterType):
    book_list = writer.update_chapter(book_id, chapter_id, request)
    return BookList(data=book_list)


# 删除章节
@app.delete("/v1/books/{book_id}/chapters/{chapter_id}", response_model=BookList)
async def delete_chapter(book_id: str, chapter_id: str):
    book_list = writer.delete_chapter(book_id, chapter_id)
    return BookList(data=book_list)


##########################
# 聊天相关的API
##########################

# 获取会话列表
@app.get("/v1/sessions", response_model=SessionList)
async def getSessions():
    session_list = session.get_sessions()
    return SessionList(data=session_list)


# 新建会话
@app.post("/v1/sessions", response_model=SessionList)
async def createNewSession():
    session_list = session.create_new_session()
    return SessionList(data=session_list)


# 删除会话
@app.delete("/v1/sessions/{session_id}", response_model=SessionList)
async def deleteSessionById(session_id: str):
    sessions = session.delete_session(session_id)
    return SessionList(data=sessions)


# 获取会话消息列表
@app.get("/v1/sessions/{session_id}/messages", response_model=MessageList)
async def getMessagesSessionById(session_id: str):
    message_list = session.get_messages(session_id)
    return MessageList(data=message_list)


# 更新会话消息
@app.post("/v1/sessions/{session_id}/messages", response_model=MessageList)
async def getSessionById(session_id: str, request: MessageType):
    messages = session.update_message(session_id, request)
    return MessageList(data=messages)


# 删除会话消息
@app.delete("/v1/sessions/{session_id}/messages/{message_id}", response_model=MessageList)
async def deleteMessage(session_id: str, message_id: str):
    messages = session.delete_message(session_id, message_id)
    return MessageList(data=messages)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    global model, tokenizer

    if len(request.messages) < 1 or request.messages[-1].role == "assistant":
        raise HTTPException(status_code=400, detail="Invalid request??")

    gen_params = dict(
        messages=request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens or 1024,
        echo=False,
        stream=request.stream,
        repetition_penalty=request.repetition_penalty,
        functions=request.functions,
    )

    logger.debug(f"==== request ====\n{gen_params}")

    if request.stream:
        generate = predict(request.model, gen_params)
        return EventSourceResponse(generate, media_type="text/event-stream")

    response = generate_chatglm3(model, tokenizer, gen_params)
    usage = UsageInfo()

    function_call, finish_reason = None, "stop"
    if request.functions:
        try:
            function_call = process_response(response["text"], use_tool=True)
        except:
            logger.warning("Failed to parse tool call")

    if isinstance(function_call, dict):
        finish_reason = "function_call"
        function_call = FunctionCallResponse(**function_call)

    message = ChatMessage(
        role="assistant",
        content=response["text"],
        function_call=function_call if isinstance(
            function_call, FunctionCallResponse) else None,
    )

    choice_data = ChatCompletionResponseChoice(
        index=0,
        message=message,
        finish_reason=finish_reason,
    )

    task_usage = UsageInfo.model_validate(response["usage"])
    for usage_key, usage_value in task_usage.model_dump().items():
        setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    return ChatCompletionResponse(model=request.model, choices=[choice_data], object="chat.completion", usage=usage)


async def predict(model_id: str, params: dict):
    global model, tokenizer

    choice_data = ChatCompletionResponseStreamChoice(
        index=0,
        delta=DeltaMessage(role="assistant"),
        finish_reason=None
    )
    chunk = ChatCompletionResponse(model=model_id, choices=[
                                   choice_data], object="chat.completion.chunk")
    yield "{}".format(chunk.model_dump_json(exclude_unset=True))

    previous_text = ""
    for new_response in generate_stream_chatglm3(model, tokenizer, params):
        decoded_unicode = new_response["text"]
        delta_text = decoded_unicode[len(previous_text):]
        previous_text = decoded_unicode

        finish_reason = new_response["finish_reason"]
        if len(delta_text) == 0 and finish_reason != "function_call":
            continue

        function_call = None
        if finish_reason == "function_call":
            try:
                function_call = process_response(
                    decoded_unicode, use_tool=True)
            except:
                print("Failed to parse tool call")

        if isinstance(function_call, dict):
            function_call = FunctionCallResponse(**function_call)

        delta = DeltaMessage(
            content=delta_text,
            role="assistant",
            function_call=function_call if isinstance(
                function_call, FunctionCallResponse) else None,
        )

        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=delta,
            finish_reason=finish_reason
        )
        chunk = ChatCompletionResponse(model=model_id, choices=[
                                       choice_data], object="chat.completion.chunk")
        yield "{}".format(chunk.model_dump_json(exclude_unset=True))

    choice_data = ChatCompletionResponseStreamChoice(
        index=0,
        delta=DeltaMessage(),
        finish_reason="stop"
    )
    chunk = ChatCompletionResponse(model=model_id, choices=[
                                   choice_data], object="chat.completion.chunk")
    yield "{}".format(chunk.model_dump_json(exclude_unset=True))
    yield '[DONE]'


if __name__ == "__main__":

    # tokenizer = AutoTokenizer.from_pretrained(
    #     TOKENIZER_PATH, trust_remote_code=True)
    # if 'cuda' in DEVICE:  # AMD, NVIDIA GPU can use Half Precision
    #     model = AutoModel.from_pretrained(
    #         MODEL_PATH, trust_remote_code=True).to(DEVICE).eval()
    # else:  # CPU, Intel GPU and other GPU can use Float16 Precision Only
    #     model = AutoModel.from_pretrained(
    #         MODEL_PATH, trust_remote_code=True).half().to(DEVICE).eval()
    uvicorn.run(app, host='0.0.0.0', port=8600, workers=1)
