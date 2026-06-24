import asyncio
from playwright.async_api import async_playwright
import random
from flask import Flask, jsonify
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class VideoCrawler:
    def __init__(self):
        self.base_url = "https://twitter-ero-video-ranking.com"
    
    async def fetch_random_video(self):
        async with async_playwright() as p:
            # 启动浏览器（无头模式，不显示界面）
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 随机访问 1-5 页
            page_num = random.randint(1, 5)
            url = f"{self.base_url}/zh-CN/weekly?sort=favorite&page={page_num}"
            logger.info(f"正在访问: {url}")
            
            # 等待页面加载完成，特别是等待视频列表出现
            await page.goto(url, timeout=30000)
            # 等待某个电影链接出现（可根据实际情况调整选择器）
            await page.wait_for_selector('a[href*="/zh-CN/movie/"]', timeout=10000)
            
            # 提取所有电影链接
            movie_links = await page.eval_on_selector_all(
                'a[href*="/zh-CN/movie/"]',
                'elements => elements.map(e => e.href)'
            )
            logger.info(f"找到 {len(movie_links)} 个电影链接")
            
            if not movie_links:
                await browser.close()
                return None
            
            # 随机选择一个电影
            movie_url = random.choice(movie_links)
            logger.info(f"进入电影页: {movie_url}")
            await page.goto(movie_url, timeout=30000)
            
            # 等待页面加载，寻找视频链接
            # 方法1：查找包含视频链接的 a 标签
            video_url = await page.eval_on_selector(
                'a[href*="video.twimg.com/amplify_video"]',
                'el => el ? el.href : null'
            )
            
            # 如果没找到，尝试从页面内容中正则提取
            if not video_url:
                content = await page.content()
                import re
                pattern = r'https://video\.twimg\.com/amplify_video/[^"\']+'
                match = re.search(pattern, content)
                if match:
                    video_url = match.group(0)
            
            await browser.close()
            
            if video_url:
                return {
                    'success': True,
                    'video_url': video_url,
                    'source_page': movie_url
                }
            else:
                return None

# 由于 Flask 不支持异步视图，需要将异步函数转为同步
def sync_fetch():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(crawler.fetch_random_video())

crawler = VideoCrawler()

@app.route('/random_video', methods=['GET'])
def random_video_api():
    try:
        result = sync_fetch()
        if result:
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': '无法获取视频链接', 'video_url': None})
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({'success': False, 'error': '服务器内部错误', 'video_url': None}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("随机视频API服务启动中 (使用 Playwright)")
    print("API端点: http://localhost:5000/random_video")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)