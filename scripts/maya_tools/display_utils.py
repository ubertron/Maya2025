from maya import cmds


def in_view_message(text: str):
    cmds.inViewMessage(assistMessage=text, fade=True, pos='midCenter')
