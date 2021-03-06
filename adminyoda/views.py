from django.http import JsonResponse
from django.shortcuts import render
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department
from datetime import datetime
from django.db.models import Sum

start_month = 6
start_year = 2021
today = datetime.now()
end_month = today.month
end_year = today.year
COLORSET = ['rgba(141,211,199)', 'rgba(255,255,179)', 'rgba(190,186,218)', 'rgba(251,128,114)', 'rgba(128,177,211)',
            'rgba(253,180,98)', 'rgba(179,222,105)', 'rgba(252,205,229)', 'rgba(217,217,217)', 'rgba(188,128,189)',
            'rgba(204,235,197)', 'rgba(255,237,111)']


def _convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


# Create your views here.
def index(request):
    num_projects = Project.objects.filter(delete_date__isnull=True).all().count
    requested_size = Project.objects.aggregate(total=Sum('requested_size'))['total'] / 1024  # TB
    miscstats = MiscStats.objects.latest('collected')
    context = {
        'num_projects': num_projects,
        'total_size': _convert_bytes(miscstats.size_total + miscstats.revision_size),
        'requested_size': round(requested_size, 1),
        'num_users': miscstats.users_total,
        'num_datasets': VaultDataset.objects.filter(deleted__isnull=True).all().count,
        'last_updated': miscstats.collected,
        'num_groups': ResearchFolder.objects.filter(deleted__isnull=True).all().count,
        'num_published': VaultDataset.objects.filter(status='PUBLISHED').all().count,
        'num_departments': Department.objects.count()
    }
    return render(request, 'index.html', context=context)


def _quarterly_miscstats():
    quarters = [3, 6, 9, 12]
    stats = []
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            s = MiscStats.objects.filter(collected__year=year, collected__month__lte=month, collected__month__gt=month-3).order_by('collected').last()
            if s is not None:
                 s.label = f'{year}-Q{q}'
                 stats.append(s)
            q += 1
    return stats


def _monthly_miscstats():
    stats = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            s = MiscStats.objects.filter(collected__year=year, collected__month=month).order_by('collected').last()
            if s is not None:
                #s.label = s.collected
                s.label = f'{year}-{month}'
                stats.append(s)
    return stats


def _all_miscstats():
    stats = []
    for s in MiscStats.objects.order_by('collected').all():
        s.label = s.collected
        stats.append(s)
    return stats


def size_chart_json(request):
    labels = []
    research = []
    vault = []
    div = (1024 * 1024 * 1024)
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(round(s.size_research / div, 2)+round(s.revision_size / div, 2))
        vault.append(round(s.size_vault / div, 2))
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


def project_chart_json(request):
    labels = []
    data = []
    miscstats = _quarterly_miscstats()
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
    miscstats = _quarterly_miscstats()
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
    stats = _quarterly_miscstats()
    # stats = _get_quarterly_miscstats()
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
            'data': research,
        },
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault,
        },
        {
            'label': 'Revisions',
            'backgroundColor': 'rgba(190,174,212,  0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
            'data': revisions,
        },
        {
            'label': 'Trash',
            'backgroundColor': 'rgba(56,108,176, 0.4)',
            'borderColor': 'rgba(56,108,176)',
            'borderWidth': 1,
            'data': trash,
        },

    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def faculty_chart_json(request):
    labels = []
    data = []
    index = {}
    i = 0
    colors = []
    projects = Project.objects.order_by('department').all()
    for project in projects:
        faculty = Department.objects.get(id=project.department.id).faculty
        if faculty not in labels:
            index[faculty] = i
            data.append(0)
            labels.append(faculty)
            colors.append(COLORSET[i])
            i += 1
        data[index[faculty]] += 1
    datasets = [{
        'label': 'Faculty',
        'backgroundColor': colors,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})
