from django.http import JsonResponse
from django.shortcuts import render
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department


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

def size_chart_json(request):
    labels = []
    data = []
    miscstats = MiscStats.objects.order_by('collected').all()
    for s in miscstats:
        labels.append(s.collected)
        data.append(s.size_total / (1024 * 1024 * 1024))
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
    miscstats = MiscStats.objects.order_by('collected').all()
    for s in miscstats:
        labels.append(s.collected)
        data.append(s.projects_total)
    datasets= [{
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
    miscstats = MiscStats.objects.order_by('collected').all()
    for s in miscstats:
        labels.append(s.collected)
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
