#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技新闻抓取与推送脚本
- 抓取 HackerNews Top Stories
- 抓取 GitHub Trending
- 通过 Server酱推送到微信
"""

import os
import requests
import json
from datetime import datetime, timedelta


class TechNewsBot:
    def __init__(self):
        self.server_chan_key = os.environ.get('SERVER_CHAN_KEY')
        if not self.server_chan_key:
            raise ValueError("请设置 SERVER_CHAN_KEY 环境变量")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TechNewsBot/1.0 (GitHub Actions)'
        })
    
    def fetch_hackernews(self, limit=10):
        """抓取 HackerNews Top Stories"""
        try:
            # 获取 top stories ID 列表
            resp = self.session.get(
                'https://hacker-news.firebaseio.com/v0/topstories.json',
                timeout=10
            )
            story_ids = resp.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                # 获取每个 story 的详情
                detail_resp = self.session.get(
                    f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                    timeout=10
                )
                story = detail_resp.json()
                if story and story.get('title'):
                    stories.append({
                        'title': story['title'],
                        'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                        'score': story.get('score', 0),
                        'by': story.get('by', 'unknown'),
                        'comments': story.get('descendants', 0),
                        'time': story.get('time', 0)
                    })
            return stories
        except Exception as e:
            print(f"抓取 HackerNews 失败: {e}")
            return []
    
    def fetch_github_trending(self):
        """抓取 GitHub Trending"""
        try:
            # 使用开源 API
            resp = self.session.get(
                'https://api.gitter.im/v1/repositories/trending?language=&since=daily',
                timeout=10
            )
            if resp.status_code == 200:
                repos = resp.json()[:5]
                return [{
                    'name': repo.get('name', 'unknown/unknown'),
                    'description': repo.get('description', '无描述')[:100] + '...' if repo.get('description') else '无描述',
                    'stars': repo.get('stars', 0),
                    'url': repo.get('url', '')
                } for repo in repos]
        except Exception as e:
            print(f"抓取 GitHub Trending 失败: {e}")
        return []
    
    def format_message(self, hn_stories, gh_repos):
        """格式化消息内容"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        content = f"## 📰 科技早报 ({today})\n\n### 🔥 HackerNews Top 10\n\n"
        
        for i, story in enumerate(hn_stories, 1):
            story_time = datetime.fromtimestamp(story['time'])
            time_str = story_time.strftime('%m-%d %H:%M')
            
            content += f"{i}. [{story['title']}]({story['url']})\n"
            content += f"   👤 {story['by']} | ⭐ {story['score']} | 💬 {story['comments']} | 🕐 {time_str}\n\n"
        
        if gh_repos:
            content += "### 🚀 GitHub 今日热门\n\n"
            for i, repo in enumerate(gh_repos, 1):
                content += f"{i}. [{repo['name']}]({repo['url']})\n"
                content += f"   ⭐ {repo['stars']} | {repo['description']}\n\n"
        
        content += f"\n---\n⏰ 推送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🤖 自动推送 via GitHub Actions & Server酱"
        
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
                print("✅ 推送成功！")
                return True
            else:
                print(f"❌ 推送失败: {result.get('message', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False
    
    def run(self):
        """主运行逻辑"""
        print("🚀 开始抓取科技新闻...")
        
        # 抓取数据
        hn_stories = self.fetch_hackernews(10)
        gh_repos = self.fetch_github_trending()
        
        if not hn_stories:
            print("⚠️ 未获取到任何新闻")
            return False
        
        # 格式化消息
        content = self.format_message(hn_stories, gh_repos)
        title = f"📰 科技早报 {datetime.now().strftime('%m/%d')} | HN Top {len(hn_stories)}"
        
        # 推送
        print(f"正在推送: {title}")
        return self.push_to_wechat(title, content)


if __name__ == '__main__':
    bot = TechNewsBot()
    success = bot.run()
    exit(0 if success else 1)
