from django.contrib import admin

from .models import ClothRoll, DipRun, Loft, NoteLengthRule

admin.site.register(Loft)
admin.site.register(ClothRoll)
admin.site.register(DipRun)
admin.site.register(NoteLengthRule)
