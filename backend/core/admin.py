from django.contrib import admin

from .models import ClothRoll, DipRun, Loft, NoteLengthPolicy

admin.site.register(Loft)
admin.site.register(ClothRoll)
admin.site.register(DipRun)


@admin.register(NoteLengthPolicy)
class NoteLengthPolicyAdmin(admin.ModelAdmin):
    list_display = ("id", "min_chars", "max_chars", "updated_at")

    def has_add_permission(self, request):
        return not NoteLengthPolicy.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
