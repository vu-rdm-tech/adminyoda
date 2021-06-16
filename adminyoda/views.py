from django.http import JsonResponse
from django.shortcuts import render
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department
from datetime import datetime

start_month = 6
start_year = 2021
today = datetime.now()
end_month = today.month
end_year = today.year
quarters = [3, 6, 9, 12]


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


# Create your views here.
def index(request):
    num_projects = Project.objects.all().count
    miscstats = MiscStats.objects.latest('collected')
    context = {
        'num_projects': num_projects,
        'total_size': convert_bytes(miscstats.size_total),
        'num_users': miscstats.users_total,
        'num_datasets': VaultDataset.objects.all().count,
        'last_updated': miscstats.collected,
        'num_groups': ResearchFolder.objects.all().count,
        'num_published': VaultDataset.objects.filter(status='PUBLISHED').all().count,
        'num_departments': Department.objects.count()
    }
    return render(request, 'index.html', context=context)


def _get_quarterly_miscstats():
    stats = []
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            if not ((year == start_year and month < start_month) or (year == end_year and month > end_month)):
                s = MiscStats.objects.filter(collected__year=year, collected__month__lte = month).order_by('collected').last()
                s.label = f'Q{q}-{year}'
                stats.append(s)
            q += 1
    return stats


def _get_monthly_miscstats():
    stats = []
    for year in range(start_year, end_year + 1):
        if year == start_year:
            m1 = start_month
        else:
            m1 = 1
        if year == end_year:
            m2 = end_month
        else:
            m2 = 12
        for month in range(m1, m2 + 1):
            s = MiscStats.objects.filter(collected__year=year, collected__month=month).order_by('collected').last()
            s.label = f'{year}-{month}'
            stats.append(s)
    return stats


def _get_all_miscstats():
    stats = []
    for s in MiscStats.objects.order_by('collected').all():
        s.label = s.collected
        stats.append(s)
    return stats


def size_chart_json(request):
    labels = []
    data = []
    miscstats = _get_all_miscstats()
    for s in miscstats:
        labels.append(s.label)
        data.append(round(s.size_total / (1024 * 1024 * 1024), 2))
    datasets = [{
        'label': 'Total size (GB)',
        'backgroundColor': 'rgba(253,192,134, 0.4)',
        'borderColor': 'rgba(253,192,134)',
        'borderWidth': 1,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_chart_json(request):
    labels = []
    data = []
    miscstats = _get_all_miscstats()
    for s in miscstats:
        labels.append(s.label)
        data.append(s.projects_total)
    datasets = [{
        'label': 'Projects',
        'backgroundColor': 'rgba(56,108,176, 0.4)',
        'borderColor': 'rgba(56,108,176)',
        'borderWidth': 1,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def user_chart_json(request):
    labels = []
    internal = []
    external = []
    miscstats = _get_all_miscstats()
    for s in miscstats:
        labels.append(s.label)
        internal.append(s.internal_users_total)
        external.append(s.external_users_total)
    datasets = [
        {
            'label': 'internal',
            'data': internal,
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
        },
        {
            'label': 'external',
            'data': external,
            'backgroundColor': 'rgba(190,174,212,  0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def storage_chart_json(request):
    labels = []
    research = []
    vault = []
    revisions = []
    trash = []
    div = (1024 * 1024 * 1024)
    stats = _get_monthly_miscstats()
    #stats = _get_quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(round(s.size_research / div, 2))
        vault.append(round(s.size_vault / div, 2))
        revisions.append(round(s.revision_size / div, 2))
        trash.append(round(s.trash_size / div, 2))
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research
        },
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault
        },
        {
            'label': 'Revisions',
            'backgroundColor': 'rgba(190,174,212,  0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
            'data': revisions
        },
        {
            'label': 'Trash',
            'backgroundColor': 'rgba(56,108,176, 0.4)',
            'borderColor': 'rgba(56,108,176)',
            'borderWidth': 1,
            'data': trash
        },

    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})
