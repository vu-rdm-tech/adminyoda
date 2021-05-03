from django.contrib import admin

# Register your models here.
from .models import Person, Project, Budget, Department, ResearchFolder

admin.site.site_header = 'Yoda project administration'

class ResearchFolderInline(admin.StackedInline):
    model=ResearchFolder
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    inlines=[
        ResearchFolderInline,
    ]

admin.site.register(Person)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Budget)
admin.site.register(Department)
#admin.site.register(ResearchFolder)