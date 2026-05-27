from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.graph import StateGraph
from langgraph.constants import END,START

from graph_chat.state import State
from new_graph_chat.fetch_user_info_node import get_user_info
from new_graph_chat.all_agent import supervisor_agent, research_agent, flight_booking_agent, hotel_booking_agent, \
    car_rental_booking_agent, excursion_booking_agent
from utils.draw_png import draw_png_local

memory = InMemorySaver()

graph = (
    StateGraph(State)
    .add_node("fetch_user_info",get_user_info)
    # 添加主管agent节点
    .add_node(supervisor_agent,destinations=["research_agent","flight_booking_agent","hotel_booking_agent","excursion_booking_agent","car_rental_booking_agent",END])
    .add_node(research_agent, destinations=(END,))
    .add_node(flight_booking_agent, destinations=(END,))
    .add_node(hotel_booking_agent, destinations=(END,))
    .add_node(car_rental_booking_agent, destinations=(END,))
    .add_node(excursion_booking_agent, destinations=(END,))
    .add_edge(START, 'fetch_user_info')
    .add_edge('fetch_user_info', 'supervisor_agent')
    .compile(checkpointer=memory)
)

# draw_png_local(graph, "../static/graph_supervisor.png")