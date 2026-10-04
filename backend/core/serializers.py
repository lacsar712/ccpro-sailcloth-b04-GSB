from rest_framework import serializers

from .models import ClothRoll, DipRun, Loft, NoteLengthPolicy
from .rules import can_mark_roll_cured, validate_dip_note


class LoftSerializer(serializers.ModelSerializer):
    rollCount = serializers.SerializerMethodField()

    class Meta:
        model = Loft
        fields = ("id", "name", "location", "notes", "rollCount", "created_at")
        read_only_fields = ("id", "rollCount", "created_at")

    def get_rollCount(self, obj):
        if hasattr(obj, "roll_count"):
            return obj.roll_count
        return obj.rolls.count()


class ClothRollSerializer(serializers.ModelSerializer):
    loftId = serializers.PrimaryKeyRelatedField(source="loft", queryset=Loft.objects.all())
    rollCode = serializers.CharField(source="roll_code")
    fabricWeightGsm = serializers.IntegerField(source="fabric_weight_gsm", required=False)
    loftName = serializers.CharField(source="loft.name", read_only=True)

    class Meta:
        model = ClothRoll
        fields = (
            "id",
            "loftId",
            "loftName",
            "rollCode",
            "status",
            "fabricWeightGsm",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "loftName", "created_at", "updated_at")

    def validate(self, attrs):
        loft = attrs.get("loft") or getattr(self.instance, "loft", None)
        roll_code = attrs.get("roll_code") or getattr(self.instance, "roll_code", None)
        if loft and roll_code:
            qs = ClothRoll.objects.filter(loft=loft, roll_code=roll_code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"rollCode": "同一帆布间卷号必须唯一"})

        new_status = attrs.get("status")
        if new_status == ClothRoll.STATUS_CURED:
            roll = self.instance
            if roll is None:
                raise serializers.ValidationError(
                    {"status": "新建布卷不能直接设为已固化"}
                )
            # 合并未提交字段到临时视角：用当前实例校验
            ok, msg = can_mark_roll_cured(roll)
            if not ok:
                raise serializers.ValidationError({"status": msg})
        return attrs


class DipRunSerializer(serializers.ModelSerializer):
    rollId = serializers.PrimaryKeyRelatedField(
        source="roll", queryset=ClothRoll.objects.all()
    )
    startedAt = serializers.DateTimeField(source="started_at")
    resinPct = serializers.DecimalField(source="resin_pct", max_digits=5, decimal_places=2)
    cureHours = serializers.DecimalField(
        source="cure_hours",
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    rollCode = serializers.CharField(source="roll.roll_code", read_only=True)
    loftName = serializers.CharField(source="roll.loft.name", read_only=True)

    class Meta:
        model = DipRun
        fields = (
            "id",
            "rollId",
            "rollCode",
            "loftName",
            "startedAt",
            "resinPct",
            "cureHours",
            "notes",
            "created_at",
        )
        read_only_fields = ("id", "rollCode", "loftName", "created_at")

    def validate(self, attrs):
        # 面板登记与浸渍台账保存走同一入口：备注越界即在保存前整笔拒绝，
        # serializer 不通过 -> 不会进入 create()，库里绝不会先出现该备注。
        notes = attrs.get("notes")
        if notes is None and self.instance is not None:
            notes = self.instance.notes
        ok, msg = validate_dip_note(notes or "")
        if not ok:
            raise serializers.ValidationError({"notes": msg})
        return attrs


class NoteLengthPolicySerializer(serializers.ModelSerializer):
    minChars = serializers.IntegerField(source="min_chars", min_value=1)
    maxChars = serializers.IntegerField(source="max_chars", min_value=1)

    class Meta:
        model = NoteLengthPolicy
        fields = ("id", "minChars", "maxChars", "updated_at")
        read_only_fields = ("id", "updated_at")

    def validate(self, attrs):
        min_chars = attrs.get("min_chars", getattr(self.instance, "min_chars", 1))
        max_chars = attrs.get("max_chars", getattr(self.instance, "max_chars", 200))
        if min_chars > max_chars:
            raise serializers.ValidationError(
                {"maxChars": "最长汉字数不能小于最短汉字数"}
            )
        return attrs
