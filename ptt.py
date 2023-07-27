import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

class PTT_BASE:
    home = "https://www.ptt.cc"
    board_and_page_url = "/bbs/{board}/index{page}.html"

class PTT:

    def __init__(self, board: str, crawler_pages: int=5, sleep: int=5) -> None:
        self.board = board
        self.crawler_pages = crawler_pages
        self.sleep = sleep
    

    @staticmethod
    def full_url(board: str, page: int) -> str:
        return PTT_BASE.home + PTT_BASE.board_and_page_url.format(board=board, page=page)
    

    @staticmethod
    def get_raw_page(url: str) -> BeautifulSoup:
        """
        Hint
        ----
        - `raw_index_page` and `raw_article_page` are same format. We will only use these pages to get the urls of articles.
        - `raw_content_page` contains the content of the article, including the comments, date, author, etc.
        """
        return BeautifulSoup(requests.get(url).text, "html.parser")


    def get_last_page_number(self, soup: str) -> int:
        re_page_number = r"\d+"
        for l in soup.find_all("a", attrs={"class": "btn wide"}):
            if "上頁" in l.text:
                page_number = re.findall(re_page_number, l["href"])[0]
                return int(page_number) + 1


    def get_article_urls(self, soup: str) -> list:
        article_urls = []
        for l in soup.find_all("div", attrs={"class": "title"}):
            if l.a:
                article_urls.append(PTT_BASE.home + l.a["href"])
        
        return article_urls
    

    # Following methods are for getting the content of the article
    @staticmethod
    def get_article_category(string) -> str:
        re_category = r"\[(.*?)\]"
        category = re.findall(pattern=re_category, string=string)
        
        if category:
            return category[0]
        
        return ""
    

    @staticmethod
    def get_article_content(soup: str) -> str:
        re_content = r"(作者.{1,30}看板.{1,30}標題.{1,30}時間.{1,30}=?)[\s\S]+(?=※ 發信站:)"
        raw_content = soup.find_all("div", attrs={"class": "bbs-screen bbs-content"})[0].text
        matches = re.finditer(re_content, raw_content)
        # print(matches)

        for match in matches:

            full_content = match.group(0)
            meta_info = match.group(1)
        try:
            return full_content.replace(meta_info, "")
        except:
            pass
    

    @staticmethod
    def get_article_comments(soup: str) -> list:
        comments = []
        for comment in soup.find_all("div", attrs={"class": "push"}):
            comments.append(comment.text.replace("\n", ""))
        return comments
    

    @staticmethod
    def get_article_datetime(soup: str) -> str:
        datetime_candidates = soup.find_all("span", attrs={"class": "article-meta-value"})
        for dt in datetime_candidates:
            try:
                return datetime.strptime(dt.text, "%a %b %d %H:%M:%S %Y")
            except:
                pass
    

    def get_article_info(self, link, soup: str) -> dict:

        title = soup.find("meta", attrs={"property": "og:title"})['content']
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
    ptt = PTT(board="Finance", crawler_pages=2)
    for article in ptt.get():
        print(article)