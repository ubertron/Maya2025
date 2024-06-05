from maya import cmds
from typing import Optional

from maya_tools.maya_enums import ObjectType


def get_keyframe_range(node: str, include_children: bool = False) -> tuple or None:
    """
    Get the range of keyframes on a selected node
    :param node:
    :param include_children:
    """
    all_frame_ranges = []

    def get_frame_ranges_from_node(node_name: str) -> list or None:
        anim_curves = cmds.listConnections(node_name, type=ObjectType.animCurve.name)
        ranges = []

        if anim_curves:
            for anim_curve in anim_curves:
                frame_range = get_anim_curve_frame_range(anim_curve)
                if frame_range:
                    ranges.append(frame_range)
        return ranges

    if include_children:
        all_children = cmds.listRelatives(node, allDescendents=True, fullPath=True)

        for child in all_children:
            frame_ranges = get_frame_ranges_from_node(node_name=child)
            if frame_ranges:
                all_frame_ranges.extend(frame_ranges)
    else:
        all_frame_ranges = get_frame_ranges_from_node(node_name=node)

    if all_frame_ranges:
        return min(x[0] for x in all_frame_ranges), max(x[1] for x in all_frame_ranges)


def get_anim_curve_frame_range(anim_curve: str) -> tuple or None:
    """
    Get the first and last keyframes of an animCurve
    :param anim_curve:
    :return:
    """
    num_keys = cmds.keyframe(anim_curve, query=True, keyframeCount=True)

    if num_keys:
        first_key = cmds.keyframe(anim_curve, query=True, index=(0,))
        last_key = cmds.keyframe(anim_curve, query=True, index=(num_keys - 1,))

        if first_key and last_key:
            return first_key[0], last_key[0]


def set_playback_range(start_frame: float, end_frame: float, start_range: Optional[float] = None,
                       end_range: Optional[float] = None, current_time: Optional[float] = None):
    """
    Set the playback range
    :param start_frame:
    :param end_frame:
    :param start_range:
    :param end_range:
    :param current_time:
    """
    pm.playbackOptions(
        animationStartTime=start_frame,
        animationEndTime=end_frame,
        minTime=start_range if start_range else start_frame,
        maxTime=end_range if end_range else end_frame
    )

    pm.currentTime(current_time if current_time else pm.playbackOptions(query=True, minTime=True))


def get_playback_range(full_range_only: bool = False) -> tuple[float]:
    """
    Query the playback range
    :return:
    """
    start_time = cmds.playbackOptions(query=True, animationStartTime=True)
    end_time = cmds.playbackOptions(query=True, animationEndTime=True)
    min_time = cmds.playbackOptions(query=True, minTime=True)
    max_time = cmds.playbackOptions(query=True, maxTime=True)

    return (start_time, end_time) if full_range_only else (start_time, end_time, min_time, max_time)
