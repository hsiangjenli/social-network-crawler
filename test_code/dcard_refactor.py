import asyncio

from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

from bs4 import BeautifulSoup
import time
import json

from fake_useragent import UserAgent

import re


class DcardHelper:

    @staticmethod
    def board_url(board: str) -> str:
        return f"https://www.dcard.tw/f/{board}?latest=true"
    
    @staticmethod
    def post_url(board: str, id: str) -> str:
        return f"https://www.dcard.tw/f/{board}/p/{id}"
    
    @staticmethod
    def fake_header() -> str:
        ua = UserAgent(browsers=['firefox'], os='windows', min_percentage=1.3)
        return ua.random


class Dcard:

    def __init__(self, board: str, scroll_down: int, log_dir: str) -> None:
        self.board = board
        self.scroll_down = scroll_down
        self.log_dir = log_dir
        self.articles = {}
        self.articles_failed = [] # 紀錄哪些文章沒爬到

    
    async def go_to_dcard(self, robot):
        # 開啟瀏覽器，並前往 Dcard
        firefox = robot.firefox
        browser = await firefox.launch(headless=False)
        page = await browser.new_page()
        # page.set_extra_http_headers(DcardHelper.fake_header())
        await page.goto("https://www.dcard.tw")

        time.sleep(1000)
        await browser.close()
    
    # 最後批次回傳爬完的結果
    def get(self):

        # 主要爬蟲的程式碼 ---------------------------------------------------------------
        async def main_func():
            async with async_playwright() as robot:
                await self.go_to_dcard(robot)
        
        asyncio.run(main_func())

        # 將爬完的結果回傳，同時如果有某些文章這次因為防爬蟲機制沒爬到，要回傳哪些文章沒爬到 ---
        for article in self.articles.values():
            yield article

if __name__ == "__main__":
    # 設定爬蟲參數
    board = "creditcard"
    scroll_down = 2
    log_dir = "log"

    # 執行爬蟲
    dcard = Dcard(board, scroll_down, log_dir)
    for article in dcard.get():
        print(article)
