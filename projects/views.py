from django.http import Http404
from django.shortcuts import render
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, ResearchStats, Person, Datamanager

GB=1024*1024*1024

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
        d.id=p.id
        d.title=p.title
        d.department=p.department.name
        d.faculty=p.department.faculty
        d.requested_size=convert_bytes(p.requested_size * GB)
        d.limit=convert_bytes(p.storage_limit * GB)
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
    d.size_warning=False
    if p is not None:
        if size > (p.storage_limit * GB):
            d.size_warning=True
    d.size = convert_bytes(size)

    return d

def project_detail(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
        rf = ResearchFolder.objects.filter(project=project)
        data=CustomObject()
        data.project=project
        data.research_folders=[]

        total_research_size=0
        total_vault_size=0
        for f in rf:
            rf_data = CustomObject()
            rf_data.datamanagers=[]
            rf_data.category=f.category
            dms = Datamanager.objects.filter(category=f.category)
            rf_data.datamanagers_object=len(dms)
            for dm in dms:
                rf_data.datamanagers.append(f'{dm.user.firstname} {dm.user.lastname} ({dm.user.vunetid})')
            rf_data.research_name=f.yoda_name
            s = ResearchStats.objects.filter(research_folder=f).latest('collected').size
            rf_data.research_size = convert_bytes(s)
            total_research_size += s
            vf = VaultFolder.objects.get(research_folder=f)
            rf_data.vault_name = vf.yoda_name
            s = VaultStats.objects.filter(vault_folder=vf).latest('collected').size
            rf_data.vault_size = convert_bytes(s)
            total_vault_size += s
            datasets = VaultDataset.objects.filter(vault_folder=vf)
            rf_data.datasets=[]
            for dataset in datasets:
                ds_data=CustomObject()
                ds_data.status=dataset.status
                ds_data.name=dataset.yoda_name
                rf_data.datasets.append(ds_data)
            data.research_folders.append(rf_data)
        data.research_size=convert_bytes(total_research_size)
        data.vault_size=convert_bytes(total_vault_size)
    except Project.DoesNotExist:
        raise Http404("Project does not exist")

    return render(request, 'projects/details.html', context={'data': data})