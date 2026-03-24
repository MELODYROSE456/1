# translator.py - 翻译模块
import urllib.parse
import requests
import time

class Translator:
    def __init__(self, email="your.email@example.com"):
        self.session = requests.Session()
        self.email = email
    
    def translate(self, text):
        """翻译英文为中文"""
        if not text or any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
        
        try:
            encoded = urllib.parse.quote(text[:500])  # 限制长度
            url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|zh-CN&email={self.email}"
            
            resp = self.session.get(url, timeout=15)
            result = resp.json()
            
            if result.get('responseStatus') == 200:
                translated = result['responseData']['translatedText']
                time.sleep(0.8)  # 礼貌延迟
                return translated if translated != text else text
            return text
        except:
            return text
