from django.http import Http404, JsonResponse
from django.shortcuts import render
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, ResearchStats, Person, Datamanager
from datetime import datetime

GB=1024*1024*1024
start_month = 6
start_year = 2021
today = datetime.now()
end_month = today.month
end_year = today.year
COLORSET = ['rgba(141,211,199)', 'rgba(255,255,179)', 'rgba(190,186,218)', 'rgba(251,128,114)', 'rgba(128,177,211)',
            'rgba(253,180,98)', 'rgba(179,222,105)', 'rgba(252,205,229)', 'rgba(217,217,217)', 'rgba(188,128,189)',
            'rgba(204,235,197)', 'rgba(255,237,111)']

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
    d = _get_rf(None, d) # unconnected research folders
    d.title = '-'
    d.department = '-'
    d.faculty = '-'
    if d.num_groups>0:
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
        rf = ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True)
    else:
        rf = ResearchFolder.objects.filter(project=p, deleted__isnull=True)
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
            if f.deleted is not None:
                deleted=True
            else:
                deleted=False
            rf_data = CustomObject()
            rf_data.datamanagers=[]
            rf_data.category=f.category
            dms = Datamanager.objects.filter(category=f.category)
            rf_data.datamanagers_object=len(dms)
            for dm in dms:
                rf_data.datamanagers.append(f'{dm.user.firstname} {dm.user.lastname} ({dm.user.vunetid})')
            rf_data.research_name=f.yoda_name
            if deleted:
                rf_data.research_name=f'{rf_data.research_name} [deleted]'
                s = 0
            else:
                s = ResearchStats.objects.filter(research_folder=f).latest('collected').size
            rf_data.research_size = convert_bytes(s)
            total_research_size += s
            vf = VaultFolder.objects.get(research_folder=f)
            rf_data.vault_name = vf.yoda_name
            if vf.deleted is not None:
                rf_data.vault_name = f'{rf_data.vault_name} [deleted]'
                s = 0
            else:
                s = VaultStats.objects.filter(vault_folder=vf).latest('collected').size
                datasets = VaultDataset.objects.filter(vault_folder=vf)
                rf_data.datasets=[]
                for dataset in datasets:
                    ds_data=CustomObject()
                    ds_data.status=dataset.status
                    ds_data.name=dataset.yoda_name
                    rf_data.datasets.append(ds_data)
            rf_data.vault_size = convert_bytes(s)
            total_vault_size += s
            data.research_folders.append(rf_data)
        data.research_size=convert_bytes(total_research_size)
        data.vault_size=convert_bytes(total_vault_size)
    except Project.DoesNotExist:
        raise Http404("Project does not exist")

    return render(request, 'projects/details.html', context={'data': data})

def _monthly_researchstats(research_folder):
    stats = []
    for year in range(start_year, end_year + 1):
        last_size=0
        for month in range(1, 12):
            s = ResearchStats.objects.filter(research_folder=research_folder, collected__year=year, collected__month=month).order_by('collected').last()
            if s is not None:
                s.label = f'{year}-{month}'
                s.delta=s.size-last_size
                last_size=s.size
                stats.append(s)
        stats[0].delta=0
    return stats

def _monthly_vaultstats(vault_folder):
    stats = []
    for year in range(start_year, end_year + 1):
        last_size=0
        for month in range(1, 13):
            s = VaultStats.objects.filter(vault_folder=vault_folder, collected__year=year, collected__month=month).order_by('collected').last()
            if s is not None:
                s.label = f'{year}-{month}'
                s.delta=s.size-last_size
                last_size=s.size
                #s.label = s.collected
                stats.append(s)
        stats[0].delta=0
    return stats

def _research_stats(project_id):
    project = Project.objects.get(pk=project_id)
    rf = ResearchFolder.objects.filter(project=project, deleted__isnull=True)
    research_stats=[]
    vault_stats=[]
    for f in rf:
        rstats = _monthly_researchstats(f)
        vf = VaultFolder.objects.get(research_folder=f)
        vstats = _monthly_vaultstats(vf)
        i=0
        for rs in rstats:
            if len(research_stats) >= i+1:
                research_stats[i].size += rs.size
                vault_stats[i].size += vstats[i].size
                research_stats[i].delta += rs.delta
                vault_stats[i].delta += vstats[i].delta
            else:
                research_stats.append(rs)
                vault_stats.append(vstats[i])
            i+=1
    return research_stats, vault_stats

def project_size_chart_json(request, project_id):
    labels = []
    research = []
    vault = []
    div = (1024 * 1024 * 1024)
    research_stats, vault_stats = _research_stats(project_id)
    i=0
    for rs in research_stats:
        labels.append(rs.label)
        research.append(round(rs.size / div, 2))
        vault.append(round(vault_stats[i].size / div, 2))
        i+=1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})

def project_delta_chart_json(request, project_id):
    labels = []
    research = []
    vault = []
    div = (1024 * 1024 * 1024)
    research_stats, vault_stats = _research_stats(project_id)
    i=0
    for rs in research_stats:
        labels.append(rs.label)
        research.append(round(rs.delta / div, 2))
        vault.append(round(vault_stats[i].delta / div, 2))
        i+=1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})