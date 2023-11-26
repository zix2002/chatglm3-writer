'''
书籍目录相关操作
'''

import os
import json

from typing import List
# 书籍目录
BOOKS_PATH = './books'
DEFAULT_BOOK_CONFIG = {
    "title": "新书名",
    "author": "",
    "words": "1",
    "bookType": "都市言情",
    "description": "",
    "characters": [],
    "chapters": [],
}


def check_books_dir():
    # 检查书籍目录是否存在，如果不存在就创建
    if not os.path.exists(BOOKS_PATH):
        os.mkdir(BOOKS_PATH)


def check_book_dir(book_name: str):
    # 检查书籍目录是否存在，如果不存在就创建
    check_books_dir()
    book_path = os.path.join(BOOKS_PATH, book_name)
    book_config_path = os.path.join(book_path, "config.json")
    # 如果书籍目录不存在，就创建目录和配置文件
    if not os.path.exists(book_path):
        raise Exception("书籍不存在")
        # os.mkdir(book_path)

    # 如果书籍配置文件不存在，就创建
    if not os.path.exists(book_config_path):
        with open(book_config_path, "w") as f:
            f.write(json.dumps(DEFAULT_BOOK_CONFIG))


def get_book_chapters(book_name: str):
    # 获取书籍章节
    check_books_dir()
    check_book_dir(book_name)
    book_path = os.path.join(BOOKS_PATH, book_name)
    files = os.listdir(book_path)
    chapters: List = []
    for file in files:
        if file.endswith(".txt"):
            name = file.split(".")[0]
            chapters.append({
                "chapter": name.split(" ")[0],
                "title": name.split(" ")[1],
            })
    return chapters


def get_book_config(book_name: str):
    # 获取书籍配置
    check_books_dir()
    check_book_dir(book_name)

    # 读取配置文件
    book_path = os.path.join(BOOKS_PATH, book_name)
    with open(os.path.join(book_path, "config.json"), "r") as f:
        book_config = json.loads(f.read())
        book_config.update({"chapters": get_book_chapters(book_name)})

    return book_config


def get_books_list():
    # 获取书籍列表
    check_books_dir()
    books_dir = os.listdir(BOOKS_PATH)

    # 书籍列表
    books: List = []

    # 遍历目录，获取书籍列表
    for i, book in enumerate(books_dir):
        books.append(get_book_config(book))

    return books


def create_book(book_name: str):
    # 创建书籍
    book_path = os.path.join(BOOKS_PATH, book_name)
    if not os.path.exists(book_path):
        os.mkdir(book_path)
        with open(os.path.join(book_path, "config.json"), "w") as f:
            f.write(json.dumps(DEFAULT_BOOK_CONFIG))
    else:
        raise Exception("书籍已存在")


def get_chapter(book_name: str, chapter: str):
    # 获取章节内容
    chapters = get_book_chapters(book_name)
    chapter_detail = None
    for c in chapters:
        if c["chapter"] == chapter:
            chapter_detail = c

    if not chapter_detail:
        raise Exception("章节不存在")

    return chapter_detail


def create_chapter(book_name: str, chapter: str, title: str):
    # 创建章节
    book_path = os.path.join(BOOKS_PATH, book_name)
    chapter_path = os.path.join(book_path, f"{chapter} {title}.txt")
    if not os.path.exists(chapter_path):
        with open(chapter_path, "w") as f:
            f.write("")
    else:
        raise Exception("章节已存在")

    return get_chapter(book_name, chapter)


def update_chapter(book_name: str, chapter: str, title: str, content: str, update_type: str = "w"):
    # 更新章节
    book_path = os.path.join(BOOKS_PATH, book_name)
    chapter_path = os.path.join(book_path, f"{chapter} {title}.txt")
    if os.path.exists(chapter_path):
        with open(chapter_path, update_type) as f:
            f.write(content)
    else:
        raise Exception("章节不存在")

    return get_chapter(book_name, chapter)


def delete_chapter(book_name: str, chapter: str):
    # 删除章节
    book_path = os.path.join(BOOKS_PATH, book_name)
    chapter_path = os.path.join(book_path, f"{chapter}.txt")
    if os.path.exists(chapter_path):
        os.remove(chapter_path)
    else:
        raise Exception("章节不存在")

    return get_book_chapters(book_name)
