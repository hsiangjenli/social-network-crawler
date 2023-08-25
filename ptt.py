import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Union, Dict

def EmptyConentHandler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return ""
    return wrapper


class PTT_BASE:
    home = "https://www.ptt.cc"
    board_and_page_url = "/bbs/{board}/index{page}.html"


class PTT:

    def __init__(self, board: str, crawler_pages: int=5, sleep: int=5) -> None:
        """
        Parameters
        ----------
        board : str
            討論版代號，以「Finance」為例
            - `Finance` : 為「Finance」討論版的代號
            ```python
            https://www.ptt.cc/bbs/Finance/index.html
            ```
        crawler_pages : int, optional
            總共要爬幾頁，由最後一頁往前算, by default 5
        sleep : int, optional
            避免太過快速的對對方的網站請求，在每次爬完文章後的休息時間, by default 5
        """
        self.board = board
        self.crawler_pages = crawler_pages
        self.sleep = sleep
    

    @staticmethod
    def full_url(board: str, page: int) -> str:
        return PTT_BASE.home + PTT_BASE.board_and_page_url.format(board=board, page=page)
    

    @staticmethod
    def get_raw_page(url: str) -> BeautifulSoup:
        return BeautifulSoup(requests.get(url).text, "html.parser")


    def get_last_page_number(self, soup: str) -> int:
        """
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位

        Returns
        -------
        int
            最後一頁的頁碼
        """
        re_page_number = r"\d+"
        css_name = "btn wide"
        for l in soup.find_all("a", attrs={"class": css_name}):
            if "上頁" in l.text:
                page_number = re.findall(re_page_number, l["href"])[0]
                return int(page_number) + 1


    def get_article_urls(self, soup: str) -> List[str]:
        """
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位

        Returns
        -------
        list
            所有文章的 URL
        """
        css_name = "title"
        article_urls = []
        for l in soup.find_all("div", attrs={"class": css_name}):
            if l.a:
                article_urls.append(PTT_BASE.home + l.a["href"])
        
        return article_urls
    

    # Following methods are for getting the content of the article ------------------------------
    @staticmethod
    def get_article_category(string) -> str:
        """
        Parameters
        ----------
        re_category : regex
            `r"\[(.*?)\]"` 用於尋找文章的分類，規則為用 `[` `]` 括起的文字視為分類  
            例如 [心得]、[問題]、[新聞] 等等

        Returns
        -------
        str
            分類，例如 [心得]、[問題]、[新聞] 等等
        """
        re_category = r"\[(.*?)\]"
        category = re.findall(pattern=re_category, string=string)
        
        if category:
            return category[0]
        
        return ""
    
    
    @staticmethod
    @EmptyConentHandler
    def get_article_content(soup: str) -> str:
        """
        Parameters
        ----------
        re_content : regex
            `r"(作者.{1,30}看板.{1,30}標題.{1,30}時間.{1,30}=?)[\s\S]+(?=※ 發信站:)"` 尋找符合該規則的內文  
            開頭：`作者` `看板` `標題` `時間` 
            結尾：`※ 發信站:`

        Returns
        -------
        str
            內文
        """
        re_content = r"(作者.{1,30}看板.{1,30}標題.{1,30}時間.{1,30}=?)[\s\S]+(?=※ 發信站:)"
        raw_content = soup.find_all("div", attrs={"class": "bbs-screen bbs-content"})[0].text
        matches = re.finditer(re_content, raw_content)

        for match in matches:
            full_content = match.group(0)
            meta_info = match.group(1)

        return full_content.replace(meta_info, "")
    

    @staticmethod
    def get_article_comments(soup: str) -> list:
        """
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位

        Returns
        -------
        list
            回覆的內容
        """
        css_name = "push"
        comments = []
        for comment in soup.find_all("div", attrs={"class": css_name}):
            comments.append(comment.text.replace("\n", ""))
        return comments
    

    @staticmethod
    def get_article_datetime(soup: str) -> str:
        """
        Parameters
        ----------
        css_name : str
            文章頁面的 css 名稱，用於定位

        Returns
        -------
        datetime
            發文時間
        """

        css_name = "article-meta-value"

        @EmptyConentHandler
        def find_datetime(dt):
            return datetime.strptime(dt.text, "%a %b %d %H:%M:%S %Y")
        
        datetime_candidates = soup.find_all("span", attrs={"class": css_name})
        
        for dt in datetime_candidates:
            if find_datetime(dt):
                return find_datetime(dt)
    
    
    @staticmethod
    @EmptyConentHandler
    def get_article_title(soup: str) -> str:
        """
        Parameters
        ----------
        property : str
            用於定位 title 的位置

        Returns
        -------
        str
            文章的標題
        """
        return soup.find("meta", attrs={"property": "og:title"})['content']


    def get_article_info(self, link, soup: str) -> dict:
        """
        Returns
        -------
        dict
            使用字典回傳文章的資訊
        """
        
        title    = PTT.get_article_title(soup)
        category = PTT.get_article_category(title)
        content  = PTT.get_article_content(soup)
        comments = PTT.get_article_comments(soup)
        datetime = PTT.get_article_datetime(soup)

        article_content = {
            "category": category,
            "title": title.replace(f"[{category}]", "").lstrip(),
            "datetime": datetime,
            "link": link,
            "article_id": link,
            "content": content,
            "comments": comments
        }

        return article_content


    def get(self):
        raw_index_page = self.get_raw_page(PTT.full_url(self.board, ""))
        last_page_number = self.get_last_page_number(raw_index_page)
        article_urls = []

        for page in range(last_page_number, last_page_number - self.crawler_pages, -1):
            raw_article_page = self.get_raw_page(PTT.full_url(self.board, page))
            article_urls.extend(self.get_article_urls(raw_article_page))
        
        for article_url in article_urls:
            raw_content_page = self.get_raw_page(article_url)
            article_info = self.get_article_info(link=article_url, soup=raw_content_page)
            yield article_info
            time.sleep(self.sleep)


if __name__ == "__main__":
    from tqdm import tqdm
    
    ptt = PTT(board="Bank_Service", crawler_pages=10, sleep=0.5)
    for article in tqdm(ptt.get()):
        print(article)