"""帆布浸渍防水台业务规则。"""

from __future__ import annotations

from decimal import Decimal

from .models import ClothRoll, DipRun, NoteLengthRule

MIN_CURE_HOURS_FOR_CURED = Decimal("12")


def latest_dip_run(roll: ClothRoll) -> DipRun | None:
    return roll.dip_runs.order_by("-started_at", "-id").first()


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


def check_dip_notes_length(notes: str | None) -> tuple[bool, str]:
    """
    浸渍备注字数校验（面板登记与浸渍台账共用）：
    空备注不校验；非空备注字数须落在管理员设定的 [最短, 最长] 区间内，
    落在区间外则整笔拒绝（校验先于落库，不先插入再改）。
    """
    text = notes or ""
    if text == "":
        return True, ""
    rule = NoteLengthRule.load()
    count = len(text)
    if count < rule.min_chars:
        return False, f"备注太短：当前 {count} 字，最少 {rule.min_chars} 字"
    if count > rule.max_chars:
        return False, f"备注太长：当前 {count} 字，最多 {rule.max_chars} 字"
    return True, ""
