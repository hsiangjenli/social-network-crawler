import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import time

def OnlyOnePageErrorHander(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return 1
    return wrapper


class Mobile01:

    def __init__(self, board: str, crawler_pages: int, sleep: float=0.5) -> None:
        """
        Parameters
        ----------
        board : str
            討論版代號，以「信用卡與消費」為例
            - `801` 為「信用卡與消費」討論版的代號
            - `p=1` 為第一頁
            
            ```python
            https://www.mobile01.com/topiclist.php?f=801&p=1
            ```
        crawler_pages : int
            總共要爬幾頁
        sleep : float, optional
            避免太過快速的對對方的網站請求，在每次爬完文章後的休息時間, by default 0.5
        """
        self.board = board
        self.crawler_pages = crawler_pages
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


    def get_article_urls(self, soup: str) -> str:
        """
        尋找爬蟲目標首頁的所有討論文章 URL
        
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位
        """
        css_name = "c-listTableTd__title"
        articles = soup.find_all("div", attrs={"class": css_name})
        article_urls = [article.a['href'] for article in articles]
        return article_urls
    

    @staticmethod
    def get_article_title(soup: str) -> str:
        """
        尋找文章的 title
        """
        return soup.find_all("h1")[0].text.replace("\n", "").strip()
    

    @staticmethod
    def get_article_datetime(soup: str) -> str:
        """
        尋找文章的發布日期
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位
        """
        css_name = "o-fNotes o-fSubMini"
        dt = soup.find_all("span", attrs={"class": css_name})[0].text.replace("\n", "").strip()
        return datetime.strptime(dt, "%Y-%m-%d %H:%M")
    

    @staticmethod
    def get_article_content(soup: str) -> str:
        """
        尋找文章的內文
        Parameters
        ----------
        itemprop : str
            文章頁面的定位名稱
        """
        return soup.find("div", attrs={"itemprop": "articleBody"}).text.replace("\n", "").strip()
    

    @staticmethod
    def get_article_comments(soup: str) -> list:
        """
        尋找文章的下方的回覆
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位
        """
        css_name = "u-gapBottom--max c-articleLimit"
        comments = []
        for i in soup.find_all("article", attrs={"class": css_name}):
            comments.append(re.sub(r"\s+", "\n", i.text.strip().replace("\n", "")))

        return [line for comment in comments for line in comment.split("\n")]


    @staticmethod
    @OnlyOnePageErrorHander
    def get_article_last_page(soup: str) -> int:
        css_name = "l-pagination__page"
        pages = soup.find_all("li", attrs={"class": css_name})
        last_page = int(pages[-1].text.replace(" ", "").replace("\n", ""))
        return last_page    
    
    
    async def main(self, crawler_page):
        async with async_playwright() as playwright:
            results = []
            
            # 找出所有文章的連結 -------------------------------------------------------------------------------------- #
            browser = await playwright.firefox.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.board_url(self.board, crawler_page), wait_until="domcontentloaded")
            soup = BeautifulSoup(await page.content(), "html.parser")
            article_urls = self.get_article_urls(soup)
            # print(article_urls)
            # print(self.board_url(self.board, page))
            
            # 用迴圈進入每一篇文章 ------------------------------------------------------------------------------------- #
            for article_id in article_urls:

                page = await browser.new_page()
                await page.goto(Mobile01.article_url(article_id=article_id, page=1), wait_until="domcontentloaded")
                soup = BeautifulSoup(await page.content(), "html.parser")
               
                title = Mobile01.get_article_title(soup)
                datetime = Mobile01.get_article_datetime(soup)
                link = Mobile01.article_url(article_id=article_id, page=1)
                content = Mobile01.get_article_content(soup)
                many_pages_comments = []
                many_pages_comments.extend(Mobile01.get_article_comments(soup))
                await page.close()
                # print(article_id)

                
                # 每一篇文章都會有多頁的回覆，所以要用迴圈進入每一頁回覆 -------------------------------------------------------------------- #
                for c_page in range(2, Mobile01.get_article_last_page(soup)+1):
                    page = await browser.new_page()
                    await page.goto(Mobile01.article_url(article_id=article_id, page=c_page), wait_until="domcontentloaded")
                    soup = BeautifulSoup(await page.content(), "html.parser")
                    single_page_comments = Mobile01.get_article_comments(soup)
                    many_pages_comments.extend(single_page_comments)
                    await page.close()

                article_contents = {
                    "title": title,
                    "datetime": datetime,
                    "link": link,
                    "article_id": article_id,
                    "content": content,
                    "comments": many_pages_comments,
                }
                
                results.append(article_contents) 
                time.sleep(self.sleep)

            await browser.close()
            return results
            

    def get(self):
        for page in range(1, self.crawler_pages + 1):
            for content in asyncio.run(self.main(crawler_page=page)):
                yield content
        

if __name__ == "__main__":
    from tqdm import tqdm
    
    mobile01 = Mobile01(board=801, crawler_pages=1)
    for i in tqdm(mobile01.get()):
        print(i)