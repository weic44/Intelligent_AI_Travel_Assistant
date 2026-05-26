import uuid

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START,END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from graph_chat.assistant import CtripAssistant, assistant_runnable, primary_assistant_tools
from graph_chat.base_data_model import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, \
    ToBookExcursion
from graph_chat.build_child_graph import build_flight_graph, builder_hotel_graph, build_car_graph, \
    builder_excursion_graph
from graph_chat.state import State
from tools.flights_tools import fetch_user_flight_information
from tools.init_db import update_dates
from tools.tools_handler import create_tool_node_with_fallback
from tools.tools_handler import _print_event
from utlis.draw_png import draw_png_local


def get_user_info(state:State):
    """
    获取用户的航班信息并更新状态字典
    :param state: 当前状态字典
    :return: dict:包含用户信息的新字典
    """
    return {"user_info":fetch_user_flight_information.invoke({})}


# 定义流程图
builder = StateGraph(State)

# 自定义函数代表节点，Runnable,或者一个自定义的类都可以是节点
builder.add_node("fetch_user_info",get_user_info) # type:ignore
builder.add_edge(START,"fetch_user_info")


# 添加四个业务助理的子工作流
builder = build_flight_graph(builder)
builder = builder_hotel_graph(builder)
builder = build_car_graph(builder)
builder = builder_excursion_graph(builder)

# 添加主助理
builder.add_node("primary_assistant",CtripAssistant(assistant_runnable))
builder.add_node(
    "primary_assistant_tools",create_tool_node_with_fallback(primary_assistant_tools)
)

def route_primary_assistant(state:dict):
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state['messages'][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToFlightBookingAssistant.__name__:
            return "enter_update_flight"
        elif tool_calls[0]["name"] == ToBookCarRental.__name__:
            return "enter_book_car_flight"
        elif tool_calls[0]["name"] == ToHotelBookingAssistant.__name__:
            return "enter_book_hotel"
        elif tool_calls[0]["name"] == ToBookExcursion.__name__:
            return "enter_book_excursion"
        return "primary_assistant_tools"
    raise ValueError("无效路由")


builder.add_conditional_edges(
    "primary_assistant",
    # 路由函数
    route_primary_assistant,
    [
        "enter_update_flight",
        "enter_book_car_rental",
        "enter_book_hotel",
        "enter_book_excursion",
        "primary_assistant_tools", # 主助手的工具：全网搜索,RAG企业知识库
        END
    ]
)

builder.add_edge("primary_assistant_tools","primary_assistant")

def route_to_workflow(state:dict)->str:
    """
    在一个委托的状态中，直接路由到相应的助理
    :param state:
    :return:
    """
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant" # 没有对话状态则返回主路由
    return dialog_state[-1] # 返回最后一个对话状态

# 即使不同助理之间来回切换，也能保持上下文连贯性
builder.add_conditional_edges("fetch_user_info",route_to_workflow) # 根据获取用户信息进行跳转

memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=[
        "update_flight_sensitive_tools",
        "book_car_rental_sensitive_tools",
        "book_hotel_sensitive_tools",
        "book_excursion_sensitive_tools",
    ]
)


draw_png_local(graph,"graph4.png")


session_id = str(uuid.uuid4())

update_dates()  # 测试时候，数据为最新

config = {
    "configurable":{
        "passenger_id":"3442 587242",
        "thread_id":session_id,
    }
}

_printed = set()


while True:
    question = input("用户“：")
    if question.lower() in ['q','quit','exit']:
        print("对话结束")
    else:
        events = graph.stream({"messages":("user",question)},config=config,stream_mode='values') # type:ignore
        # 打印消息
        for event in events:
            _print_event(event,_printed)

        current_state = graph.get_state(config)
        if current_state.next:
            user_input = input(
                "你是否批准上述操作?输入‘y’继续，按q结束\n"
            )
            if user_input.strip().lower() in ['y','yes']:
                # 继续执行
                events = graph.stream(None,config=config,stream_mode='values')
                for event in events:
                    _print_event(event,_printed)
            else:
                result = graph.stream(
                    {
                        "messages":[
                            ToolMessage(
                                tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                content=f"Tool的调用被用户拒绝，原因:'{user_input}'。",
                            )
                        ]
                    },
                    config=config,
                )

                for event in events:
                    _print_event(event,_printed)