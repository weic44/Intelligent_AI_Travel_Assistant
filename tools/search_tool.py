import os
from typing import Type

from langgraph.types import interrupt
from zhipuai import ZhipuAI
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from utils.log_utils import get_logger

log = get_logger(__name__)

zhipuai_client = ZhipuAI(
    api_key= os.getenv("ZHIPU_API_KEY"),
    max_retries=3
)

class SearchArgs(BaseModel):
    query:str = Field(description="需要进行网络搜索的信息.")

class MySearchTool(BaseTool):
    name:str = "search_tool"

    description:str = "搜索互联网上公开的内容"

    return_direct:bool = False

    args_schema:Type[BaseModel] = SearchArgs

    def _run(self,query)->str:
        try:
            print("AI大模型试图调用工具")
            response = interrupt(
                f"AI大模型试图调用工具'search_tool'来完成数据搜索\n"
                "请审核并选择，批准(y)"
            )
            if response['answer'] == "y":
                pass # 增加使用原参数运行
            else:
                return f"人工停止了该工具的调用，给出的理由或者答案是{response['answer']}",
            response = zhipuai_client.web_search.web_search(
                search_query=query,
                search_engine="search_std",
            )

            if response.search_result:
                return "\n\n".join([d.content for d in response.search_result])
            return "没有搜索到任何内容"
        except Exception as e:
            log.error(e)
            return "没有搜索到任何内容"
