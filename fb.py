import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup

class JSTemplate:

    @staticmethod
    def account(account) -> str:
        
        return f"""
        () => {{document.getElementById('email').value = '{account}';}}
        """


    @staticmethod
    def password(password) -> str:
        
        return f"""
        () => {{document.getElementById('pass').value = '{password}';}}
        """


    @staticmethod
    def press_button_by_id(btn_id) -> str:
        
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

    def __init__(self, account, password, output) -> None:
        self.url = "https://www.facebook.com/CowBaBanker"
        self.account = account
        self.password = password
        self.output = output
    
    
    def get_see_more_class(self, soup) -> str:
        for i in soup.find_all("div"):
            if i.text == "See more":
                class_name = " ".join(i['class'])
                return class_name
        


    async def get(self) -> str:
        
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
        for i in range(10):
            await page.evaluate('_ => {window.scrollBy(0, 1000);}')
            await page.waitFor(1000)

        # Get page content
        incomplete_soup = BeautifulSoup(await page.content(), "html.parser")

        # Click "See more" button
        see_more_class = self.get_see_more_class(incomplete_soup)
        await page.evaluate(JSTemplate.press_button_by_class(see_more_class))


        await page.screenshot({'path': f"{self.output}.png"}, fullPage=True)
        
        with open(f"{self.output}.txt", "w", encoding="utf-8") as f:
            f.write(await page.content())


if __name__ == "__main__":
    import os
    import re
    import pandas as pd
    from dotenv import load_dotenv
    load_dotenv('.env')

    ACCOUNT = os.getenv("FB_ACCOUNT")
    PASSWORD = os.getenv("FB_PASSWORD")
    OUTPUT_FB  = "fb_out"

    fb = Facebook(account=ACCOUNT, password=PASSWORD, output=OUTPUT_FB)
    asyncio.get_event_loop().run_until_complete(fb.get())


    with open(f"{OUTPUT_FB}.txt", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    all_text = ""
    for i in soup.find_all("div", {"dir": "auto", "style": "text-align: start;"}):
        all_text += f"{i.text}\n"

    output_dict = {}

    regex_content = r"#靠北銀行員\d{0,10}([\s\S]*?)(?=#靠北銀行員\d{5})"
    regex_hashtag = r"#靠北銀行員\d{0,10}"

    contents = re.finditer(regex_content, all_text, re.MULTILINE)

    for content in contents:

        title = re.findall(regex_hashtag, content.group())
        content = content.group()
        for ht in title:
            content = content.replace(ht, "")

        output_dict["&".join(title)] = content

    pd.DataFrame([output_dict]).T.to_excel(f"{OUTPUT_FB}.xlsx")