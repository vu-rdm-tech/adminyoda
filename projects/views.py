from django.http import Http404, JsonResponse
from django.shortcuts import render
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, \
    ResearchStats, Person, Datamanager
from datetime import datetime
from .tables import ProjectTable, ProjectFilter
from django_tables2 import RequestConfig

GB = 1024 * 1024 * 1024
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


# Create your views here.
def projects_index_table(request):
    f = ProjectFilter(request.GET, queryset=Project.objects.filter(delete_date__isnull=True).all().order_by('title'))
    data = []
    for p in f.qs:
        d = {}
        d['id'] = p.id
        d['title'] = p.title
        d['department'] = p.department.name
        d['faculty'] = p.department.faculty
        d['requested_size'] = p.requested_size
        d['limit'] = p.storage_limit
        d['request_date'] = p.request_date
        d = _get_rf_table(p, d)
        data.append(d)
    d = {}
    d = _get_rf_table(None, d)  # unconnected research folders
    d['title'] = 'Not registered'
    d['department'] = '-'
    d['faculty'] = '-'
    if d['num_groups'] > 0:
        data.append(d)
    
    table = ProjectTable(data)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    return render(request, "projects/index.html", {
        "table": table, 'filter': f
    })


def projects_storage(request):
    context = {}
    return render(request, 'projects/storage.html', context=context)


def _get_rf_table(p, d):
    if p is None:
        rf = ResearchFolder.objects.filter(project__isnull=True)
        d['num_groups'] = ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True).count()
    else:
        rf = ResearchFolder.objects.filter(project=p)
        d['num_groups'] = ResearchFolder.objects.filter(project=p, deleted__isnull=True).count()
    d['num_dataset'] = 0
    d['num_published'] = 0
    size = 0
    for f in rf:
        if f.deleted is None:
            stat = ResearchStats.objects.filter(research_folder=f).latest('collected')
            size = size + stat.size + stat.revision_size
        vf = VaultFolder.objects.get(research_folder=f)
        if vf.deleted is None:
            size = size + VaultStats.objects.filter(vault_folder=vf).latest('collected').size
            cnt = VaultDataset.objects.filter(vault_folder=vf, deleted__isnull=True).count()
            pubcnt = VaultDataset.objects.filter(status='PUBLISHED', vault_folder=vf, deleted__isnull=True).count()
            d['num_dataset'] = d['num_dataset'] + cnt
            d['num_published'] = d['num_published'] + pubcnt
    d['size_warning'] = False
    if p is not None:
        if size > (p.storage_limit * GB):
            d['size_warning'] = True
    d['size'] = round(size / GB, 2)
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
            show = True
            deleted = False
            vf = VaultFolder.objects.get(research_folder=f)
            if f.deleted is not None:
                deleted = True
                if vf.deleted is not None:
                    show = False  # hide groups that were completely deleted
            if show:
                rf_data = CustomObject()
                rf_data.datamanagers = []
                rf_data.category = f.category
                dms = Datamanager.objects.filter(category=f.category)
                rf_data.datamanagers_object = len(dms)
                for dm in dms:
                    rf_data.datamanagers.append(f'{dm.user.firstname} {dm.user.lastname} ({dm.user.email} )')
                rf_data.research_name = f.yoda_name
                if deleted:
                    rf_data.research_name = f'{rf_data.research_name} [deleted]'
                    s = 0
                else:
                    latest_stats = ResearchStats.objects.filter(research_folder=f).latest('collected')
                    s = latest_stats.size + latest_stats.revision_size
                rf_data.research_size = friendly_size(s)
                total_research_size += s
                rf_data.vault_name = vf.yoda_name
                rf_data.datasets = []
                if vf.deleted is not None:
                    rf_data.vault_name = f'{rf_data.vault_name} [deleted]'
                    s = 0
                else:
                    s = VaultStats.objects.filter(vault_folder=vf).latest('collected').size
                    datasets = VaultDataset.objects.filter(vault_folder=vf, deleted__isnull=True)
                    for dataset in datasets:
                        ds_data = dataset
                        ds_data.name = dataset.yoda_name
                        ds_data.csize = friendly_size(dataset.size)
                        rf_data.datasets.append(ds_data)
                rf_data.vault_size = friendly_size(s)
                total_vault_size += s
                data.research_folders.append(rf_data)
        data.research_size_bytes = total_research_size
        data.vault_size_bytes = total_vault_size
        data.research_size = friendly_size(total_research_size)
        data.vault_size = friendly_size(total_vault_size)
    except Project.DoesNotExist:
        return None
    return data


def project_detail(request, project_id):
    data = project_detail_data(project_id)
    if data == None:
        raise Http404("Project does not exist")

    return render(request, 'projects/details.html', context={'data': data})


def _vaultstats_quarterly(vault_folder, year, month):
    return VaultStats.objects.filter(vault_folder=vault_folder, collected__year=year,
                                     collected__month__lte=month, collected__month__gt=month - 3).order_by(
        'collected').last()


def _researchstats_quarterly(research_folder, year, month):
    return ResearchStats.objects.filter(research_folder=research_folder, collected__year=year,
                                        collected__month__lte=month, collected__month__gt=month - 3).order_by(
        'collected').last()


def _vaultstats_month(vault_folder, year, month):
    return VaultStats.objects.filter(vault_folder=vault_folder, collected__year=year,
                                     collected__month=month).order_by('collected').last()


def _researchstats_month(research_folder, year, month):
    return ResearchStats.objects.filter(research_folder=research_folder, collected__year=year,
                                        collected__month=month).order_by('collected').last()


def _monthly_research_stats(folder):
    stats = []
    last_size = 0
    last_revision_size = 0
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            s = _researchstats_month(folder, year, month)
            if s is not None:
                s.label = f'{year}-{str(month).rjust(2, "0")}'
                s.delta = s.size - last_size
                s.revision_delta = s.revision_size - last_revision_size
                last_size = s.size
                last_revision_size = s.revision_size
                s.total_size = s.size + s.revision_size
                stats.append(s)
    return stats


def _monthly_vault_stats(folder):
    stats = []
    last_size = 0
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            s = _vaultstats_month(folder, year, month)
            if s is not None:
                s.label = f'{year}-{str(month).rjust(2, "0")}'
                s.delta = s.size - last_size
                last_size = s.size
                stats.append(s)
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


def project_research_stats(project_id):
    project = Project.objects.get(pk=project_id)
    rf = ResearchFolder.objects.filter(project=project)  # deleted folders should automatically disappear from the stats
    research_stats = {}
    vault_stats = {}
    labels = []
    for f in rf:
        # rstats = _quarterly_research_stats(f)
        rstats = _monthly_research_stats(f)
        vf = VaultFolder.objects.get(research_folder=f)
        # vstats = _quarterly_vault_stats(vf)
        vstats = _monthly_vault_stats(vf)
        i = 0
        # Now merge these on label
        for rstat in rstats:
            label = rstat.label
            if label not in labels:
                labels.append(label)
            if label not in research_stats:
                research_stats[label] = {}
                research_stats[label]['size'] = 0
                research_stats[label]['delta'] = 0
                research_stats[label]['revision_size'] = 0
                research_stats[label]['revision_delta'] = 0
                research_stats[label]['total_size'] = 0
            research_stats[label]['total_size'] += rstat.total_size
            research_stats[label]['size'] += rstat.size
            research_stats[label]['delta'] += rstat.delta
            research_stats[label]['revision_size'] += rstat.revision_size
            research_stats[label]['revision_delta'] += rstat.revision_delta
        for vstat in vstats:
            label = vstat.label
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
    labels, research_stats, vault_stats = project_research_stats(project_id)
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


def project_research_size_chart_json(request, project_id):
    research = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = project_research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round((research_stats[label]['size'] + research_stats[label]['revision_size']) / div, 2))

        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
            'borderWidth': 1,
            'data': research,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_research_revision_size_chart_json(request, project_id):
    research = []
    revision = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = project_research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round(research_stats[label]['size'] / div, 2))
        revision.append(round(research_stats[label]['revision_size'] / div, 2))
        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
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
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_vault_size_chart_json(request, project_id):
    vault = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = project_research_stats(project_id)
    i = 0
    for label in labels:
        if label in vault_stats:
            vault.append(round(vault_stats[label]['size'] / div, 2))
        else:
            vault.append(0)
        i += 1
    datasets = [
        {
            'label': 'Vault',
            'backgroundColor': 'rgb(217, 248, 154, 0.4)',
            'borderColor': 'rgb(217, 248, 154)',
            'borderWidth': 1,
            'data': vault,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_delta_chart_json(request, project_id):
    research = []
    vault = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = project_research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round((research_stats[label]['delta'] + research_stats[label]['revision_delta']) / div, 2))
        if label in vault_stats:
            vault.append(round(vault_stats[label]['delta'] / div, 2))
        else:
            vault.append(0)
        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
            'borderWidth': 1,
            'data': research,
        },
        {
            'label': 'Vault',
            'backgroundColor': 'rgb(217, 248, 154, 0.4)',
            'borderColor': 'rgb(217, 248, 154)',
            'borderWidth': 1,
            'data': vault,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_delta_with_revision_chart_json(request, project_id):
    research = []
    revision = []
    vault = []
    div = (1024 * 1024 * 1024)
    labels, research_stats, vault_stats = project_research_stats(project_id)
    i = 0
    for label in labels:
        research.append(round(research_stats[label]['delta'] / div, 2))
        revision.append(round(research_stats[label]['revision_delta'] / div, 2))
        vault.append(round(vault_stats[label]['delta'] / div, 2))
        i += 1
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
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