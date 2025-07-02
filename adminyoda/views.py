from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import now, make_aware
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department, ResearchStats
from datetime import datetime, timedelta
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from projects.reports import generate_yearly_report, generate_statistics_report
import mimetypes
import logging

logger = logging.getLogger(__name__)

GB = 1024 * 1024 * 1024
start_year = 2023
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

# divide bytes by divTB to get TeraBytes
divTB = (1024 * 1024 * 1024 * 1024)

# Create your views here.
def index(request):
    num_projects = Project.objects.filter(delete_date__isnull=True).all().count()
    requested_size = Project.objects.aggregate(total=Sum('requested_size'))['total'] / 1024  # TB
    miscstats = MiscStats.objects.latest('collected')
    stalecnt, stalesize = stale_groups(days = 366, collected = miscstats.collected)
    context = {
        'current_year': end_year,
        'previous_year': end_year-1,
        'num_projects': num_projects,
        'stale_groups': stalecnt,
        'stale_size': _convert_bytes(stalesize),
        'unregistered_groups': ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True).all().count,
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


def stale_groups(days, collected):
    # groups were newest file is older than <days> ago. Remember irods timestamps are always the date the file was updated on irods, not the original file date.
    cutoff = make_aware(datetime.combine(collected, datetime.min.time())) - timedelta(days=days)
    collected=MiscStats.objects.latest('collected').collected
    #newest_old = ResearchStats.objects.filter(newest_file__lt = cutoff, newest_file__gt = datetime.fromtimestamp(0), collected = collected).all().count()
    stalecols = ResearchStats.objects.filter(newest_file__lt = cutoff, newest_file__gt = datetime.fromtimestamp(0), collected = collected).all()
    size = 0
    for col in stalecols:
        size += col.size + col.revision_size
    # groups created before cutoff and empty
    return stalecols.count(), size


@login_required(login_url='/admin/login/')
def download_billing_report(request, year: int):
    # fill these variables with real values
    fl_path = generate_yearly_report(int(year), include_revisions=True)
    if int(year) == today.year:
        month = today.month
    else:
        month = 12
    filename = f'yoda_cost_report_{year}-{month}.xlsx'

    fl = open(fl_path, 'rb')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

def download_statistics_report(request):
    fl_path = generate_statistics_report(include_revisions=True)
    filename = f'yoda_statistics_report_{today.year}-{today.month}-{today.day}.xlsx'

    fl = open(fl_path, 'rb')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response        

def _quarterly_miscstats():
    quarters = [3, 6, 9, 12]
    stats = []
    last_size = 0
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            s = MiscStats.objects.filter(collected__year=year, collected__month__lte=month,
                                         collected__month__gt=month - 3).order_by('collected').last()
            if s is not None:
                s.label = f'{year}-Q{q}'
                stats.append(s)
                if last_size > 0:
                    s.research_delta = s.size_research + s.revision_size - last_size
                    s.research_delta_percent = round((s.research_delta) / last_size * 100, 2)
                else:
                    s.delta = 0
                    s.research_delta_percent = 0
                last_size = s.size_research + s.revision_size
            q += 1
    return stats


def _monthly_miscstats():
    stats = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            s = MiscStats.objects.filter(collected__year=year, collected__month=month).order_by('collected').last()
            if s is not None:
                # s.label = s.collected
                s.label = f'{year}-{month}'
                stats.append(s)
    return stats


def _all_miscstats():
    stats = []
    for s in MiscStats.objects.order_by('collected').all():
        s.label = s.collected
        stats.append(s)
    return stats


def vault_size_chart_json(request):
    labels = []
    vault = []
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        vault.append(round(s.size_vault / divTB, 2))
    datasets = [
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def research_size_chart_json(request):
    labels = []
    research = []
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(round(s.size_research / divTB, 2) + round(s.revision_size / divTB, 2))
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def research_percentage_chart_json(request):
    labels = []
    research = []
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(s.research_delta_percent)
    datasets = [
        {
            'label': 'Research',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': research,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})

def size_chart_json(request):
    labels = []
    research = []
    vault = []
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(round(s.size_research / divTB, 2) + round(s.revision_size / divTB, 2))
        vault.append(round(s.size_vault / divTB, 2))
    datasets = [
        {
            'label': 'Vault',
            # d9f89a
            'backgroundColor': 'rgb(217, 248, 154, 0.4)',
            'borderColor': 'rgb(217, 248, 154)',
            'borderWidth': 1,
            'data': vault,
        },
        {
            'label': 'Research',
            # ed9ac8
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
            'borderWidth': 1,
            'data': research,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})

def dataset_chart_json(request):
    labels = []
    archived = []
    published = []
    stats = _quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        archived.append(s.datasets_total - s.published_total)
        published.append(s.published_total)
    datasets = [
        {
            'label': 'published',
            'backgroundColor': 'rgba(155,214,215,0.4)',
            'borderColor': 'rgba(155,214,215)',
            'borderWidth': 1,
            'data': published,
        },
        {
            'label': 'archived',
            'backgroundColor': 'rgba(255,199,152,0.4)',
            'borderColor': 'rgba(255,199,152)',
            'borderWidth': 1,
            'data': archived,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})

def rights_chart_json(request):
    labels = []
    data = []
    index = {}
    i = 0
    colors = []
    vault_datasets = VaultDataset.objects.filter(deleted__isnull=True, status="PUBLISHED").all()
    for set in vault_datasets:
        if set.publication_access not in labels:
            index[set.publication_access]=i
            labels.append(set.publication_access)
            colors.append(COLORSET[i])
            data.append(0)
            i += 1
        data[index[set.publication_access]] += 1
    
    datasets = [{
        'label': 'Publication access rights',
        'backgroundColor': colors,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def project_chart_json(request):
    labels = []
    data = []
    unregistered_groups = ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True).all().count()
    miscstats = _quarterly_miscstats()
    for s in miscstats:
        labels.append(s.label)
        data.append(s.projects_total)
    # count unregistered groups as projects
    data[-1] += unregistered_groups
    datasets = [{
        'label': 'Projects',
        'backgroundColor': 'rgba(56,108,176, 0.4)',
        'borderColor': 'rgba(56,108,176)',
        'borderWidth': 1,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def group_chart_json(request):
    labels = []
    data = []
    
    miscstats = _quarterly_miscstats()
    for s in miscstats:
        labels.append(s.label)
        data.append(s.groups_total)
    datasets = [{
        'label': 'Groups',
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
    stats = _quarterly_miscstats()
    # stats = _get_quarterly_miscstats()
    for s in stats:
        labels.append(s.label)
        research.append(round(s.size_research / divTB, 2))
        vault.append(round(s.size_vault / divTB, 2))
        revisions.append(round(s.revision_size / divTB, 2))
        trash.append(round(s.trash_size / divTB, 2))
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
        {
            'label': 'Vault',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': vault,
        },

    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def faculty_chart_json(request):
    labels = []
    tempdata = {}
    data = []
    index = {}
    i = 0
    colors = []
    projects = Project.objects.filter(delete_date__isnull=True).order_by('department').all()
    for project in projects:
        faculty = Department.objects.get(id=project.department.id).faculty
        if faculty not in tempdata:
            tempdata[faculty] = 0
        tempdata[faculty] += 1
    i = 0
    for faculty in dict(reversed(sorted(tempdata.items(), key=lambda item: item[1]))):
        logger.info(faculty)
        data.append(tempdata[faculty])
        labels.append(faculty)
        colors.append(COLORSET[i])
        i+=1

    datasets = [{
        'label': 'Faculty',
        'backgroundColor': colors,
        'data': data
    }]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})


def size_breakdown_chart_json(request):
    labels = ['empty', '0-10', '10-100', '100-500', '500-1000', '>1000']	
    data = []
    collected=MiscStats.objects.latest('collected').collected
    data.append(ResearchStats.objects.filter(size = 0, collected = collected).all().count())
    data.append(ResearchStats.objects.filter(size__gt = 0, size__lte = 10 * GB, collected = collected).all().count())
    data.append(ResearchStats.objects.filter(size__gt = 10 * GB, size__lte = 100 * GB, collected = collected).all().count())
    data.append(ResearchStats.objects.filter(size__gt = 100 * GB, size__lte = 500 * GB, collected = collected).all().count())
    data.append(ResearchStats.objects.filter(size__gt = 500 * GB, size__lte = 1000 * GB, collected = collected).all().count())
    data.append(ResearchStats.objects.filter(size__gt = 1000 * GB, collected = collected).all().count())
    
    datasets = [
        {
            'label': 'Research size breakdown',
            'backgroundColor': 'rgb(128,177,211, 0.4)',
            'borderColor': 'rgba(128,177,211)',
            'borderWidth': 1,
            'data': data,
        },
    ]
    return JsonResponse(data={'labels': labels, 'datasets': datasets})