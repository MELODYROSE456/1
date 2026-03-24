# github_fetcher.py - GitHub热门项目抓取
import requests
from translator import Translator

class GitHubFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.translator = Translator()
    
    def fetch_trending(self, limit=5):
        """抓取GitHub今日热门"""
        try:
            url = "https://ghapi.huchen.dev/repositories?since=daily"
            resp = self.session.get(url, timeout=15)
            repos = resp.json()[:limit]
            
            results = []
            for repo in repos:
                name = f"{repo['author']}/{repo['name']}"
                desc = repo.get('description', 'No description')
                
                # 翻译
                name_zh = self.translator.translate(name)
                desc_zh = self.translator.translate(desc)
                
                results.append({
                    'name': name_zh,
                    'name_en': name,
                    'desc': desc_zh,
                    'desc_en': desc,
                    'lang': repo.get('language', 'Unknown'),
                    'stars': repo['stars'],
                    'today_stars': repo['currentPeriodStars'],
                    'url': repo['url']
                })
            return results
        except Exception as e:
            print(f"GitHub抓取失败: {e}")
            return []
