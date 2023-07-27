import asyncio
import time
from pyppeteer import launch
from bs4 import BeautifulSoup


class JSTemplate:

    """
    這個 class 是用來產生 **JavaScript** 的模板，以便在 pyppeteer 中使用
    """

    @staticmethod
    def account(account) -> str:
        """
        這個 function 會接收使用者的帳號，並回傳一段 JavaScript，這段 JavaScript 會將帳號填入 Facebook 的登入欄位中
        """

        return f"""
        () => {{document.getElementById('email').value = '{account}';}}
        """

    @staticmethod
    def password(password) -> str:
        """
        這個 function 會接收使用者的密碼，並回傳一段 JavaScript，這段 JavaScript 會將密碼填入 Facebook 的登入欄位中
        """
        return f"""
        () => {{document.getElementById('pass').value = '{password}';}}
        """

    @staticmethod
    def press_button_by_id(btn_id) -> str:
        """
        跟上面兩個 function 一樣，這個 function 會回傳一段 JavaScript，這段 JavaScript 會模擬使用者按下登入按鈕
        """

        return f"""
        () => {{
                document.getElementById('{btn_id}').dispatchEvent(new MouseEvent('click', {{
                    bubbles: true,
                    cancelable: true,
                    view: window
                }}));
            }}
        """

    @staticmethod
    def press_button_by_class(btn_class) -> str:
        """
        這個 function 會回傳一段 JavaScript，這段 JavaScript 主要是去模擬使用者按下「See more」按鈕
        """

        t1 = """() => {"""
        t2 = f"const elements = document.getElementsByClassName('{btn_class}');"
        t3 = """

            if (elements.length > 0) {
                for (let i = 0; i < elements.length; i++) {
                    const element = elements[i];
                    if (element.textContent.trim() === 'See more') {
                        element.dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                    }
                }
            }
        }
        """
        return t1 + t2 + t3


class Facebook:

    def __init__(self, account: str, password: str, board_name: str, board_id: str, hashtag: str) -> None:
        """

        Parameters
        ----------
        account : str
            接收使用者的帳號
        password : str
            接收使用者的密碼
        board_name : str
            臉書粉絲專頁的名稱
        board_id : str
            臉書粉絲專頁的 ID, 可以從網址中取得。例如: https://www.facebook.com/CowBaBanker，這個粉絲專頁的 ID 就是 CowBaBanker
        hashtag : str
            要爬取的 Hashtag，主要是用來區分不同的貼文，把貼文拆分開來
            例如: 有兩篇貼文，第一篇貼文的 Hashtag 是 `#靠北銀行員1111111`，第二篇貼文的 Hashtag 是 `#靠北銀行員2222222`。可以看到 Hashtag 是不同的，所以這兩篇貼文就會被拆分開來
            ```shell
            #靠北銀行員1111111
            這是第一篇貼文的內容
            #靠北銀行員2222222
            這是第二篇貼文的內容
            ```

        """
        self.board_name = board_name
        self.board_id = board_id
        self.hashtag = hashtag
        self.url = f"https://www.facebook.com/{board_id}"
        self.account = account
        self.password = password

    def regex_content(self) -> str:
        """
        這個 function 會回傳一段 regex，這段 regex 會用來**區分貼文的開頭與結尾**

        Example
        -------
        ```python
        #靠北銀行員\d{0,10}([\s\S]*?)(?=#靠北銀行員\d{10})
        ```
        這個正則表達式代表的意思是: 
        1. 貼文的開頭必須是 `#靠北銀行員`，後面可以接 0 ~ 10 個任意數字
        1. 接著是任意字元
        1. 最後結尾必須是 `#靠北銀行員`，後面接 0 ~ 10 個任意數字
        """

        content = self.hashtag + \
            "\d{0,10}([\s\S]*?)(?=" + self.hashtag + "\d{0,10})"

        return r"{}".format(content)

    def regex_hashtag(self) -> str:
        """
        這個 function 會回傳一段 regex，這段 regex 最後回傳的結果我們會用來當作**貼文的標題**
        """
        return r"{}".format(self.hashtag + "\d{0,10}")

    def get_see_more_class(self, soup: BeautifulSoup) -> str:
        """

        這個 function 會接收一個 BeautifulSoup 物件，並回傳「See more」按鈕的 class name

        Parameters
        ----------
        soup : BeautifulSoup
            已經使用 BeautifulSoup 解析過的 HTML

        Returns
        -------
        str
            回傳「See more」按鈕的 class name
        """
        for i in soup.find_all("div"):
            if i.text == "See more":
                class_name = " ".join(i['class'])
                return class_name

    async def launch_browser(self) -> None:
        """
        這個 function 會使用 pyppeteer 去模擬使用者登入 Facebook，並模擬使用者滾動頁面，最後將頁面的 HTML 使用 BeautifulSoup 解析後，逐一取得每一篇貼文的內容回傳

        Flow
        ----
        1. 使用 pyppeteer 去模擬使用者登入 Facebook
           - 模擬使用者輸入帳號、密碼
           - 模擬使用者按下登入按鈕
           - 稍微等待一下，讓網頁載入
        1. 使用 JavaScript 模擬使用者滾動頁面
           - 目的是為了讓網頁載入更多貼文
        1. 接者使用 BeautifulSoup 解析頁面 HTML
           - 會發現有些貼文會被折疊，必須要按下「See more」按鈕才會展開
           - 所以在此，會先找出「See more」按鈕的 class name
        1. 藉由先前找到的「See more」按鈕的 class name，使用 JavaScript 模擬使用者按下「See more」按鈕
           - 使用到的 JS 程式碼在 `JSTemplate.press_button_by_class`
           - 裡面有一個限制，就是這個按鈕的文字必須是「See more」，如果不是的話，就不會按下去
        1. 已經將所有貼文展開後，在使用 BeautifulSoup 解析頁面 HTML
        1. 臉書的貼文是以 `div` 標籤包起來的，且有一個屬性是 `dir="auto"`，所以可以使用這個屬性來找到貼文
           - 但有一個問題，就是這標籤並不是一個完整的貼文，而是把貼文裡面的每一行文字
           - 所以在這邊會使用 `find_all` 只能把網頁上所有的貼文抓下來
           - 但是不能區分這是哪一篇貼文
        1. 所以在這邊會使用 `regex` 來區分貼文
           - `Facebook.regex_content()` 來找出符合規則的開頭與結尾
           - `Facebook.regex_hashtag()` 來找出符合規則的貼文的標題
        1. 使用 `re.finditer` 來找出所有符合規則的貼文
           - 這個 function 會回傳一個 generator，所以可以使用 `for` 迴圈來取得每一篇貼文
        """

        # Init browser
        browser = await launch()
        page = await browser.newPage()

        await page.goto(self.url)

        # Fill account and password and press login button
        await page.evaluate(JSTemplate.account(self.account))
        await page.evaluate(JSTemplate.password(self.password))
        await page.evaluate(JSTemplate.press_button_by_id("loginbutton"))

        # Wait for page to load
        await page.waitForNavigation()

        # Scroll down to load more posts
        for _ in range(20):
            try:
                await page.evaluate('_ => {window.scrollBy(0, 1000);}')
                await page.waitFor(1000)
                # time.sleep(1)
            except:
                pass
            # Click "See more" button
            incomplete_soup = BeautifulSoup(await page.content(), "html.parser")
            see_more_class = self.get_see_more_class(incomplete_soup)
            await page.evaluate(JSTemplate.press_button_by_class(see_more_class))
        # Get page content

        # Use BeautifulSoup to parse page content
        complete_soup = BeautifulSoup(await page.content(), "html.parser")

        # Close browser
        await browser.close()

        return complete_soup

    def get(self) -> str:
        """
        Example
        -------
        ```python

        fb = Facebook(
            account=ACCOUNT, 
            password=PASSWORD, 
            board_name="靠北銀行員", 
            board_id="CowBaBanker", 
            hashtag="#靠北銀行員"
        )

        for post in fb.get():
            print(post)
        ```
        """

        complete_soup = asyncio.get_event_loop().run_until_complete(self.launch_browser())
        # Get all posts
        posts_texts = complete_soup.find_all("div", {"dir": "auto", "style": "text-align: start;"})
        combine_text = ""
        for post_text in posts_texts:
            combine_text += f"{post_text.text}\n"
        
        # using regex to split posts
        regex_content = self.regex_content()
        regex_hashtag = self.regex_hashtag()

        contents = re.finditer(regex_content, combine_text, re.MULTILINE)

        for content in contents:

            title = re.findall(regex_hashtag, content.group())
            content = content.group()
            for ht in title:
                content = content.replace(ht, "")

            yield {
                "title": "&".join(title),
                "content": content
            }
            

if __name__ == "__main__":
    import os
    import re
    import pandas as pd
    from dotenv import load_dotenv

    load_dotenv('.env')

    ACCOUNT = os.getenv("FB_ACCOUNT")
    PASSWORD = os.getenv("FB_PASSWORD")
    OUTPUT_FB = "fb_out_6"

    fb = Facebook(
        account=ACCOUNT, 
        password=PASSWORD, 
        board_name="靠北銀行員", 
        board_id="CowBaBanker", 
        hashtag="#靠北銀行員"
    )

    output = []
    
    for post in fb.get():
        print(post)
        output.append(post)
    
    pd.DataFrame(output).to_excel(f"{OUTPUT_FB}.xlsx")