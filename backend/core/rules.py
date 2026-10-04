"""帆布浸渍防水台业务规则。"""

from __future__ import annotations

import unicodedata
from decimal import Decimal

from .models import ClothRoll, DipRun, NoteLengthPolicy

MIN_CURE_HOURS_FOR_CURED = Decimal("12")


def latest_dip_run(roll: ClothRoll) -> DipRun | None:
    return roll.dip_runs.order_by("-started_at", "-id").first()


def note_han_char_count(notes: str) -> int:
    """统计备注里的汉字数（CJK 表意文字），标点、数字、空白不计。"""
    if not notes:
        return 0
    count = 0
    for ch in notes:
        if not ch.isspace() and "CJK" in unicodedata.name(ch, ""):
            count += 1
    return count


def validate_dip_note(
    notes: str, policy: NoteLengthPolicy | None = None
) -> tuple[bool, str]:
    """
    浸渍备注字数闸门：落在 [最短, 最长] 汉字数区间外则拒绝整笔。
    空备注（或纯空白）豁免；只约束浸渍备注文本，与其他字段无关。
    """
    if notes is None or not notes.strip():
        return True, ""
    policy = policy or NoteLengthPolicy.load()
    count = note_han_char_count(notes)
    if count < policy.min_chars:
        return (
            False,
            f"浸渍备注汉字数 {count} 少于下限 {policy.min_chars}，本笔登记被拒绝",
        )
    if count > policy.max_chars:
        return (
            False,
            f"浸渍备注汉字数 {count} 超过上限 {policy.max_chars}，本笔登记被拒绝",
        )
    return True, ""



def can_mark_roll_cured(roll: ClothRoll) -> tuple[bool, str]:
    """
    布卷转为「已固化」(cured) 的前提：
    最近一条浸渍记录的固化时长已记录，且 >= 12 小时。
    """
    latest = latest_dip_run(roll)
    if latest is None:
        return False, "该布卷尚无浸渍记录，不能标记为已固化"
    if latest.cure_hours is None:
        return False, "最近浸渍记录尚未填写固化时长，不能标记为已固化"
    if latest.cure_hours < MIN_CURE_HOURS_FOR_CURED:
        return (
            False,
            f"最近浸渍固化时长 {latest.cure_hours} 小时低于 {MIN_CURE_HOURS_FOR_CURED} 小时，不能标记为已固化",
        )
    return True, ""
