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


class ProjectInline(admin.TabularInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    fields = ('id','owner', 'department', 'request_date', 'delete_date')
    readonly_fields = ('owner', 'department', 'request_date', 'delete_date')
    model=Project
    show_change_link = True
    extra = 0

class ResearchFolderInline(admin.TabularInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    fields = ('category', 'data_classification', 'internal_users', 'external_users', 'sram_open_invitations', 'sram_memberships', 'deleted')
    readonly_fields = ('category', 'data_classification', 'internal_users', 'external_users', 'sram_open_invitations', 'sram_memberships', 'deleted')
    model=ResearchFolder
    extra = 0

class VaultFolderInline(admin.TabularInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    model=VaultFolder
    fields = ('yoda_name', 'deleted')
    readonly_fields =  ('yoda_name', 'deleted')
    extra = 0

class VaultDatasetInline(admin.TabularInline):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    model=VaultDataset
    fields = ('yoda_name', 'status', 'retention', 'size', 'data_classification', 'deleted')
    readonly_fields = ('yoda_name', 'status', 'retention', 'size', 'data_classification', 'deleted')
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ["title", "owner", "department", "research_folders", "delete_date"]
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
    def has_delete_permission(self, request, obj=None):
        return False
    ordering = ["faculty", "name"]
    list_display = ["faculty", "name", "abbreviation", "projects"]
    inlines=[
        ProjectInline
    ]
    def projects(self, obj):
        return Project.objects.filter(department=obj).count()

class BudgetAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
    ordering = ["code"]
    list_display = ["code", "type", "vunetid", "projects"]

    inlines=[
        ProjectInline
    ]
    def projects(self, obj):
        return Project.objects.filter(budget=obj).count()

class ResearchAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ("yoda_name", "category", "project", "size", "data_classification", "datasets", "newest_file", "created", "deleted")
    readonly_fields = ("yoda_name", "category", "data_classification", "internal_users", "external_users", "sram_co_id", "sram_open_invitations", "sram_memberships", "datasets", "newest_file", "created", "deleted")
    ordering = ["yoda_name"]
    inlines=[
        VaultFolderInline,
    ]
    def newest_file(self, obj):
        return ResearchStats.objects.filter(research_folder=obj).latest('collected').newest_file

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
    readonly_fields =  ('research_folder', 'yoda_name', 'deleted')
    ordering = ["yoda_name"]
    inlines=[
        VaultDatasetInline,
    ]

admin.site.register(Person, PersonAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Budget, BudgetAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(ResearchFolder, ResearchAdmin)
admin.site.register(VaultFolder, VaultAdmin)

