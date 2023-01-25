from django.contrib import admin

# Register your models here.
from .models import Person, Project, Budget, Department, ResearchFolder, VaultFolder, VaultDataset, ResearchStats, VaultStats, VaultDataset

admin.site.site_header = 'Yoda project administration'


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0



class ResearchFolderInline(admin.StackedInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    model=ResearchFolder
    extra = 0

class VaultFolderInline(admin.StackedInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    model=VaultFolder
    extra = 0

class VaultDatasetInline(admin.StackedInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    model=VaultDataset
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ["title", "owner", "department", "research_folders"]
    ordering = ["title"]
    inlines=[
        ResearchFolderInline,
    ]
    def research_folders(self, obj):
        return ResearchFolder.objects.filter(project=obj).count()

class PersonAdmin(admin.ModelAdmin):
    ordering = ["email"]
    list_display = ["email", "lastname", "firstname", "vunetid"]

class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["faculty", "name"]

class ResearchAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ("yoda_name", "category", "project", "size", "data_classification", "datasets", "deleted")
    ordering = ["yoda_name"]
    inlines=[
        VaultFolderInline,
    ]
    def size(self, obj):
        # most recent size of the research folder
        researchsize = ResearchStats.objects.filter(research_folder=obj).latest('collected').size
        # most recent size of the vault folder
        vault = VaultFolder.objects.get(research_folder=obj)
        vaultsize = VaultStats.objects.filter(vault_folder=vault).latest('collected').size
        total=researchsize+vaultsize
        # return total
        return convert_bytes(total)

    def datasets(self, obj):
        # return number of datasets in vault
        vault = VaultFolder.objects.get(research_folder=obj)
        return VaultDataset.objects.filter(vault_folder=vault).count()


class VaultAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    ordering = ["yoda_name"]
    inlines=[
        VaultDatasetInline,
    ]

admin.site.register(Person, PersonAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Budget)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(ResearchFolder, ResearchAdmin)
admin.site.register(VaultFolder, VaultAdmin)

