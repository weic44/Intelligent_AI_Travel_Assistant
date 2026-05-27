import os
from typing import Union
from playwright.sync_api import sync_playwright, Browser, Page
from langchain_core.runnables.graph import Graph

from utils.log_utils import get_logger

logger = get_logger(__name__)

# 全局浏览器实例，用于单例模式提高性能
_browser: Union[Browser, None] = None
_playwright_instance = None


def _get_browser() -> Browser:
    """
    单例模式获取 Playwright 浏览器实例。
    注意：需要在程序退出时调用 close_browser() 清理资源。
    """
    global _browser, _playwright_instance

    if _browser is None:
        # 1. 启动 Playwright 实例
        _playwright_instance = sync_playwright().start()
        # 2. 启动 Chromium 浏览器 (headless=True 表示无头模式，适合服务器/后台运行)
        _browser = _playwright_instance.chromium.launch(headless=True)
        logger.info("Playwright browser launched successfully.")

    return _browser


def close_browser():
    """关闭浏览器和 Playwright 实例，释放资源"""
    global _browser, _playwright_instance
    if _browser:
        _browser.close()
        _browser = None
    if _playwright_instance:
        _playwright_instance.stop()
        _playwright_instance = None
        logger.info("Playwright browser closed.")


def draw_png_local(graph: Graph, file: str):
    """
    使用本地 Playwright 浏览器渲染 Mermaid 图表为 PNG。
    完全离线，不依赖 mermaid.ink API。

    Args:
        graph: LangChain 的 Graph 对象
        file: 输出图片的文件路径
    """
    browser = None
    try:
        # 1. 从 LangChain Graph 对象中提取 Mermaid 源码
        # get_graph().draw_mermaid() 返回的是 mermaid 语法的字符串
        mermaid_code = graph.get_graph().draw_mermaid()

        if not mermaid_code:
            raise ValueError("Failed to extract mermaid code from graph.")

        # 2. 获取浏览器实例
        browser = _get_browser()
        page = browser.new_page()

        # 3. 构建一个包含 Mermaid JS 的 HTML 页面
        # 我们使用 CDN 引入 mermaid.js，但如果需要完全离线，可以下载 mermaid.min.js 到本地并引用本地文件
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: white; }}
                .mermaid {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div class="mermaid">
                {mermaid_code}
            </div>
            <!-- 使用 jsdelivr CDN 加载 Mermaid -->
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ 
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose'
                }});
                await mermaid.run();
            </script>
        </body>
        </html>
        """

        # 4. 设置页面内容
        page.set_content(html_content)

        # 5. 等待 Mermaid 图表渲染完成
        # 等待 .mermaid svg 元素出现，超时时间设为 10 秒
        page.wait_for_selector('.mermaid svg', timeout=10000)

        # 额外等待一小段时间确保样式完全应用
        page.wait_for_timeout(500)

        # 6. 截图并保存
        # clip 可以指定截取区域，这里截取整个页面
        page.screenshot(path=file, full_page=True)

        logger.info(f"Mermaid diagram saved to {file}")

    except Exception as e:
        logger.exception(f"Failed to render mermaid diagram locally: {e}")
        raise e
    finally:
        # 注意：这里不关闭 page，因为 browser 是单例复用的。
        # 如果希望每次调用都清理 page，可以在这里 page.close()
        if 'page' in locals():
            page.close()


# 示例用法
if __name__ == "__main__":
    # 假设你有一个 LangChain Graph 对象
    # from langchain_core.runnables import RunnableSequence
    # ... 构建你的 graph ...

    # 为了测试，你可以创建一个简单的 mock 对象或实际运行你的链
    # draw_png_local(your_graph, "output.png")

    # 程序结束前记得关闭浏览器
    # close_browser()
    pass

#
# def draw_png(graph,file:str):
#     try:
#         mermaid_code = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)
#         with open(file,"wb") as f:
#             f.write(mermaid_code)
#     except Exception as e:
#         logger.exception(e)