from maya import cmds


class UndoStack:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        cmds.undoInfo(openChunk=True, chunkName=self.name, infinity=True)

    def __exit__(self, typ, val, tb):
        cmds.undoInfo(closeChunk=True)
