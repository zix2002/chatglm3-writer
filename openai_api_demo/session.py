from __future__ import unicode_literals
from typing import List, Dict
from pydantic import BaseModel
import os
import json
import datetime
import uuid


class SessionType(BaseModel):
    id: str
    name: str
    createdAt: str


class MessageType(BaseModel):
    id: str = ''
    role: str = ''
    content: str = '新会话'


class SessionList(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: List[SessionType] = []


class MessageList(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: List[MessageType]


class SessionDetail(BaseModel):
    success: bool = True
    message: str = "success"
    data: dict


# 对话目录
SESSION_PATH = './sessions'


# 新建对话目录
def create_session_dir() -> bool:
    # 新建对话目录
    session_dir = os.path.join(SESSION_PATH)
    session_config_path = os.path.join(session_dir, 'config.json')
    if not os.path.exists(session_dir):
        os.mkdir(session_dir)
        if not os.path.exists(session_config_path):
            with open(session_config_path, "w") as f:
                f.write(json.dumps([]))

    return True


# 保存对话文件列表
def save_sessions(sessions: List[SessionType]) -> bool:
    create_session_dir()
    session_file_path = os.path.join(SESSION_PATH, 'config.json')
    data = []
    for session in sessions:
        data.append(session.dict())

    with open(session_file_path, "w") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))

    return True


# 保存对话文件列表
def save_messages(session_id: str, messages: List[MessageType]) -> bool:
    create_session_dir()
    session_file_path = os.path.join(SESSION_PATH, session_id + '.json')
    data = []
    for message in messages:
        data.append(message.dict())

    with open(session_file_path, "w") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))

    return True


# 获取会话列表
def get_sessions() -> List[SessionType]:
    create_session_dir()

    # 读取 config.json 文件
    session_file_path = os.path.join(SESSION_PATH, 'config.json')
    with open(session_file_path, "r") as f:
        data = json.loads(f.read())
        sessions: List[SessionType] = [SessionType(**item) for item in data]

    return sessions


# 获取会话
def get_session(session_id: str) -> SessionType:
    sessions = get_sessions()
    session = next(
        (item for item in sessions if item.id == session_id))
    if not session:
        raise Exception('会话不存在')

    return session


# 获取对话消息列表
def get_messages(session_id: str) -> List[MessageType]:

    message_file_path = os.path.join(SESSION_PATH, session_id + ".json")
    if not os.path.exists(message_file_path):
        return []

    with open(message_file_path, "r") as f:
        data = json.loads(f.read())
        messages: List[MessageType] = [MessageType(**item) for item in data]

    return messages


# 新建会话
def create_new_session() -> List[SessionType]:
    sessions = get_sessions()
    session_id = str(uuid.uuid4())

    sessions.append(SessionType(
        id=session_id,
        name='新会话',
        createdAt=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    save_sessions(sessions)

    return sessions


# 更新会话
def update_session(session_id: str, session: SessionType) -> List[SessionType]:
    sessions = get_sessions()
    old_session = next((item for item in sessions if item.id == session_id))
    old_session.name = session.name

    save_sessions(sessions)

    return sessions


# 更新会话消息
def update_message(session_id: str, message: MessageType) -> List[MessageType]:
    # 获取对话文件名
    session = get_session(session_id)

    if (session.name == '新会话'):
        session.name = message.content[:10]
        update_session(session_id, session)

    # 获取对话
    messages = get_messages(session_id)
    messages.append(MessageType(
        id=str(uuid.uuid4()),
        role=message.role,
        content=message.content
    ))
    save_messages(session_id, messages)

    return messages


# 删除会话
def delete_session(session_id: str) -> List[SessionType]:
    sessions = get_sessions()
    session = next((item for item in sessions if item.id == session_id))
    sessions.remove(session)

    save_sessions(sessions)

    # 删除会话消息文件
    message_file_path = os.path.join(SESSION_PATH, session_id + '.json')
    if os.path.exists(message_file_path):
        os.remove(message_file_path)

    return sessions


# 删除消息
def delete_message(session_id: str, message_id: str) -> List[MessageType]:
    messages = get_messages(session_id)
    message = next(item for item in messages if item.id == message_id)
    # 删除消息
    messages.remove(message)

    # 获取对话文件名
    save_messages(session_id, messages)

    return messages
