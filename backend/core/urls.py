from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClothRollViewSet,
    DipRunViewSet,
    LoftViewSet,
    NoteLengthRuleView,
    dashboard_stats,
)

router = DefaultRouter()
router.register("lofts", LoftViewSet, basename="loft")
router.register("rolls", ClothRollViewSet, basename="roll")
router.register("dips", DipRunViewSet, basename="dip")

urlpatterns = [
    path("dashboard/", dashboard_stats, name="dashboard"),
    path("note-length-rule/", NoteLengthRuleView.as_view(), name="note-length-rule"),
    path("", include(router.urls)),
]
