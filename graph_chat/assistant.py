import os
import datetime

from zhipuai import ZhipuAI
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.runnables import Runnable,RunnableConfig

from graph_chat.base_data_model import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant
from graph_chat.llm_tavily import llm
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

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是携程瑞士航空公司的客户服务助理。"
            "您的主要职责是搜索航班信息和公司政策以回答客户的查询。"
            "如果客户请求更新或取消航班、预订租车、预订酒店或获取旅行推荐，请通过调用相应的工具将任务委派给合适的专门助理。您自己无法进行这些类型的更改。"
            "只有专门助理才有权限为用户执行这些操作。"
            "用户并不知道有不同的专门助理存在，因此请不要提及他们；只需通过函数调用来安静地委派任务。"
            "向客户提供详细的信息，并且在确定信息不可用之前总是复查数据库。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "如果搜索无果，请扩大搜索范围后再放弃。"
            "\n\n当前用户的航班信息:\n<Flights>\n{user_info}\n</Fllights>"
            "\n当前时间: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.datetime.now())


# 定义主助理使用的工具
primary_assistant_tools = [
    search_car_rentals,
    lookup_policy,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
    + [
        ToFlightBookingAssistant, # 转交给航班agent
        ToBookCarRental,
        ToHotelBookingAssistant,
        ToBookCarRental
    ]
)
