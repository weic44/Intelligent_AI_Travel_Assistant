import os
import datetime

from zhipuai import ZhipuAI
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.runnables import Runnable,RunnableConfig

from graph_chat.state import State
from tools.car_tools import search_car_rentals, book_car_rental, update_car_rental, cancel_car_rental
from tools.flights_tools import fetch_user_flight_information, search_flights, update_ticket_to_new_flight, \
    cancel_ticket
from tools.hotels_tools import search_hotels, book_hotel, update_hotel, cancel_hotel
from tools.retriever_vector import lookup_policy
from tools.trip_tools import search_trip_recommendations, book_excursion, update_excursion, cancel_excursion


class CtripAssistant:
    #自定义一个类，表示流程图的一个节点

    def __init__(self,runnable:Runnable):
        self.runnable = runnable

    def __call__(self,state:State,config:RunnableConfig):
        while True:
            # configuration = config.get('configurable',{})
            # user_id = configuration.get('passenger_id',None)
            # state = {**state,'user_info':user_id} # 从配置中得到旅客ID,创建一个新字典，里面包含state所有键值对，并且新增user_info
            result = self.runnable.invoke(state)
            # 如果没有得到输出
            if not result.tool_calls and ( # 有无调用工具
                not result.content or isinstance(result.content,list)
                and not result.content[0].get('text')
            ):
                messages = state['messages' ] + ['user','请提供一个真实的输出作为回应.']
                state = {**state,'messages':messages}
            else:
                break

        return {"messages":result}
# 定义只读工具列表，无需用户确认即可使用
safe_tools = [
    fetch_user_flight_information,
    search_flights,
    lookup_policy,
    search_car_rentals,
    search_hotels,
    search_trip_recommendations,
]
# 定义敏感工具列表,需要用户确认呢
sensitive_tools = [
    update_ticket_to_new_flight,
    cancel_ticket,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
    book_hotel,
    update_hotel,
    cancel_hotel,
    book_excursion,
    update_excursion,
    cancel_excursion
]

# 用于后续是否需要用户确认
sensitive_tools_names = {t.name for t in sensitive_tools}





def create_assistant_node() -> CtripAssistant:
    """
    定义节点
    :return:
    """
    llm = ChatTongyi(
        model = os.getenv("QWEN_MODEL"),
        api_key = os.getenv("QWEN_API_KEY"),
    )

    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "您是携程瑞士航空公司的客户服务助理。优先使用提供的工具搜索航班、公司政策和其他信息来帮助用户的查询"
                "搜索时，请坚持不懈。如果第一次搜索没有结果，扩大您的查询范围。"
                "如果搜索为空，在放弃之前扩展您的搜索。\n\n当前用户:\n<User>\n{user_info}\n</User>"
                "\n当前时间：{time}.",
            ),
            ("placeholder","{messages}"),
        ]
    ).partial(time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    runnable = primary_assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)
    return CtripAssistant(runnable)

    return CtripAssistant(runnable) # 创建一个类的对象