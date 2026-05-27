from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState

from tools.flights_tools import fetch_user_flight_information

def format_flight_info(flight_data: list[dict]) -> str:
    """将航班数据格式化为中文字符串"""
    flight = flight_data[0]  # 假设返回的是单条航线信息
    return (
        f"已查询到您的航班信息: \n"
        f"- 机票号: {flight['ticket_no']}\n"
        f"- 订编号: {flight['book_ref']}\n"
        f"- 航号: {flight['flight_no']} ( {flight['flight_id']} ) \n"
        f"- 出发机场: {flight['departure_airport']}\n"
        f"- 到达机场: {flight['arrival_airport']}\n"
        f"- 计划起飞时间: {flight['scheduled_departure']}\n"
        f"- 计划到达时间: {flight['scheduled_arrival']}\n"
        f"- 座位号: {flight['seat_no']}\n"
        f"- 舱位条件: {flight['fare_conditions']}"
    )


def get_user_info(state: MessagesState,config:RunnableConfig):
    if "messages" in state:
        for message in state["messages"]:
            # 查到航班信息就返回
            if isinstance(message,AIMessage) and message.id == "user_info_success":
                return

    flight_data = fetch_user_flight_information(config)
    if flight_data:
        flight_message = AIMessage(
            content=format_flight_info(flight_data),
            additional_kwargs={},
            id="user_info_success"
        )
    else:
        flight_message = AIMessage(
            content="未找到您的航班信息，请检查输入的航班信息是否正确",
            additional_kwargs={},
            id="user_info_fail"
        )
    return {
        "messages":[flight_message],# 新增加AIMessage
    }