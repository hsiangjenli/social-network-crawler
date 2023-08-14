import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import time
import json


def CannotFindTextErrorHander(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return None
    return wrapper


def OnlyOnePageErrorHander(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return 1
    return wrapper


class Mobile01:

    def __init__(self, board: str, page: int, sleep: float=0.5) -> None:
        self.board = board
        self.page = page
        self.sleep = sleep

    @staticmethod
    def board_url(board: str, page: int) -> str:
        """
        爬蟲目標的首頁
        """
        return f"https://www.mobile01.com/topiclist.php?f={board}&p={page}"


    @staticmethod
    def article_url(article_id: str, page: int) -> str:
        """
        爬蟲目標的文章頁面
        """
        return f"https://www.mobile01.com/{article_id}&p={page}"


    # get data --------------------------------------------------------------------------------------- #
    @staticmethod
    def get_article_title(soup: str) -> str:
        return soup.find_all("h1")[0].text.replace("\n", "").strip()
    

    @staticmethod
    def get_article_datetime(soup: str) -> str:
        css_name = "o-fNotes o-fSubMini"
        dt = soup.find_all("span", attrs={"class": css_name})[0].text.replace("\n", "").strip()
        # print(dt)
        return datetime.strptime(dt, "%Y-%m-%d %H:%M")
    

    @staticmethod
    def get_article_content(soup: str) -> str:
        return soup.find("div", attrs={"itemprop": "articleBody"}).text.replace("\n", "").strip()
    

    @staticmethod
    def get_article_comments(soup: str) -> list:
        css_name = "u-gapBottom--max c-articleLimit"
        comments = []
        
        for i in soup.find_all("article", attrs={"class": css_name}):
            print(re.sub(r"\s+", "\n", i.text.strip().replace("\n", "")))
            comments.append(re.sub(r"\s+", "\n", i.text.strip().replace("\n", "")))

        return [line for comment in comments for line in comment.split("\n")]


    def get_article_urls(self, soup: str) -> str:
        css_name = "c-listTableTd__title"
        articles = soup.find_all("div", attrs={"class": css_name})
        article_urls = [article.a['href'] for article in articles]
        return article_urls
    

    @staticmethod
    @OnlyOnePageErrorHander
    def get_article_last_page(soup: str) -> int:
        css_name = "l-pagination__page"
        pages = soup.find_all("a", attrs={"class": css_name})
        last_page = int(pages[-1].text.replace(" ", "").replace("\n", ""))
        return last_page
    
    
    async def main(self, page):
        async with async_playwright() as playwright:
            
            # 找出所有文章的連結 -------------------------------------------------------------------------------------- #
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(self.board_url(self.board, page), wait_until="domcontentloaded")
            soup = BeautifulSoup(await page.content(), "html.parser")
            article_urls = self.get_article_urls(soup)
            
            # 用迴圈進入每一篇文章 ------------------------------------------------------------------------------------- #
            for article_id in article_urls:
                page = await browser.new_page()
                await page.goto(Mobile01.article_url(article_id=article_id, page=1), wait_until="domcontentloaded")
                soup = BeautifulSoup(await page.content(), "html.parser")
                with open("test_3.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
                print(1)
                title = Mobile01.get_article_title(soup)
                print(2)
                datetime = Mobile01.get_article_datetime(soup)
                print(3)
                link = Mobile01.article_url(article_id=article_id, page=1)
                content = Mobile01.get_article_content(soup)
                many_pages_comments = []
                
                # 每一篇文章都會有多頁的回覆，所以要用迴圈進入每一頁回覆 -------------------------------------------------------------------- #
                for c_page in range(2, Mobile01.get_article_last_page(soup)+1):
                    await page.goto(Mobile01.article_url(article_id=article_id, page=c_page), wait_until="domcontentloaded")
                    soup = BeautifulSoup(await page.content(), "html.parser")
                    print(soup)
                    single_page_comments = Mobile01.get_article_comments(soup)
                    many_pages_comments.extend(single_page_comments)

                article_contents = {
                    "title": title,
                    "datetime": datetime,
                    "link": link,
                    "article_id": article_id,
                    "content": content,
                    "comments": many_pages_comments,
                }

                yield article_contents
                time.sleep(self.sleep)


            await browser.close()

    async def get(self):
        results = []
        for i in range(1, self.page + 1):
            async for content in self.main(page=i):
                results.append(content)
        return results
        

if __name__ == "__main__":
    m = Mobile01(board=801, page=1)
    
    asyncio.run(m.get())