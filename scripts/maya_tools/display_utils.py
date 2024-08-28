import logging

from maya import cmds


def in_view_message(text: str, persist_time: int = 2000):
    """
    Display a message across the viewport
    :param text:
    :param persist_time:
    """
    cmds.inViewMessage(assistMessage=text, fade=True, pos='midCenter', fadeStayTime=persist_time)


def warning_message(text: str, persist_time: int = 2000):
    """
    Display a warning message in-view and in the log
    :param text:
    :param persist_time:
    """
    in_view_message(text=text, persist_time=persist_time)
    cmds.warning(text)


def info_message(text: str, persist_time: int = 2000):
    """
    Display an info message in-view and in the log
    :param text:
    :param persist_time:
    """
    in_view_message(text=text, persist_time=persist_time)
    logging.info(text)


def toggle_transform_constraints():
    """
    Toggle the transform constraint mode
    """
    mode = cmds.xformConstraint(query=True, type=True)
    new_mode = 'edge' if mode == 'none' else 'none'
    cmds.xformConstraint(type=new_mode)
    in_view_message(text=f'Tranform constraint set to {new_mode}')
            
    
if __name__ == '__main__':
    toggle_transform_constraint()
    