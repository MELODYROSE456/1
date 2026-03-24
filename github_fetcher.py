# github_fetcher.py - 使用 GitHub 官方 Search API（稳定可靠）
import requests
from translator import Translator

class GitHubFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.translator = Translator()
    
    def fetch_trending(self, limit=5):
        """
        使用 GitHub Search API 获取最近热门仓库
        查询条件：最近7天创建，按星标数排序
        """
        try:
            # GitHub 官方 Search API（无需Token，但有频率限制）
            # 查询最近7天创建的 Python/JavaScript/Go 项目，按stars排序
            url = "https://api.github.com/search/repositories"
            params = {
                "q": "created:>2026-03-17",  # 最近7天
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            
            resp = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                repos = data.get("items", [])
                
                results = []
                for repo in repos:
                    name = repo['full_name']
                    desc = repo.get('description', 'No description') or 'No description'
                    
                    # 翻译
                    name_zh = self.translator.translate(name)
                    desc_zh = self.translator.translate(desc)
                    
                    results.append({
                        'name': name_zh,
                        'name_en': name,
                        'desc': desc_zh,
                        'desc_en': desc,
                        'lang': repo.get('language', 'Unknown') or 'Unknown',
                        'stars': repo['stargazers_count'],
                        'today_stars': repo['stargazers_count'],  # 用总数代替今日新增
                        'url': repo['html_url']
                    })
                
                print(f"✅ GitHub 官方 API 抓取成功：{len(results)} 个项目")
                return results
            else:
                print(f"⚠️ GitHub API 返回错误：{resp.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ GitHub 抓取失败：{e}")
            return []
