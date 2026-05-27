from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from sqlalchemy.sql.annotation import Annotated

from graph_chat.agent_assistant import update_flight_safe_tools, update_flight_sensitive_tools, book_hotel_tools, \
    book_car_rental_tools, book_excursion_tools
from graph_chat.llm_tavily import llm
from tools.search_tool import MySearchTool

memory = InMemorySaver()

research_agent = create_agent(
    model=llm,
    tools=[MySearchTool()],
    system_prompt=
    (
        "你是一个网络搜索的智能体(Agent).\n\n"
        "指令："
        "- 网络数据获取，网络查询，数据查询相关任务，不做计算"
        "- 回复时，仅回复搜索结果，不包含其他文字"
    ),
    checkpointer=memory,
    name="research_agent",
)

update_flight = update_flight_safe_tools + update_flight_sensitive_tools

flight_booking_agent = create_agent(
    model=llm,
    tools=update_flight,
    system_prompt=(
        "您是专门处理航班查询，改签政策查询，改签和预定的智能体(Agent)。\n\n"
        "指令：\n"
        "- 在搜索航班时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
        "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
        "- 回复时仅包含工作结果，不要包含任何其他文字"
    ),
    name="flight_booking_agent",
)

hotel_booking_agent = create_agent(
    model=llm,
    tools=book_hotel_tools,
    system_prompt=(
        "您是专门处理酒店查询，酒店预定，订单修改的智能体(Agent)。\n\n"
        "指令：\n"
        "- 在搜索航班时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
        "- 根据客户的偏好搜索可用酒店，并与用户确认预定情况"
        "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
        "- 回复时仅包含工作结果，不要包含任何其他文字"
    ),
    name="hotel_booking_agent",
)

car_rental_booking_agent = create_agent(
    model=llm,
    tools=book_car_rental_tools,
    system_prompt=(
        "您是专门处理汽车租车查询，租车租聘预定，汽车租聘订单修改的智能体(Agent)。\n\n"
        "指令：\n"
        "- 在搜索航班时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
        "- 根据客户的偏好搜索可用酒店，并与用户确认预定情况"
        "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
        "- 回复时仅包含工作结果，不要包含任何其他文字"
    ),
    name="car_rental_booking_agent",
)

excursion_booking_agent = create_agent(
    model=llm,
    tools=book_excursion_tools,
    system_prompt=(
        "您是专门处理旅行推荐查询，旅行产品预定，旅行订单订单修改的智能体(Agent)。\n\n"
        "指令：\n"
        "- 在搜索航班时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
        "- 根据客户的偏好搜索可用酒店，并与用户确认预定情况"
        "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
        "- 回复时仅包含工作结果，不要包含任何其他文字"
    ),
    name="excursion_booking_agent",
)

def create_handoff_tool(*,agent_name:str,description:str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help"

    @tool(name,description=description)
    def handoff_tool(
            state:Annotated[MessagesState,InjectedState],
            tool_call_id:Annotated[str,InjectedToolCallId],
    )->Command:
        """执行实际地方转接操作"""
        # 构建工具消息，记录转接操作的成功执行
        tool_message = {
            "role":"tool",
            "content":f"Successfully transferred to {agent_name}",
            "name":name,
            "tool_call_id":tool_call_id,
        }

        # 返回转接命令
        return Command(
            # 转接到哪个智能体
            goto=agent_name,
            update={**state,"messages":state["messages"] + [tool_message]}, # 占用上下文长度过长
            graph=Command.PARENT
        )

    return handoff_tool

# Handoffs
assign_to_research_agent = create_handoff_tool(
    agent_name="research_agent",
    description="将任务分配给:research_agent",
)

assign_to_hotel_agent = create_handoff_tool(
    agent_name="hotel_agent",
    description="将任务分配给:hotel_agent",
)

assign_to_flight_agent = create_handoff_tool(
    agent_name="flight_booking_agent",
    description="将任务分配给:flight_booking_agent",
)

assign_to_car_rental_booking_agent = create_handoff_tool(
    agent_name="car_rental_booking_agent",
    description="将任务分配给:flight_booking_agent",
)

assign_to_excursion_booking_agent = create_handoff_tool(
    agent_name="excursion_booking_agent",
    description="将任务分配给:excursion_booking_agent",
)

# 主管者智能体
supervisor_agent = create_agent(
    model=llm,
    tools = [assign_to_flight_agent, assign_to_car_rental_booking_agent,
             assign_to_excursion_booking_agent,assign_to_hotel_agent,assign_to_research_agent],
    system_prompt=(
        "你是一个监督者或者管理者，管理五个智能体：\n"
        "- 网络搜索智能体：分配与网络搜索、数据查询相关的任务\n"
        "- 航班预订智能体：分配与航班查询，预定，改签等相关的任务\n"
        "- 酒店预订智能体：分配与酒店查询，预定，修改订单等相关的任务\n"
        "- 汽车租赁预定智能体：分配与汽车租赁查询，预定，修改订单等相关的任务\n"
        "- 旅行产品预定智能体：分配与旅行推荐查询，预定，修改订单等相关的任务\n"
        "处理规则：\n"
        "1. 如果问题属于以下类别，直接回答：\n"
        "    - 可以根据上下文记录直接回答的内容（如'你的航班信息，起飞时间等'）。\n"
        "    - 不需要工具的一般咨询（如'你好'）。\n"
        "    - 确认类问题（如'你收到我的请求了吗'）。\n"
        "2. 其他情况按类型分配给对应智能体。\n"
        "3. 一次只分配一个任务给一个智能体。\n"
        "4. 不要自己执行需要工具的任务。\n"
    ),
    name="supervisor_agent",
)




