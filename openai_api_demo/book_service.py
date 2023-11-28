from __future__ import unicode_literals
from calendar import c
import os
import json
from typing import List, Optional, Dict
from pydantic import BaseModel
from regex import B


class CharacterCard(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""


class ChapterCard(BaseModel):
    title: str = ""
    content: str = ""


class BookCard(BaseModel):
    title: str
    cover: str = ""
    author: str = ""
    words: str = ""
    bookType: str = ""
    description: str = ""
    characters: List[CharacterCard] = []
    chapters: List[ChapterCard] = []


# 书籍目录
BOOKS_PATH = './books'

# 默认书籍配置
DEFAULT_BOOK_CONFIG = {
    "title": "新书名",
    "author": "",
    "words": "",
    "bookType": "",
    "description": "",
    "characters": [],
    "chapters": [],
}


def create_books_dir() -> None:
    # 检查书籍目录是否存在，如果不存在就创建
    if not os.path.exists(BOOKS_PATH):
        os.mkdir(BOOKS_PATH)

    # 检查 config.json 是否存在，如果不存在就创建
    config_path = os.path.join(BOOKS_PATH, "config.json")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(json.dumps([]))


def create_book_dir(book_name: str) -> None:
    # 检查书籍目录是否存在，如果不存在就创建
    create_books_dir()
    book_path = os.path.join(BOOKS_PATH, book_name)
    # 如果书籍目录不存在，就创建目录和配置文件
    if not os.path.exists(book_path):
        os.mkdir(book_path)


def get_book_chapters(book_name: str):
    pass
    # 获取书籍章节
    # check_books_dir()
    # check_book_dir(book_name)
    # book_path = os.path.join(BOOKS_PATH, book_name)
    # files = os.listdir(book_path)
    # chapters: List = []
    # for file in files:
    #     if file.endswith(".txt"):
    #         name = file.split(".")[0]
    #         chapters.append({
    #             "chapter": name.split(" ")[0],
    #             "title": name.split(" ")[1],
    #         })
    # return chapters


def save_books_config(books):
    # 保存书籍列表 config.json
    config_path = os.path.join(BOOKS_PATH, "config.json")

    with open(config_path, "w") as f:
        f.write(json.dumps(books, ensure_ascii=False))


def get_books():
    # 获取书籍列表
    create_books_dir()
    config_path = os.path.join(BOOKS_PATH, "config.json")
    # 读取 config.json 文件并返回
    with open(config_path, "r") as f:
        books = json.loads(f.read())
    return books


def get_book_by_name(book_name: str):
    # 获取书籍配置
    books = get_books()
    # 读取配置文件
    for book in books:
        if book["title"] == book_name:
            return book
    return None


def get_book_by_index(index: int):
    # 根据小标获取书籍配置
    books = get_books()

    if index < len(books):
        return books[index]

    return None


def create_book(config):
    print(config)

    # 创建书籍
    book_config = {**DEFAULT_BOOK_CONFIG, **config}
    book_name = book_config["title"]

    # 检查书籍是否在 config.json 中存在
    if get_book_by_name(book_name):
        raise Exception("书籍已存在")

    books = get_books()
    books.append(book_config)

    # 保存书籍列表 config.json
    save_books_config(books)

    # 创建书籍目录
    create_book_dir(book_name)

    # 返回刚创建的书籍
    return book_config


def update_book(index: int, config):
    # 保存指定书名的书籍配置
    books = get_books()
    if index >= len(books):
        raise Exception("书籍不存在")

    if (books[index]["title"] != config["title"]):
        # 修改书籍目录名
        old_book_path = os.path.join(BOOKS_PATH, books[index]["title"])
        new_book_path = os.path.join(BOOKS_PATH, config["title"])
        os.rename(old_book_path, new_book_path)

    books[index].update(config)

    # 保存书籍列表 config.json
    save_books_config(books)
    return config


def delete_book(index: int):
    # 删除指定书名的书籍配置
    books = get_books()
    if index >= len(books):
        raise Exception("书籍不存在")

    # 删除书籍目录
    book_path = os.path.join(BOOKS_PATH, books[index]["title"])
    os.rmdir(book_path)

    # 删除 config.json 中的书籍配置
    del books[index]

    # 保存书籍列表 config.json
    save_books_config(books)
    return books


def get_chapters_by_book_index(book_index: int):
    # 获取书籍人物列表
    book = get_book_by_index(book_index)
    if not book:
        return []
    return book["chapters"]


def get_chapter_content_by_index(book_name: str, chapter_name: str):
    # 获取章节内容
    chapter_path = os.path.join(BOOKS_PATH, book_name, chapter_name + ".txt")
    if not os.path.exists(chapter_path):
        return ''

    with open(chapter_path, "r") as f:
        return f.read()


def get_chapter(book_index: int, chapter_index: int):
    # 获取章节详情
    book = get_book_by_index(book_index)
    if not book:
        raise Exception("书籍不存在")

    chapters = get_chapters_by_book_index(book_index)
    if chapter_index >= len(chapters):
        raise Exception("章节不存在")

    chapter = chapters[chapter_index]
    chapter.update(content=get_chapter_content_by_index(
        book["title"], chapter["title"]))

    return chapter


def save_chapter_content(book_name: str, chapter_name: str, content: str):
    # 保存章节内容
    chapter_path = os.path.join(BOOKS_PATH, book_name, chapter_name + ".txt")

    with open(chapter_path, "w") as f:
        f.write(content)


def create_chapter(book_index: int, chapter):
    # 创建章节
    book = get_book_by_index(book_index)
    if not book:
        raise Exception("书籍不存在")

    book_name = book["title"]
    chapter_title = chapter["title"]
    chapter_content = chapter["content"]

    chapter.update(content="")
    book["chapters"].append(chapter)

    # 保存书籍列表 config.json
    update_book(book_index, book)
    save_chapter_content(book_name, chapter_title, chapter_content)

    return book


def update_chapter(book_index: int, chapter_index: int, chapter):
    # 更新章节
    book = get_book_by_index(book_index)
    if not book:
        raise Exception("书籍不存在")

    if chapter_index >= len(book['chapters']):
        raise Exception("章节不存在")

    book_name = book["title"]
    chapter_title = chapter["title"]
    chapter_content = chapter["content"]
    chapter.update(content="")

    old_chapter_title = book["chapters"][chapter_index]["title"]
    book["chapters"][chapter_index].update(chapter)

    update_book(book_index, book)

    if chapter_title != old_chapter_title:
        # 修改章节文件名
        old_chapter_path = os.path.join(
            BOOKS_PATH, book_name, old_chapter_title + ".txt")
        new_chapter_path = os.path.join(
            BOOKS_PATH, book_name, chapter_title + ".txt")
        os.rename(old_chapter_path, new_chapter_path)

    save_chapter_content(book_name, chapter_title, chapter_content)

    return book


def delete_chapter(book_index: int, chapter_index: int):
    # 删除章节
    book = get_book_by_index(book_index)
    if not book:
        raise Exception("书籍不存在")

    if chapter_index >= len(book['chapters']):
        raise Exception("章节不存在")

    book_name = book["title"]
    chapter_title = book["chapters"][chapter_index]["title"]

    book["chapters"].pop(chapter_index)
    update_book(book_index, book)

    # 删除章节文件
    chapter_path = os.path.join(BOOKS_PATH, book_name, chapter_title + ".txt")
    os.remove(chapter_path)

    return book
