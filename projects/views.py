import math
from django.http import Http404, JsonResponse
from django.shortcuts import render
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, \
    ResearchStats, Person, Datamanager
from datetime import datetime

GB = 1024 * 1024 * 1024
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


def friendly_size(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def calculate_blocks(bytes, block_size=250):
    gigabytes = bytes/(1024*1024*1024)
    return int(math.ceil(gigabytes/block_size))

# Create your views here.
def projects_index(request):
    pr = Project.objects.all().order_by('title')
    data = []
    for p in pr:
        d = CustomObject()
        d.id = p.id
        d.title = p.title
        d.department = p.department.name
        d.faculty = p.department.faculty
        d.requested_size = friendly_size(p.requested_size * GB)
        d.limit = friendly_size(p.storage_limit * GB)
        d = _get_rf(p, d)
        data.append(d)
    d = CustomObject()
    d = _get_rf(None, d)  # unconnected research folders
    d.title = '-'
    d.department = '-'
    d.faculty = '-'
    if d.num_groups > 0:
        data.append(d)
    context = {
        'projects': data
    }
    return render(request, 'projects/index.html', context=context)


def projects_storage(request):
    context = {}
    return render(request, 'projects/storage.html', context=context)


def _get_rf(p, d):
    if p is None:
        rf = ResearchFolder.objects.filter(project__isnull=True)
        d.num_groups = ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True).count()
    else:
        rf = ResearchFolder.objects.filter(project=p)
        d.num_groups = ResearchFolder.objects.filter(project=p, deleted__isnull=True).count()
    d.num_dataset = 0
    d.num_published = 0
    size = 0
    for f in rf:
        if f.deleted is None:
            size = size + ResearchStats.objects.filter(research_folder=f).latest('collected').size
        vf = VaultFolder.objects.get(research_folder=f)
        if vf.deleted is None:
            size = size + VaultStats.objects.filter(vault_folder=vf).latest('collected').size
            cnt = VaultDataset.objects.filter(vault_folder=vf).count()
            pubcnt = VaultDataset.objects.filter(status='PUBLISHED', vault_folder=vf).count()
            d.num_dataset = d.num_dataset + cnt
            d.num_published = d.num_published + pubcnt
    d.size_warning = False
    if p is not None:
        if size > (p.storage_limit * GB):
            d.size_warning = True
    d.size = friendly_size(size)

    return d

def project_detail_data(project_id):
    try:
        project = Project.objects.get(pk=project_id)
        rf = ResearchFolder.objects.filter(project=project)
        data = CustomObject()
        data.project = project
        data.research_folders = []

        total_research_size = 0
        total_vault_size = 0
        for f in rf:
            if f.deleted is not None:
                deleted = True
            else:
                deleted = False
            rf_data = CustomObject()
            rf_data.datamanagers = []
            rf_data.category = f.category
            dms = Datamanager.objects.filter(category=f.category)
            rf_data.datamanagers_object = len(dms)
            for dm in dms:
                rf_data.datamanagers.append(f'{dm.user.firstname} {dm.user.lastname} ({dm.user.vunetid})')
            rf_data.research_name = f.yoda_name
            if deleted:
                rf_data.research_name = f'{rf_data.research_name} [deleted]'
                s = 0
            else:
                latest_stats = ResearchStats.objects.filter(research_folder=f).latest('collected')
                s = latest_stats.size + latest_stats.revision_size
            rf_data.research_size = friendly_size(s)
            total_research_size += s
            vf = VaultFolder.objects.get(research_folder=f)
            rf_data.vault_name = vf.yoda_name
            rf_data.datasets = []
            if vf.deleted is not None:
                rf_data.vault_name = f'{rf_data.vault_name} [deleted]'
                s = 0
            else:
                s = VaultStats.objects.filter(vault_folder=vf).latest('collected').size
                datasets = VaultDataset.objects.filter(vault_folder=vf)
                for dataset in datasets:
                    ds_data = dataset
                    ds_data.name = dataset.yoda_name
                    ds_data.csize = friendly_size(dataset.size)
                    rf_data.datasets.append(ds_data)
            rf_data.vault_size = friendly_size(s)
            total_vault_size += s
            data.research_folders.append(rf_data)
        data.research_size = friendly_size(total_research_size)
        data.research_block_size = '2TB'
        data.research_blocks = calculate_blocks(total_research_size, 2048)
        data.vault_size = friendly_size(total_vault_size)
        data.vault_block_size = '250GB'
        data.vault_blocks = calculate_blocks(total_vault_size, 250)
    except Project.DoesNotExist:
        return None
    return data

def project_detail(request, project_id):
    data = project_detail_data(project_id)
    if data==None:
        raise Http404("Project does not exist")

    return render(request, 'projects/details.html', context={'data': data})


def _vaultstats_quarterly(vault_folder, year, month):
    return VaultStats.objects.filter(vault_folder=vault_folder, collected__year=year,
                                     collected__month__lte=month, collected__month__gt=month-3).order_by('collected').last()


def _researchstats_quarterly(research_folder, year, month):
    return ResearchStats.objects.filter(research_folder=research_folder, collected__year=year,
                                        collected__month__lte=month, collected__month__gt=month-3).order_by('collected').last()

def _vaultstats_month(vault_folder, year, month):
    return VaultStats.objects.filter(vault_folder=vault_folder, collected__year=year,
                                     collected__month=month).order_by('collected').last()


def _researchstats_month(research_folder, year, month):
    return ResearchStats.objects.filter(research_folder=research_folder, collected__year=year,
                                        collected__month=month).order_by('collected').last()


def _monthly_stats(folder, type):
    stats = {}
    last_size = 0
    for year in range(start_year, end_year + 1):
        for month in range(1, 12):
            if type == 'research':
                s = _researchstats_month(folder, year, month)
            elif type == 'vault':
                s = _vaultstats_month(folder, year, month)
            if s is not None:
                size = s.size
                label = f'{year}-{month}'
                stats[label] = {}
                delta = size - last_size
                last_size = size
                stats[label]['size'] = size
                stats[label]['delta'] = delta
    return stats


def _quarterly_research_stats(folder):
    quarters = [3, 6, 9, 12]
    stats = []
    last_size = 0
    last_revision_size = 0
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            s = _researchstats_quarterly(folder, year, month)
            if s is not None:
                s.label = f'{year}-Q{q}'
                s.delta = s.size - last_size
                s.revision_delta = s.revision_size - last_revision_size
                last_size = s.size
                last_revision_size = s.revision_size
                stats.append(s)
            q += 1
    return stats

def _quarterly_vault_stats(folder):
    quarters = [3, 6, 9, 12]
    stats = []
    last_size = 0
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            s = _vaultstats_quarterly(folder, year, month)
            if s is not None:
                s.label = f'{year}-Q{q}'
                s.delta = s.size - last_size
                last_size = s.size
                stats.append(s)
            q += 1
    return stats


def _research_stats(project_id):
    project = Project.objects.get(pk=project_id)
    rf = ResearchFolder.objects.filter(project=project)  # deleted folders should automatically disappear from the stats
    research_stats = {}
    vault_stats = {}
    labels = []
    for f in rf:
        rstats = _quarterly_research_stats(f)
        vf = VaultFolder.objects.get(research_folder=f)
        vstats = _quarterly_vault_stats(vf)
        i = 0
        # Now merge these on label
        for rstat in rstats:
            label=rstat.label
            if label not in labels:
                labels.append(label)
            if label not in research_stats:
                research_stats[label] = {}
                research_stats[label]['size'] = 0
                research_stats[label]['delta'] = 0
                research_stats[label]['revision_size'] = 0
                research_stats[label]['revision_delta'] = 0
            research_stats[label]['size'] += rstat.size
            research_stats[label]['delta'] += rstat.delta
            research_stats[label]['revision_size'] += rstat.revision_size
            research_stats[label]['revision_delta'] += rstat.revision_delta
        for vstat in vstats:
            label=vstat.label
            if label not in labels:
                labels.append(label)
            if label not in vault_stats:
                vault_stats[label] = {}
                vault_stats[label]['size'] = 0
                vault_stats[label]['delta'] = 0
            vault_stats[label]['size'] += vstat.size
            vault_stats[label]['delta'] += vstat.delta
    return sorted(labels), research_stats, vault_stats


def project_size_chart_json(request, project_id):
    research = []
    revision = []
    vault = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = _research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round(research_stats[label]['size'] / div, 2))
        revision.append(round(research_stats[label]['revision_size'] / div, 2))
        vault.append(round(vault_stats[label]['size'] / div, 2))
        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
        {
            'label': 'Revisions',
            'backgroundColor': 'rgba(190,174,212, 0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
            'data': revision,
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
    research = []
    revision = []
    vault = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = _research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round(research_stats[label]['delta'] / div, 2))
        revision.append(round(research_stats[label]['revision_delta'] / div, 2))
        vault.append(round(vault_stats[label]['delta'] / div, 2))
        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
        {
            'label': 'Revisions',
            'backgroundColor': 'rgba(190,174,212, 0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
            'data': revision,
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
