import asyncio
# from pyppeteer import launch
# from pyppeteer_stealth import stealth
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

from bs4 import BeautifulSoup
import time
import json
import re


class Dcard:

    def __init__(self, account: str, password: str, board: str, output: str) -> None:
        self.account = account
        self.password = password
        self.board = board
        self.output = output
        self.article_data = {}

    @staticmethod
    def post_href(board: str, id: str) -> str:
        return f"https://www.dcard.tw/f/{board}/p/{id}"

    @staticmethod
    async def get_raw_page(page):
        return BeautifulSoup(await page.content(), "html.parser")

    def get_article_urls(self, soup: str) -> list:
        article_urls = []

        raw_board_page_data = soup.find_all(
            "script", attrs={"id": "__NEXT_DATA__"})
        raw_board_page_data = json.loads(raw_board_page_data[0].text)

        data = raw_board_page_data['props']['initialState']['post']['data']

        for id, content in data.items():
            article_urls.append(Dcard.post_href(self.board, id))

        return article_urls

    async def extract_data(self, response):
        output = {}
        url = response.url
        if 'comments' in url:  # 根據需要的資料 URL 進行篩選
            data = await response.json()  # 使用 text() 方法獲取回應的文本內容
            # print(data)
            # print()
            id = re.findall(r"\d{5,20}", url)[0]  # 透過正則表達式取得文章 id
            output['id'] = id
            output['comments'] = []
            output['date'] = None
            try:
                if isinstance(data, dict):
                    comments = [d['content'] for d in data['items']]
                elif isinstance(data, list):
                    comments = [d['content'] for d in data]

                output['comments'] = comments
                output['date'] = datetime.strptime(
                    data['items'][-1]['updatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                pass

            self.article_data[id] = output

    async def go_to_dcard(self, playwright):
        firefox = playwright.firefox
        browser = await firefox.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.dcard.tw")

        # 不斷確認是否有使用人工的方式通過驗證
        while True:
            time.sleep(5)
            # 查看 page content 是否有 "人工驗證"
            human_verification = True
            if human_verification:
                break

        # 通過驗證後，填入帳號密碼

        # [Board] 進入目標頁面
        await page.goto(f"https://www.dcard.tw/f/{self.board}?latest=true")

        # [Board] 滾動頁面
        for _ in range(10):
            await page.evaluate('_ => {window.scrollBy(0, 3000);}')
            time.sleep(1)

        article_urls = self.get_article_urls(await Dcard.get_raw_page(page))

        for url in article_urls:
            try:
                id = re.findall(r"\d{5,20}", url)[0]
                page.on('response', self.extract_data)
                await page.goto(url)
                raw_article_content = await Dcard.get_raw_page(page)
                title = raw_article_content.find_all("h1")[0].text
                content = ""
                for c in raw_article_content.find_all("span"):
                    content += c.text

                if id not in self.article_data:
                    self.article_data[id] = {}

                self.article_data[id].update(
                    {"id": id, "content": content, "title": title, "url": url}
                )
                time.sleep(1)
            except:
                pass


    def get(self):

        async def main():
            async with async_playwright() as playwright:
                await self.go_to_dcard(playwright)
        
        asyncio.run(main())

        for article in self.article_data.values():
            yield article


if __name__ == "__main__":

    dcard = Dcard("no required", "no required",
                  "creditcard", "dcard-creditcard")
    
    output = []

    for article in dcard.get():
        print(article)
        output.append(article)
    
    pd.DataFrame(output).to_excel(f"test.xlsx", index=False, columns=["id", "date", "url", "title", "content", "comments"])

    # async def main():
    #     async with async_playwright() as playwright:
    #         await dcard.get(playwright)

    # asyncio.run(main())
