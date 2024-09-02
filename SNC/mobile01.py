import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime
import time

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
    """_summary_

    Args:
        board (str): _description_
        crawler_pages (int): _description_
        sleep (float, optional): _description_. Defaults to 0.5.
    """
    def __init__(self, board: str, crawler_pages: int, sleep: float=0.5) -> None:

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


    # get data --------------------------------------------------------------------------------------- #
    @staticmethod
    @CannotFindTextErrorHander
    def get_article_title(soup: str) -> str:
        return soup.find_all("h1")[0].text.replace("\n", "").strip()
    

    @staticmethod
    @CannotFindTextErrorHander
    def get_article_datetime(soup: str) -> str:
        css_name = "o-fNotes o-fSubMini"
        dt = soup.find_all("span", attrs={"class": css_name})[0].text.replace("\n", "").strip()
        return datetime.strptime(dt, "%Y-%m-%d %H:%M")
    

    @staticmethod
    @CannotFindTextErrorHander
    def get_article_content(soup: str) -> str:
        return soup.find("div", attrs={"itemprop": "articleBody"}).text.replace("\n", "").strip()
    

    @staticmethod
    @CannotFindTextErrorHander
    def get_article_comments(soup: str) -> list:
        css_name = "u-gapBottom--max c-articleLimit"
        comments = []
        for i in soup.find_all("article", attrs={"class": css_name}):
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
            
            # 用迴圈進入每一篇文章 ------------------------------------------------------------------------------------- #
            for article_id in article_urls:

                print(f"Crawling {Mobile01.article_url(article_id=article_id, page=1)}")

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
    m = Mobile01(board=801, crawler_pages=2)
    for i in m.get():
        print(i)