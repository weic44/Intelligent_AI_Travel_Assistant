from langgraph.graph import StateGraph
from langgraph_sdk.schema import Assistant

from graph_chat.agent_assistant import update_flight_runnable, update_flight_sensitive_tools, update_flight_safe_tools
from graph_chat.assistant import CtripAssistant
from graph_chat.entry_node import create_entry_node
from tools.tools_handler import create_tool_node_with_fallback


def build_flight_graph(builder:StateGraph)->StateGraph:
    builder.add_node(
        "entry_update_flight",
        create_entry_node("Flight Update & Booking Assistant","update_flight"), # 创建入口节点
    )
    builder.add_node("update_flight",CtripAssistant(update_flight_runnable)) # 添加处理航班的实际节点
    builder.add_edge("entry_update_flight","update_flight") # 连接入口节点到实际节点
    #添加敏感工具和安全工具的节点
    builder.add_node(
        "update_flight_sensitive_tools",
        create_tool_node_with_fallback(update_flight_sensitive_tools) # 敏感工具节点 ignore
    )

    builder.add_node(
        "update_flight_safe_tools",
        create_tool_node_with_fallback(update_flight_safe_tools) # 安全工具节点
    )