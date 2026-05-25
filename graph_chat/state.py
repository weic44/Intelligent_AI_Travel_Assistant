from typing import TypedDict, Annotated, Literal, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

def update_dialog_stack(left:list[str],right:Optional[str])->list[str]:
    """
    更新对话状态栈
    :param left:当前状态栈
    :param right: 想要添加到栈中的新状态或者动作，如果为NULL，则不做修改，如果为“pop”，则弹出栈顶元素
    :return: list[str: 更新后的状态栈
    """
    if right is None:
        return left # 如果为right是NULL，保持当前状态栈不变
    if right == "pop":
        return left[:-1] # 如果是“pop”溢出栈顶元素（最后一个状态）
    return left + [right] # 否则将right加入状态栈

# 状态类
class State(TypedDict):
    # 添加消息
    messages:Annotated[list[AnyMessage],add_messages]
    user_info: str

    # 添加子工作流
    dialog_state: Annotated[
        list[ # 其元素严格限定为上述五个字符串之一,这种做法确保了对话状态逻辑的一致性与正确性
            Literal[
                "assistant",
                "update_flight",
                "book_car_flight",
                "book_hotel",
                "book_excursion",
            ]
        ],
        # 如果大模型觉得不需要工具便会移除状态
        update_dialog_stack,
    ]