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
    num_projects=Project.objects.all().count
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
    labels=[]
    data=[]
    miscstats = MiscStats.objects.all()
    for s in miscstats:
        labels.append(s.collected)
        data.append(s.size_total/(1024*1024*1024))
    return JsonResponse(data={'labels': labels, 'data': data})

def user_chart_json(request):
    labels=[]
    data=[]
    miscstats = MiscStats.objects.all()
    for s in miscstats:
        labels.append(s.collected)
        data.append(s.users_total)
    return JsonResponse(data={'labels': labels, 'data': data})