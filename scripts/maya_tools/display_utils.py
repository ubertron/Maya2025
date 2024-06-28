from maya import cmds


def in_view_message(text: str, persist_time: int = 2000):
    cmds.inViewMessage(assistMessage=text, fade=True, pos='midCenter', fadeStayTime=persist_time)
