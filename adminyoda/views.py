from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import now, make_aware
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department, ResearchStats, ChartCache
from datetime import datetime, timedelta
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from projects.reports import billing_report_path, STATISTICS_REPORT_PATH
import mimetypes
import os
import logging

logger = logging.getLogger(__name__)

today = datetime.now()
end_year = today.year


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
    fl_path = billing_report_path(int(year))
    if not os.path.exists(fl_path):
        return HttpResponse("Billing report has not been generated yet, please try again later.", status=503)
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
    fl_path = STATISTICS_REPORT_PATH
    if not os.path.exists(fl_path):
        return HttpResponse("Statistics report has not been generated yet, please try again later.", status=503)
    filename = f'yoda_statistics_report_{today.year}-{today.month}-{today.day}.xlsx'

    fl = open(fl_path, 'rb')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


# All *_chart_json views below just serve the payloads precomputed by
# projects.tasks.generate_chart_cache_task (see projects/chart_data.py for how each is
# built). They used to recompute their data from scratch on every request.

def vault_size_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('vault_size'))


def research_size_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('research_size'))


def research_percentage_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('research_percentage'))


def size_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('size'))


def dataset_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('dataset'))


def rights_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('rights'))


def project_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('project'))


def group_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('group'))


def user_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('user'))


def storage_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('storage'))


def faculty_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('faculty'))


def faculty_size_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('faculty_size'))


def size_breakdown_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('size_breakdown'))


def paid_free_chart_json(request):
    return JsonResponse(data=ChartCache.get_data('paid_free'))
