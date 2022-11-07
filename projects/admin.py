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
    model=ResearchFolder
    extra = 0

class VaultFolderInline(admin.StackedInline):
    model=VaultFolder
    extra = 0

class VaultDatasetInline(admin.StackedInline):
    model=VaultDataset
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    ordering = ["title"]
    inlines=[
        ResearchFolderInline,
        #VaultFolderInline,
        #VaultDatasetInline,
    ]

class PersonAdmin(admin.ModelAdmin):
    ordering = ["email"]

class ResearchAdmin(admin.ModelAdmin):
    list_display = ("yoda_name", "category", "project", "size", "datasets", "deleted")
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
    ordering = ["yoda_name"]
    inlines=[
        VaultDatasetInline,
    ]

admin.site.register(Person, PersonAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Budget)
admin.site.register(Department)
admin.site.register(ResearchFolder, ResearchAdmin)
admin.site.register(VaultFolder, VaultAdmin)

