import os
import json
import time
import pickle
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIE_FILE = "jd_cookies.pkl"
LOGIN_URL = "https://passport.jd.com/new/login.aspx"
TARGET_URL = "https://details.jd.com/normal/item.action?orderid=327390369995&PassKey=C8C57472349BAAE9AC22FB506A24186E#none"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def save_cookies(driver, path):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    with open(path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

def login_and_save_cookie():
    options = Options()
    options.add_experimental_option('detach', True)
    driver = webdriver.Chrome(options=options)
    driver.get(LOGIN_URL)

    print("请在打开的浏览器中手动完成登录...")
    WebDriverWait(driver, 300).until(lambda d: "我的订单" in d.page_source)
    save_cookies(driver, COOKIE_FILE)
    print("登录成功，Cookies 已保存")
    driver.quit()

def get_valid_cookies():
    if not os.path.exists(COOKIE_FILE):
        login_and_save_cookie()

    session = requests.Session()
    session.headers.update(HEADERS)

    # 模拟浏览器添加 Cookie
    with open(COOKIE_FILE, 'rb') as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

    return session

def fetch_logistics_info():
    session = get_valid_cookies()
    response = session.get(TARGET_URL)

    if "请登录" in response.text:
        print("Cookie 已失效，重新登录获取...")
        login_and_save_cookie()
        session = get_valid_cookies()
        response = session.get(TARGET_URL)

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all('li', class_='afterdate')

    if not items:
        print("未找到物流信息，请确认订单有效且已发货")
        return

    for i, item in enumerate(items, 1):
        date = item.find('span', class_='date')
        time_tag = item.find('span', class_='time')
        txt = item.find('span', class_='txt')
        print(f"[{i}] {date.get_text(strip=True) if date else ''} {time_tag.get_text(strip=True) if time_tag else ''}")
        print(f"     {txt.get_text(strip=True) if txt else ''}\n")

if __name__ == '__main__':
    fetch_logistics_info()
