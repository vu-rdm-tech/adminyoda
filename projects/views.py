from django.shortcuts import render
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, ResearchStats

class CustomObject():
    pass

def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

# Create your views here.
def projects_index(request):
    pr = Project.objects.all().order_by('title')
    data = []
    for p in pr:
        d = CustomObject()
        d.title=p.title
        d.department=p.department.name
        d.faculty=p.department.faculty
        d = _get_rf(p,d)
        data.append(d)
    d = CustomObject()
    d.title = '-'
    d.department = '-'
    d.faculty = '-'
    d = _get_rf(None, d)
    data.append(d)
    context = {
        'projects': data
    }
    return render(request, 'projects/index.html', context=context)

def projects_storage(request):
    context={}
    return render(request, 'projects/storage.html', context=context)

def _get_rf(p, d):
    if p is None:
        rf = ResearchFolder.objects.filter(project__isnull=True)
    else:
        rf = ResearchFolder.objects.filter(project=p)
    d.num_groups = rf.count()
    d.num_dataset = 0
    d.num_published = 0
    size = 0
    for f in rf:
        size = size + ResearchStats.objects.filter(research_folder=f).latest('collected').size
        vf = VaultFolder.objects.get(research_folder=f)
        size = size + VaultStats.objects.filter(vault_folder=vf).latest('collected').size
        cnt = VaultDataset.objects.filter(vault_folder=vf).count()
        pubcnt = VaultDataset.objects.filter(status='PUBLISHED', vault_folder=vf).count()
        d.num_dataset = d.num_dataset + cnt
        d.num_published = d.num_published + pubcnt
    d.size = convert_bytes(size)
    return d