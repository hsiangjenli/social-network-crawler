import asyncio

from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

from bs4 import BeautifulSoup
import time
import json
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
            'Referer': 'https://www.dcard.tw/f',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6',
            # 'Cookie': '_fbp=fb.1.1668262182332.69274538; CFFPCKUUID=1025-92ayqvQMNaNszVCdOs96CXLMF0RlWLOE; __htid=3853f36e-f271-4131-ae55-2a47c9efcf74; CFFPCKUUIDMAIN=4025-oo5Z14O14J7dKBMiPGXH0hFrNoJcNgPc; FPUUID=4025-683c43ab57e5286c8502cee43fd051270bf43bbd2ba10279e77c00826c03da69; _ga_C3J49QFLW7=GS1.1.1681825326.213.0.1681825326.0.0.0; _fbc=fb.1.1683904854194.IwAR2uqY9sDKrzePh5WE_yKP80XWKG-CQ01pt5S__dKxVoBTSnPoTxLbpKV6s; _gcl_au=1.1.610574737.1684140290; _ga=GA1.1.762610775.1668262182; __gpi=UID=00000b85a5a0fd3f:T=1669690404:RT=1690281985:S=ALNI_MZ7-LXgQOCc07s3pFIdyAWstAE2Rg; _cfuvid=cRrOsPu..uQ1CUKbjPhtSFbmR5q7AAt3Ww73SLsCPwQ-1690736092776-0-604800000; CFFPCKUUID=1025-92ayqvQMNaNszVCdOs96CXLMF0RlWLOE; _ht_hi=1; __cf_dm=YWRtaW46MDox.721.crc.cf4dca1e; dcsrd=rU14xtZw-OhUipRIGltWVgmP; __gads=ID=7256ae945d22624e:T=1669690404:RT=1690750026:S=ALNI_Ma1TRnKAO_XW0O_Y78vIBriwtTz-A; cto_bundle=Bq_mGF8xTjBsUWNRSUslMkZGSWJCRkJnYlJ6NEVMbEJRdllqRHlNWFVNZ245bkFvd0RHUDZaYU1PNXhwNW1admJEaFlKOUFpWU5WSG1zb1hCZlNQbFlhdEpJUFBRdXljeVJ4byUyQkN2S2F3cEg4dE9Za1luclZKU3lXRnhBWENXNW04bmk0eWc; dcard-web-oauth-tk=eyJhY2Nlc3NUb2tlbiI6ImV5SmhiR2NpT2lKRlpFUlRRU0lzSW10cFpDSTZJbEpMTFVoZlRUUm9VVkpET1dzeFUxcEdZMEZ1UkRBMVZreFljV1JZUm1kUVZYQXdWbGx0YjJ4eWFqZzlJbjAuZXlKaGNIQWlPaUpqTW1VM05qTTVOUzB6T0dFeExUUTRaamN0WVRsbE1DMWhaamN6TldJNFpqZGpOREVpTENKbGVIQWlPakUyT1RBM09EazRNVGtzSW1saGRDSTZNVFk1TURjNE9Ea3hPU3dpYVhKMElqb2lOMlkzTlROa1pqRXRNVEV4TnkwME1HVTNMVGxtTlRrdE4yRmtPR0l4TmpBM056RTBJaXdpYVhOeklqb2laR05oY21RaUxDSnFkR2tpT2lKaU1ETXhNVGxrTWkwd01HWTVMVFF4TUdRdFlXUTBZeTA1TW1FMU5XUTVPR0U0Tm1VaUxDSnpZMjl3WlhNaU9sc2liV1Z0WW1WeUlpd2liV1Z0WW1WeU9uZHlhWFJsSWl3aVpXMWhhV3dpTENKbGJXRnBiRHAzY21sMFpTSXNJbVJsZG1salpTSXNJbVJsZG1salpUcDNjbWwwWlNJc0luQm9iM1J2SWl3aWJtOTBhV1pwWTJGMGFXOXVJaXdpWm05eWRXMGlMQ0ptYjNKMWJUcHpkV0p6WTNKcFltVWlMQ0p3YjNOMElpd2ljRzl6ZERwemRXSnpZM0pwWW1VaUxDSm1ZV05sWW05dmF5SXNJbkJvYjI1bElpd2ljR2h2Ym1VNmRtRnNhV1JoZEdVaUxDSndhRzl1WlRwM2NtbDBaU0lzSW5CbGNuTnZibUVpTENKd1pYSnpiMjVoT25OMVluTmpjbWxpWlNJc0ltTnZibVpwWnlJc0ltTnZibVpwWnpwM2NtbDBaU0lzSW5SdmEyVnVPbkpsZG05clpTSXNJbWxrWTJGeVpDSXNJblJ2Y0dsaklpd2lkRzl3YVdNNmMzVmljMk55YVdKbElpd2labVZsWkRwemRXSnpZM0pwWW1VaUxDSmpiMnhzWldOMGFXOXVJaXdpWTI5c2JHVmpkR2x2YmpwM2NtbDBaU0lzSW1aeWFXVnVaQ0lzSW1aeWFXVnVaRHAzY21sMFpTSXNJbTFsYzNOaFoyVWlMQ0p0WlhOellXZGxPbmR5YVhSbElpd2lhV1JsYm5ScGRIazZkbUZzYVdSaGRHVmtJaXdpYkdsclpTSXNJbkpsWVdOMGFXOXVJaXdpY0c5emREcDNjbWwwWlNJc0ltTnZiVzFsYm5RNmQzSnBkR1VpTENKeVpYQnZjblFpTENKc2IyZHBibFpsY21sbWFXTmhkR2x2YmlJc0lteHZaMmx1Vm1WeWFXWnBZMkYwYVc5dU9uWmxjbWxtZVNJc0luQmxjbk52Ym1FNmQzSnBkR1VpTENKdFpYTnpZV2RsT25CeWFYWmhkR1VpTENKd2IyeHNPbmR5YVhSbElpd2laRzkzYm5admRHVWlYU3dpYzJsa0lqb2lPVFExTmpCbE4yTXRNV0V5WkMwMFlUWmtMV0kxTUdNdE5tRmpZbU14WldFellqVXlJaXdpYzNWaUlqb2lNelU0TURJMk15SjkuQS1WZGJpYkxrV1JfRlRIOE5KS1BDSFJzeUM2aXdMR2x4SU8zQ1lDY1FEcVZmWkpmWnNDZWt1eUJuczl4bUhKbjZrc2p1R21Ld1k3Nk9RT19TdDVoQmciLCJ0b2tlblR5cGUiOiJCZWFyZXIiLCJyZWZyZXNoVG9rZW4iOiJaLzNVMFp1U1M1ZUNBY3NCblhLVjFnPT0iLCJleHBpcmVzQXQiOiIyMDIzLTA3LTMxVDA3OjUwOjE5LjAwMFoifQ==; dcard-web-oauth-tk.sig=Y_IG8DsJ8q7PxfdJ9F3UzIYgWYE; cf_clearance=BP5YRAhM6S14KPPetAeR_B67tFwNmcvKQQofkgc2RJ8-1690788930-0-0.2.1690788930; _ga_DSM1GSYX4C=GS1.1.1690788928.446.1.1690788961.27.0.0; __cf_bm=JK8ZgGLJqqgdbnB9ZW_HgclGV07_pCm2tfexjzMUElA-1690788963-0-ATyRg42GfwA9nUMClIkVpPA9FYh+rC+1fBRXg6tx7og4pYYByjMhGPgBV8OJSbTKnmyMzDaMgDJQWu4YxzUva3w='
        }
        return headers


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

        time.sleep(30)
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
