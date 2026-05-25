import uuid

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START,END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from graph_chat.assistant import create_assistant_node, safe_tools, sensitive_tools, sensitive_tools_names
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
builder.add_node("assistant",create_assistant_node()) # type:ignore
builder.add_node("fetch_user_info",get_user_info) # type:ignore

# 工具拆成两个节点
builder.add_node("safe_tools",create_tool_node_with_fallback(safe_tools))
builder.add_node("sensitive_tools",create_tool_node_with_fallback(sensitive_tools))

def route_conditional_tools(state:State)->str:
    """
    根据当前状态，决定下一个执行节点
    :param state:
    :return: str
    """
    next_node = tools_condition(state)
    if next_node == END:
        return END

    ai_message = state['messages'][-1]
    tool_call = ai_message.tool_calls[0]
    if tool_call['name'] in sensitive_tools_names: # 敏感工具调用
        return "sensitive_tools"
    return "safe_tools"

builder.add_edge(START,"fetch_user_info")

builder.add_edge("fetch_user_info","assistant")

# 使用tools_condition决定哪些条件满足
builder.add_conditional_edges(
    "assistant",
    # 工具和END节点 二选一跳转
    route_conditional_tools,
    path_map=['safe_tools','sensitive_tools',END]
)

builder.add_edge("safe_tools","assistant")
builder.add_edge("sensitive_tools","assistant")
# 检查点让状态图可以持久化状态
# 状态图的完整内存
memory = MemorySaver()
# 编译状态图，检查点位memory,配置中断点
graph = builder.compile(checkpointer=memory,interrupt_before=['sensitive_tools'])

draw_png_local(graph,"graph3.png")

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