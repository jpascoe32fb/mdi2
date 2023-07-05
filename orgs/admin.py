from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Severity)
admin.site.register(Technology)
admin.site.register(Analyst)
admin.site.register(Condition)
admin.site.register(Unit)
admin.site.register(Report)


admin.site.register(UnitName)
admin.site.register(Function)
admin.site.register(Asset)
admin.site.register(Component)
admin.site.register(PlantTag)

admin.site.register(FaultGroup)