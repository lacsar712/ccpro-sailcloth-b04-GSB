from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClothRoll, DipRun, Loft, NoteLengthRule
from .permissions import IsAdminRole
from .serializers import (
    ClothRollSerializer,
    DipRunSerializer,
    LoftSerializer,
    NoteLengthRuleSerializer,
)


class LoftViewSet(viewsets.ModelViewSet):
    queryset = Loft.objects.annotate(roll_count=Count("rolls")).all()
    serializer_class = LoftSerializer


class ClothRollViewSet(viewsets.ModelViewSet):
    serializer_class = ClothRollSerializer

    def get_queryset(self):
        qs = ClothRoll.objects.select_related("loft").all()
        loft_id = self.request.query_params.get("loftId")
        status = self.request.query_params.get("status")
        if loft_id:
            qs = qs.filter(loft_id=loft_id)
        if status:
            qs = qs.filter(status=status)
        return qs


class DipRunViewSet(viewsets.ModelViewSet):
    serializer_class = DipRunSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = DipRun.objects.select_related("roll", "roll__loft").all()
        roll_id = self.request.query_params.get("rollId")
        if roll_id:
            qs = qs.filter(roll_id=roll_id)
        return qs


class NoteLengthRuleView(APIView):
    """备注字数规则：登录用户均可读取，仅管理员可修改。"""

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get(self, request):
        return Response(NoteLengthRuleSerializer(NoteLengthRule.load()).data)

    def put(self, request):
        return self._save(request, partial=False)

    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial):
        serializer = NoteLengthRuleSerializer(
            NoteLengthRule.load(), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    data = {
        "loftCount": Loft.objects.count(),
        "rawRollCount": ClothRoll.objects.filter(status=ClothRoll.STATUS_RAW).count(),
        "dippingRollCount": ClothRoll.objects.filter(
            status=ClothRoll.STATUS_DIPPING
        ).count(),
        "curedRollCount": ClothRoll.objects.filter(status=ClothRoll.STATUS_CURED).count(),
        "dipRunCount": DipRun.objects.count(),
    }
    return Response(data)
