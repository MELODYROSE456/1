#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技新闻抓取、翻译与推送脚本（MyMemory翻译版 - 稳定可靠）
"""

import os
import requests
import json
import urllib.parse
import time
from datetime import datetime
# 在原有import下面新增这两行
from github_fetcher import GitHubFetcher
from translator import Translator
from config import SERVER_CHAN_KEY


class TechNewsBot:
    def __init__(self):
        self.server_chan_key = os.environ.get('SERVER_CHAN_KEY')
        if not self.server_chan_key:
            raise ValueError("请设置 SERVER_CHAN_KEY 环境变量")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TechNewsBot/1.0 (GitHub Actions)'
        })
    
    def translate_mymemory(self, text):
        """
        使用 MyMemory API 翻译（免费，无需Key，每天1000次限制）
        """
        if not text or len(text.strip()) == 0:
            return text
        
        # 如果包含中文，直接返回
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
        
        try:
            # URL编码文本
            encoded_text = urllib.parse.quote(text)
            
            # MyMemory API（免费版，建议加上你的邮箱以获得更高额度）
            # 把下面的 email 参数换成你的真实邮箱（可选，但推荐）
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|zh-CN&email=your.email@example.com"
            
            resp = self.session.get(url, timeout=15)
            result = resp.json()
            
            # 检查响应状态
            if result.get('responseStatus') == 200:
                translated = result['responseData']['translatedText']
                # 如果返回的是英文（有时API会返回原文），说明可能失败了
                if translated.lower() == text.lower():
                    print(f"⚠️ 翻译可能失败，返回原文: {text[:40]}...")
                    return text
                print(f"✅ 翻译: {text[:40]}... -> {translated[:40]}...")
                time.sleep(1)  # 免费API建议间隔1秒，避免限流
                return translated
            else:
                print(f"⚠️ MyMemory API 错误: {result.get('responseDetails', '未知错误')}")
                return text
                
        except Exception as e:
            print(f"❌ 翻译异常: {e}, 使用原文")
            return text
    
    def fetch_hackernews(self, limit=10):
        """抓取 HackerNews 并翻译"""
        try:
            resp = self.session.get(
                'https://hacker-news.firebaseio.com/v0/topstories.json',
                timeout=10
            )
            story_ids = resp.json()[:limit]
            
            stories = []
            print(f"🔄 开始抓取 {limit} 条新闻并翻译...")
            
            for idx, story_id in enumerate(story_ids, 1):
                try:
                    detail_resp = self.session.get(
                        f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                        timeout=10
                    )
                    story = detail_resp.json()
                    
                    if story and story.get('title'):
                        original = story['title']
                        # 翻译
                        translated = self.translate_mymemory(original)
                        
                        stories.append({
                            'title_original': original,
                            'title_translated': translated,
                            'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                            'score': story.get('score', 0),
                            'by': story.get('by', 'unknown'),
                            'comments': story.get('descendants', 0),
                            'time': story.get('time', 0)
                        })
                        
                        print(f"  {idx}. {translated[:60]}...")
                        
                except Exception as e:
                    print(f"⚠️ 处理第 {idx} 条新闻失败: {e}")
                    continue
            
            return stories
            
        except Exception as e:
            print(f"抓取 HackerNews 失败: {e}")
            return []
    
    def format_message(self, stories, gh_repos=None):  # 加了个参数
        """格式化消息（双语显示）"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        content = f"## 📰 科技早报 ({today})\n\n### 🔥 HackerNews Top {len(stories)}（已翻译）\n\n"
        
        for i, story in enumerate(stories, 1):
            story_time = datetime.fromtimestamp(story['time'])
            time_str = story_time.strftime('%m-%d %H:%M')
            
            content += f"{i}. **{story['title_translated']}**\n"
            content += f"   📝 {story['title_original']}\n"
            content += f"   👤 {story['by']} | ⭐ {story['score']} | 💬 {story['comments']} | 🕐 {time_str}\n"
            content += f"   🔗 [阅读原文]({story['url']})\n\n"
        
        content += f"\n---\n⏰ 推送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🤖 自动翻译推送 | GitHub Actions & MyMemory"
                # 🆕 在 HackerNews 部分后面，添加 GitHub 部分
        if gh_repos:
            content += f"\n### 🚀 GitHub Trending Top {len(gh_repos)}\n\n"
            for i, repo in enumerate(gh_repos, 1):
                content += f"{i}. **{repo['name']}**\n"
                content += f"   📝 {repo['name_en']}\n"
                content += f"   📄 {repo['desc']}\n"
                content += f"   💻 {repo['lang']} | ⭐{repo['stars']} | 🔥+{repo['today_stars']}\n"
                content += f"   🔗 [查看项目]({repo['url']})\n\n"
        return content
    
    def push_to_wechat(self, title, content):
        """通过 Server酱 推送到微信"""
        try:
            url = f"https://sctapi.ftqq.com/{self.server_chan_key}.send"
            data = {
                'title': title,
                'desp': content
            }
            
            resp = self.session.post(url, data=data, timeout=10)
            result = resp.json()
            
            if result.get('code') == 0:
                print("✅ 微信推送成功！")
                return True
            else:
                print(f"❌ 推送失败: {result.get('message', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False
    
    def run(self):
    """主运行逻辑"""
    print("🚀 开始抓取并翻译科技新闻...")
    
    # 原有：抓取 HackerNews
    stories = self.fetch_hackernews(10)
    
    # 🆕 新增：抓取 GitHub（就加这 3 行！）
    from github_fetcher import GitHubFetcher
    gh_fetcher = GitHubFetcher()
    gh_repos = gh_fetcher.fetch_trending(5)
    
    # 修改：传入两个参数
    content = self.format_message(stories, gh_repos)
    title = f"📰 科技早报 {datetime.now().strftime('%m/%d')} | HN×{len(stories)} GitHub×{len(gh_repos)}"
    
    print(f"📤 正在推送: {title}")
    return self.push_to_wechat(title, content)


if __name__ == '__main__':
    bot = TechNewsBot()
    success = bot.run()
    exit(0 if success else 1)
