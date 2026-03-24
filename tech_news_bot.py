#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技新闻抓取、翻译与推送脚本
- 抓取 HackerNews Top Stories
- 自动翻译为中文
- 通过 Server酱推送到微信
"""

import os
import requests
import json
import time
from datetime import datetime


class TechNewsBot:
    def __init__(self):
        self.server_chan_key = os.environ.get('SERVER_CHAN_KEY')
        if not self.server_chan_key:
            raise ValueError("请设置 SERVER_CHAN_KEY 环境变量")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TechNewsBot/1.0 (GitHub Actions)'
        })
        
        # LibreTranslate 公共实例（免费，无需Key）
        # 如果失效，可以尝试其他实例：https://github.com/LibreTranslate/LibreTranslate#mirrors
        self.translate_urls = [
            "https://libretranslate.de/translate",
            "https://translate.argosopentech.com/translate",
            "https://libretranslate.pussthecat.org/translate"
        ]
    
    def translate_text(self, text, target_lang="zh"):
        """
        翻译文本为中文（带重试机制）
        """
        if not text or len(text.strip()) == 0:
            return text
        
        # 如果已经是中文为主（简单判断），跳过翻译
        if self._is_mostly_chinese(text):
            return text
        
        payload = {
            "q": text,
            "source": "en",
            "target": target_lang,
            "format": "text"
        }
        
        # 尝试多个翻译实例
        for url in self.translate_urls:
            try:
                resp = self.session.post(
                    url, 
                    data=payload, 
                    timeout=15,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if resp.status_code == 200:
                    result = resp.json()
                    translated = result.get("translatedText", text)
                    print(f"✅ 翻译成功: {text[:30]}... -> {translated[:30]}...")
                    time.sleep(0.5)  # 礼貌延迟，避免频率限制
                    return translated
            except Exception as e:
                print(f"⚠️ 翻译实例 {url} 失败: {e}")
                continue
        
        # 全部失败则返回原文
        print(f"❌ 翻译失败，使用原文: {text[:30]}...")
        return text
    
    def _is_mostly_chinese(self, text):
        """简单判断文本是否主要为中文"""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        return chinese_chars > len(text) * 0.3  # 如果中文占比超30%，认为是中文
    
    def fetch_hackernews(self, limit=10):
        """抓取 HackerNews Top Stories 并翻译"""
        try:
            # 获取 top stories ID 列表
            resp = self.session.get(
                'https://hacker-news.firebaseio.com/v0/topstories.json',
                timeout=10
            )
            story_ids = resp.json()[:limit]
            
            stories = []
            print(f"🔄 开始抓取 {limit} 条新闻并翻译...")
            
            for idx, story_id in enumerate(story_ids, 1):
                try:
                    # 获取每个 story 的详情
                    detail_resp = self.session.get(
                        f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                        timeout=10
                    )
                    story = detail_resp.json()
                    
                    if story and story.get('title'):
                        original_title = story['title']
                        # 翻译标题
                        translated_title = self.translate_text(original_title)
                        
                        stories.append({
                            'title_original': original_title,
                            'title_translated': translated_title,
                            'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                            'score': story.get('score', 0),
                            'by': story.get('by', 'unknown'),
                            'comments': story.get('descendants', 0),
                            'time': story.get('time', 0)
                        })
                        
                        print(f"  {idx}. {translated_title}")
                        
                except Exception as e:
                    print(f"⚠️ 处理第 {idx} 条新闻失败: {e}")
                    continue
            
            return stories
            
        except Exception as e:
            print(f"抓取 HackerNews 失败: {e}")
            return []
    
    def format_message(self, stories):
        """格式化消息（双语显示）"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        content = f"## 📰 科技早报 ({today})\n\n### 🔥 HackerNews Top {len(stories)}\n\n"
        
        for i, story in enumerate(stories, 1):
            story_time = datetime.fromtimestamp(story['time'])
            time_str = story_time.strftime('%m-%d %H:%M')
            
            # 显示格式：序号. 中文标题（原文标题）
            content += f"{i}. **{story['title_translated']}**\n"
            content += f"   📝 {story['title_original']}\n"
            content += f"   👤 {story['by']} | ⭐ {story['score']} | 💬 {story['comments']} | 🕐 {time_str}\n"
            content += f"   🔗 [阅读原文]({story['url']})\n\n"
        
        content += f"\n---\n⏰ 推送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🤖 自动抓取并翻译 | GitHub Actions & Server酱"
        
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
        
        # 抓取并翻译数据
        stories = self.fetch_hackernews(10)
        
        if not stories:
            print("⚠️ 未获取到任何新闻")
            return False
        
        # 格式化消息
        content = self.format_message(stories)
        title = f"📰 科技早报 {datetime.now().strftime('%m/%d')} | 已翻译 {len(stories)} 条"
        
        # 推送
        print(f"📤 正在推送: {title}")
        return self.push_to_wechat(title, content)


if __name__ == '__main__':
    bot = TechNewsBot()
    success = bot.run()
    exit(0 if success else 1)
