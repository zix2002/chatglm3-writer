from __future__ import unicode_literals
import uuid
import os
import json
import datetime
from click import prompt
from pydantic import BaseModel
from typing import List


class CharacterType(BaseModel):
    name: str = ""
    description: str = ""


class ParagraphType(BaseModel):
    id: str = ""
    previous: str = ""
    style: str = ""
    fragment: str = ""
    requirement: str = ""
    content: str = ""


class ChapterType(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    summary: str = ""
    content: str = ""
    paragraphs: List[ParagraphType] = []


class BookType(BaseModel):
    id: str = ""
    novelType: str = "都市悬疑"
    title: str = ""
    cover: str = ""
    description: str = ""
    summary: str = ""
    characters: List[CharacterType] = []
    chapters: List[ChapterType] = []
    createdAt: str = ""


class BookList(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: List[BookType] = []


class BookDetail(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: BookType


class ChapterList(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: List[ChapterType] = []


class ChapterDetail(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: ChapterType


class PromptType(BaseModel):
    label: str
    content: str = ''
    format: str = ''


class NovelType(BaseModel):
    label: str
    prompt: List[PromptType] = []


class NovelTypeList(BaseModel):
    success: bool = True
    message: str = "success"
    showType: str = "silent"
    data: List[NovelType] = []


BOOK_PATH = './books'


# 创建书籍目录和配置文件
def create_books_dir() -> None:
    config_file_path = os.path.join(BOOK_PATH, "config.json")
    if (not os.path.exists(BOOK_PATH)) or (not os.path.exists(config_file_path)):
        os.mkdir(BOOK_PATH)
        with open(config_file_path, "w") as f:
            f.write(json.dumps([]))


def save_books(books: List[BookType]) -> bool:
    # 保存到 config.json
    config_file_path = os.path.join(BOOK_PATH, "config.json")
    save_data = []
    for book in books:
        save_data.append(book.dict())

    with open(config_file_path, "w") as f:
        f.write(json.dumps(save_data, ensure_ascii=False, indent=4))

    return True


def get_books() -> List[BookType]:
    # 获取书籍列表
    create_books_dir()

    # 读取 config.json 文件
    config_file_path = os.path.join(BOOK_PATH, "config.json")
    with open(config_file_path, "r") as f:
        data = json.loads(f.read())
        books: List[BookType] = [BookType(**item) for item in data]

    return books


def get_book(book_id: str) -> BookType:
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    return book


def create_book() -> List[BookType]:
    # 新建书籍
    new_book = BookType(
        id=str(uuid.uuid4()),
        title="新书名",
        createdAt=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # 添加书籍配置
    books = get_books()
    books.append(new_book)

    save_books(books)

    return books


# 更新书籍
def update_book(book_id: str, new_config: BookType):
    # 更新书籍配置
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    # 更新书籍配置，如果没有传入则不更新
    book.title = new_config.title or book.title
    book.cover = new_config.cover or book.cover
    book.description = new_config.description or book.description
    book.summary = new_config.summary or book.summary
    book.characters = new_config.characters or book.characters
    book.chapters = new_config.chapters or book.chapters

    save_books(books)

    return book


def delete_book(book_id: str) -> List[BookType]:
    # 删除书籍
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    books.remove(book)
    save_books(books)

    return books


# 新建章节
def create_chapter(book_id: str, chapter: ChapterType) -> List[BookType]:
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    newChapter = ChapterType(
        id=str(uuid.uuid4()),
        title=chapter.title or "新章节名",
        summary=chapter.summary or "",
        content=chapter.content or "",
        paragraphs=chapter.paragraphs or [],
    )

    book.chapters.append(newChapter)

    save_books(books)

    return books


# 获取章节详情
def get_chapter(book_id: str, chapter_id: str) -> ChapterType:
    book = get_book(book_id)

    chapter = next((item for item in book.chapters if item.id == chapter_id))
    if not chapter:
        raise Exception('章节未找到')

    return chapter


# 更新章节
def update_chapter(book_id: str, chapter_id: str, chapter: ChapterType) -> List[BookType]:
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    oldChapter = next(
        (item for item in book.chapters if item.id == chapter_id))

    oldChapter.title = chapter.title or oldChapter.title
    oldChapter.content = chapter.content or oldChapter.content
    oldChapter.description = chapter.description or oldChapter.description
    oldChapter.summary = chapter.summary or oldChapter.summary
    oldChapter.paragraphs = chapter.paragraphs or []

    save_books(books)

    return books


# 删除章节
def delete_chapter(book_id: str, chapter_id: str) -> List[BookType]:
    books = get_books()
    book = next((item for item in books if item.id == book_id))
    if not book:
        Exception('书籍不存在')

    chapter = next(
        (item for item in book.chapters if item.id == chapter_id))

    book.chapters.remove(chapter)
    save_books(books)

    return books


# 保存小说类型
def save_novel_type(data: List[NovelType]) -> bool:
    novel_type_file = os.path.join(BOOK_PATH, "novel_type.json")

    save_data = []
    for item in data:
        save_data.append(item.dict())

    with open(novel_type_file, "w") as f:
        f.write(json.dumps(save_data, ensure_ascii=False, indent=4))

    return True


# 获取小说类型
def get_novel_types() -> List[NovelType]:
    novel_type_file = os.path.join(BOOK_PATH, "novel_type.json")

    if not os.path.exists(novel_type_file):
        return []

    with open(novel_type_file, "r") as f:
        data = json.loads(f.read())
        return [NovelType(**item) for item in data]


# 创建小说类型
def create_novel_type(novel_type: NovelType) -> List[NovelType]:
    data = get_novel_types()

    data.append(novel_type)
    save_novel_type(data)

    return data


# 更新小说类型
def update_novel_type(id: str, novel_type: NovelType) -> List[NovelType]:
    data = get_novel_types()
    old_novel_type = next((item for item in data if item.label == id))
    if not old_novel_type:
        raise Exception('小说类型不存在')

    old_novel_type.label = novel_type.label or old_novel_type.label
    old_novel_type.prompt = novel_type.prompt or old_novel_type.prompt
    save_novel_type(data)

    return data


# 删除小说类型
def delete_novel_type(label: str) -> List[NovelType]:
    data = get_novel_types()
    novel_type = next((item for item in data if item.label == label))
    if not novel_type:
        raise Exception('类型不存在')

    data.remove(novel_type)
    save_novel_type(data)

    return data
