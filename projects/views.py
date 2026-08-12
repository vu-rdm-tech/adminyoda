from django.http import Http404, JsonResponse
from .models import Project, MiscStats, VaultDataset, ResearchFolder, Department, VaultFolder, VaultStats, \
    ResearchStats, Person, Datamanager, ChartCache
from django.shortcuts import render
from .tables import ProjectTable, ProjectFilter
from django_tables2 import RequestConfig

GB = 1024 * 1024 * 1024


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
        try:
            vf = VaultFolder.objects.get(research_folder=f)
            if vf.deleted is None:
                size = size + VaultStats.objects.filter(vault_folder=vf).latest('collected').size
                cnt = VaultDataset.objects.filter(vault_folder=vf, deleted__isnull=True).count()
                pubcnt = VaultDataset.objects.filter(status='PUBLISHED', vault_folder=vf, deleted__isnull=True).count()
                d['num_dataset'] = d['num_dataset'] + cnt
                d['num_published'] = d['num_published'] + pubcnt
        except:
            pass
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


# All project_*_chart_json views below just serve the payloads precomputed by
# projects.tasks.generate_chart_cache_task for each active project (see
# projects/chart_data.py for how each is built, ported from the functions that used to
# live here). They used to recompute their data from scratch on every request.

def project_size_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_size:{project_id}'))


def project_research_size_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_research_size:{project_id}'))


def project_research_revision_size_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_research_revision_size:{project_id}'))


def project_vault_size_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_vault_size:{project_id}'))


def project_delta_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_delta:{project_id}'))


def project_delta_with_revision_chart_json(request, project_id):
    return JsonResponse(data=ChartCache.get_data(f'project_delta_with_revision:{project_id}'))