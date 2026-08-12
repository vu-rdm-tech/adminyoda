"""Builds the payloads served by the *_chart_json views.

These used to be computed inline in adminyoda/views.py and projects/views.py on every
request. They are now computed once by tasks.generate_chart_cache_task and stored in
ChartCache; the views just read the cached row. Keeping the builders here mirrors how
reports.py separates report computation from the views that serve the result.
"""
from datetime import date

from django.db.models import Count, Q

from .models import (
    Project,
    ResearchFolder,
    VaultFolder,
    VaultDataset,
    ResearchStats,
    VaultStats,
    MiscStats,
)

GB = 1024 * 1024 * 1024
divTB = 1024 * 1024 * 1024 * 1024
start_year = 2023  # dashboard/storage charts (adminyoda/views.py's original start_year)
project_start_year = 2021  # per-project charts (projects/views.py's original start_year)
end_year = date.today().year
COLORSET = ['rgba(141,211,199)', 'rgba(255,255,179)', 'rgba(190,186,218)', 'rgba(251,128,114)', 'rgba(128,177,211)',
            'rgba(253,180,98)', 'rgba(179,222,105)', 'rgba(252,205,229)', 'rgba(217,217,217)', 'rgba(188,128,189)',
            'rgba(204,235,197)', 'rgba(255,237,111)']


def _quarter_range(year, end_month):
    """[start, end) date range covering the 3 months up to and including end_month."""
    start = date(year, end_month - 2, 1)
    end = date(year + 1, 1, 1) if end_month == 12 else date(year, end_month + 1, 1)
    return start, end


def _month_range(year, month):
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


# ---------------------------------------------------------------------------
# Dashboard / storage page charts (adminyoda/views.py)
# ---------------------------------------------------------------------------

def _quarterly_miscstats():
    quarters = [3, 6, 9, 12]
    stats = []
    last_size = 0
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            start, end = _quarter_range(year, month)
            s = MiscStats.objects.filter(collected__gte=start, collected__lt=end).order_by('collected').last()
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


def vault_size_chart_data():
    labels, vault = [], []
    for s in _quarterly_miscstats():
        labels.append(s.label)
        vault.append(round(s.size_vault / divTB, 2))
    datasets = [{
        'label': 'Vault',
        'backgroundColor': 'rgba(127,201,127, 0.4)',
        'borderColor': 'rgba(127,201,127)',
        'borderWidth': 1,
        'data': vault,
    }]
    return {'labels': labels, 'datasets': datasets}


def research_size_chart_data():
    labels, research = [], []
    for s in _quarterly_miscstats():
        labels.append(s.label)
        research.append(round(s.size_research / divTB, 2) + round(s.revision_size / divTB, 2))
    datasets = [{
        'label': 'Research',
        'backgroundColor': 'rgba(253,192,134, 0.4)',
        'borderColor': 'rgba(253,192,134)',
        'borderWidth': 1,
        'data': research,
    }]
    return {'labels': labels, 'datasets': datasets}


def research_percentage_chart_data():
    labels, research = [], []
    for s in _quarterly_miscstats():
        labels.append(s.label)
        research.append(s.research_delta_percent)
    datasets = [{
        'label': 'Research',
        'backgroundColor': 'rgba(253,192,134, 0.4)',
        'borderColor': 'rgba(253,192,134)',
        'borderWidth': 1,
        'data': research,
    }]
    return {'labels': labels, 'datasets': datasets}


def size_chart_data():
    labels, research, vault = [], [], []
    for s in _quarterly_miscstats():
        labels.append(s.label)
        research.append(round(s.size_research / divTB, 2) + round(s.revision_size / divTB, 2))
        vault.append(round(s.size_vault / divTB, 2))
    datasets = [
        {
            'label': 'Vault',
            'backgroundColor': 'rgb(217, 248, 154, 0.4)',
            'borderColor': 'rgb(217, 248, 154)',
            'borderWidth': 1,
            'data': vault,
        },
        {
            'label': 'Research',
            'backgroundColor': 'rgba(237, 154, 200, 0.4)',
            'borderColor': 'rgba(237, 154, 200)',
            'borderWidth': 1,
            'data': research,
        },
    ]
    return {'labels': labels, 'datasets': datasets}


def dataset_chart_data():
    labels, archived, published = [], [], []
    for s in _quarterly_miscstats():
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
    return {'labels': labels, 'datasets': datasets}


def rights_chart_data():
    labels, data, colors = [], [], []
    index = {}
    i = 0
    vault_datasets = VaultDataset.objects.filter(deleted__isnull=True, status="PUBLISHED").all()
    for set in vault_datasets:
        if set.publication_access not in labels:
            index[set.publication_access] = i
            labels.append(set.publication_access)
            colors.append(COLORSET[i])
            data.append(0)
            i += 1
        data[index[set.publication_access]] += 1
    datasets = [{
        'label': 'Publication access rights',
        'backgroundColor': colors,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def project_chart_data():
    labels, data = [], []
    unregistered_groups = ResearchFolder.objects.filter(project__isnull=True, deleted__isnull=True).count()
    for s in _quarterly_miscstats():
        labels.append(s.label)
        data.append(s.projects_total)
    if data:
        data[-1] += unregistered_groups
    datasets = [{
        'label': 'Projects',
        'backgroundColor': 'rgba(56,108,176, 0.4)',
        'borderColor': 'rgba(56,108,176)',
        'borderWidth': 1,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def group_chart_data():
    labels, data = [], []
    for s in _quarterly_miscstats():
        labels.append(s.label)
        data.append(s.groups_total)
    datasets = [{
        'label': 'Groups',
        'backgroundColor': 'rgba(56,108,176, 0.4)',
        'borderColor': 'rgba(56,108,176)',
        'borderWidth': 1,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def user_chart_data():
    labels, internal, external = [], [], []
    for s in _quarterly_miscstats():
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
    return {'labels': labels, 'datasets': datasets}


def storage_chart_data():
    labels, research, vault, revisions, trash = [], [], [], [], []
    for s in _quarterly_miscstats():
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
    return {'labels': labels, 'datasets': datasets}


def _faculty_colors(data):
    colorlist = {}
    i = 0
    for faculty in dict(sorted(data.items())):
        colorlist[faculty] = COLORSET[i]
        i += 1
    return colorlist


def faculty_chart_data():
    tempdata = {}
    projects = Project.objects.filter(delete_date__isnull=True).select_related('department').order_by('department')
    for project in projects:
        faculty = project.department.faculty
        tempdata[faculty] = tempdata.get(faculty, 0) + 1
    colorlist = _faculty_colors(tempdata)
    labels, data, colors = [], [], []
    for faculty in dict(reversed(sorted(tempdata.items(), key=lambda item: item[1]))):
        data.append(tempdata[faculty])
        labels.append(faculty)
        colors.append(colorlist[faculty])
    datasets = [{
        'label': 'Faculty',
        'backgroundColor': colors,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def faculty_size_chart_data():
    projects = Project.objects.filter(delete_date__isnull=True).select_related('department')
    project_faculty = {p.id: p.department.faculty for p in projects}
    tempdata = {faculty: 0 for faculty in project_faculty.values()}

    # latest ResearchStats per folder, by `created` (matches the original .latest('created'))
    research_latest = {}
    for row in (ResearchStats.objects
                .filter(research_folder__project_id__in=project_faculty)
                .order_by('research_folder_id', '-created')
                .values('research_folder_id', 'size', 'revision_size')):
        fid = row['research_folder_id']
        if fid not in research_latest:
            research_latest[fid] = row['size'] + row['revision_size']

    # latest VaultStats per folder (via its VaultFolder), by `created`
    vault_latest = {}
    for row in (VaultStats.objects
                .filter(vault_folder__research_folder__project_id__in=project_faculty)
                .order_by('vault_folder_id', '-created')
                .values('vault_folder_id', 'vault_folder__research_folder_id', 'size')):
        fid = row['vault_folder__research_folder_id']
        if fid not in vault_latest:
            vault_latest[fid] = row['size']

    folders = ResearchFolder.objects.filter(project_id__in=project_faculty).values('id', 'project_id')
    for folder in folders:
        if folder['id'] not in research_latest or folder['id'] not in vault_latest:
            continue  # no stats collected yet for this folder
        faculty = project_faculty[folder['project_id']]
        tempdata[faculty] += (research_latest[folder['id']] + vault_latest[folder['id']]) / GB

    colorlist = _faculty_colors(tempdata)
    labels, data, colors = [], [], []
    for faculty in dict(reversed(sorted(tempdata.items(), key=lambda item: item[1]))):
        data.append(tempdata[faculty])
        labels.append(faculty)
        colors.append(colorlist[faculty])
    datasets = [{
        'label': 'Faculty',
        'backgroundColor': colors,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def size_breakdown_chart_data():
    labels = ['empty', '0-10', '10-100', '100-500', '500-1000', '>1000']
    collected = MiscStats.objects.latest('collected').collected
    counts = ResearchStats.objects.filter(collected=collected).aggregate(
        empty=Count('id', filter=Q(size=0)),
        b0_10=Count('id', filter=Q(size__gt=0, size__lte=10 * GB)),
        b10_100=Count('id', filter=Q(size__gt=10 * GB, size__lte=100 * GB)),
        b100_500=Count('id', filter=Q(size__gt=100 * GB, size__lte=500 * GB)),
        b500_1000=Count('id', filter=Q(size__gt=500 * GB, size__lte=1000 * GB)),
        gt1000=Count('id', filter=Q(size__gt=1000 * GB)),
    )
    data = [counts['empty'], counts['b0_10'], counts['b10_100'], counts['b100_500'], counts['b500_1000'], counts['gt1000']]
    datasets = [{
        'label': 'Research size breakdown',
        'backgroundColor': 'rgb(128,177,211, 0.4)',
        'borderColor': 'rgba(128,177,211)',
        'borderWidth': 1,
        'data': data,
    }]
    return {'labels': labels, 'datasets': datasets}


def _quarter_folder_sizes(start, end):
    """Latest (size + revision_size) per research_folder collected within [start, end),
    plus which project each folder belongs to. One query per quarter instead of one per
    folder."""
    rows = (
        ResearchStats.objects
        .filter(collected__gte=start, collected__lt=end, research_folder__project__isnull=False)
        .order_by('research_folder_id', '-collected')
        .values('research_folder_id', 'research_folder__project_id', 'size', 'revision_size')
    )
    sizes = {}
    for row in rows:
        fid = row['research_folder_id']
        if fid in sizes:
            continue  # already have this folder's latest-in-quarter row
        sizes[fid] = (row['research_folder__project_id'], row['size'] + row['revision_size'])
    return sizes


def _quarterly_paid_free_stats(cutoff1=500 * GB, cutoff2=2 * divTB):
    quarters = [3, 6, 9, 12]
    stats = {}
    for year in range(start_year, end_year + 1):
        q = 1
        for month in quarters:
            label = f'{year}-Q{q}'
            start, end = _quarter_range(year, month)
            folder_sizes = _quarter_folder_sizes(start, end)

            # The original computed one size per project by overwriting (not summing) as
            # it walked a project's folders in ascending id order, so only the
            # highest-id folder with data in the quarter counted. Reproduce that here.
            project_sizes = {}
            for folder_id in sorted(folder_sizes):
                project_id, size = folder_sizes[folder_id]
                project_sizes[project_id] = size

            for project_size in project_sizes.values():
                if project_size > 0:
                    if label not in stats:
                        stats[label] = {'tier1': 0, 'tier2': 0, 'tier3': 0, 'total': 0}
                    stats[label]['total'] += project_size
                    if project_size > cutoff2:
                        stats[label]['tier1'] += cutoff1
                        stats[label]['tier2'] += cutoff2 - cutoff1
                        stats[label]['tier3'] += project_size - cutoff2
                    elif project_size > cutoff1:
                        stats[label]['tier1'] += cutoff1
                        stats[label]['tier3'] += project_size - cutoff1
                    else:
                        stats[label]['tier1'] += project_size
            q += 1
    return stats


def paid_free_chart_data():
    labels, tier1, tier2, tier3 = [], [], [], []
    stats = _quarterly_paid_free_stats()
    for label in dict(sorted(stats.items())):
        labels.append(label)
        tier1.append(stats[label]['tier1'] / divTB)
        tier2.append(stats[label]['tier2'] / divTB)
        tier3.append(stats[label]['tier3'] / divTB)
    datasets = [
        {
            'label': 'Free (<500GB)',
            'backgroundColor': 'rgba(127,201,127, 0.4)',
            'borderColor': 'rgba(127,201,127)',
            'borderWidth': 1,
            'data': tier1,
        },
        {
            'label': 'tier 1 (500GB-2TB)',
            'backgroundColor': 'rgba(253,192,134, 0.4)',
            'borderColor': 'rgba(253,192,134)',
            'borderWidth': 1,
            'data': tier2,
        },
        {
            'label': 'tier2 (>2TB)',
            'backgroundColor': 'rgba(190,174,212,  0.4)',
            'borderColor': 'rgba(190,174,212)',
            'borderWidth': 1,
            'data': tier3,
        },
    ]
    return {'labels': labels, 'datasets': datasets}


CHART_BUILDERS = {
    'vault_size': vault_size_chart_data,
    'research_size': research_size_chart_data,
    'research_percentage': research_percentage_chart_data,
    'size': size_chart_data,
    'dataset': dataset_chart_data,
    'rights': rights_chart_data,
    'project': project_chart_data,
    'group': group_chart_data,
    'user': user_chart_data,
    'storage': storage_chart_data,
    'faculty': faculty_chart_data,
    'faculty_size': faculty_size_chart_data,
    'size_breakdown': size_breakdown_chart_data,
    'paid_free': paid_free_chart_data,
}


# ---------------------------------------------------------------------------
# Per-project charts (projects/views.py, project detail page)
# ---------------------------------------------------------------------------

def _researchstats_month(research_folder, year, month):
    start, end = _month_range(year, month)
    return ResearchStats.objects.filter(research_folder=research_folder, collected__gte=start,
                                        collected__lt=end).order_by('collected').last()


def _vaultstats_month(vault_folder, year, month):
    start, end = _month_range(year, month)
    return VaultStats.objects.filter(vault_folder=vault_folder, collected__gte=start,
                                     collected__lt=end).order_by('collected').last()


def _monthly_research_stats(folder):
    stats = []
    last_size = 0
    last_revision_size = 0
    for year in range(project_start_year, end_year + 1):
        for month in range(1, 13):
            s = _researchstats_month(folder, year, month)
            if s is not None:
                s.label = f'{year}-{str(month).rjust(2, "0")}'
                s.delta = s.size - last_size
                s.revision_delta = s.revision_size - last_revision_size
                s.total_size = s.size + s.revision_size
                last_size = s.size
                last_revision_size = s.revision_size
                stats.append(s)
    return stats


def _monthly_vault_stats(folder):
    stats = []
    last_size = 0
    for year in range(project_start_year, end_year + 1):
        for month in range(1, 13):
            s = _vaultstats_month(folder, year, month)
            if s is not None:
                s.label = f'{year}-{str(month).rjust(2, "0")}'
                s.delta = s.size - last_size
                last_size = s.size
                stats.append(s)
    return stats


def project_research_stats(project_id):
    """Monthly research/vault stats for a project, merged by label. Matches the
    original project_research_stats(project_id, quarterly=False) default path — the
    quarterly=True path had no callers anywhere in the codebase, so it's dropped here."""
    project = Project.objects.get(pk=project_id)
    rf = list(ResearchFolder.objects.filter(project=project))
    vault_folders = {vf.research_folder_id: vf for vf in VaultFolder.objects.filter(research_folder__in=rf)}
    research_stats = {}
    vault_stats = {}
    labels = []
    for f in rf:
        vf = vault_folders.get(f.id)
        if vf is None:
            continue
        rstats = _monthly_research_stats(f)
        vstats = _monthly_vault_stats(vf)
        for rstat in rstats:
            label = rstat.label
            if label not in labels:
                labels.append(label)
            if label not in research_stats:
                research_stats[label] = {'size': 0, 'delta': 0, 'revision_size': 0, 'revision_delta': 0, 'total_size': 0}
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
                vault_stats[label] = {'size': 0, 'delta': 0}
            vault_stats[label]['size'] += vstat.size
            vault_stats[label]['delta'] += vstat.delta
    return sorted(labels), research_stats, vault_stats


def project_size_chart_data(labels, research_stats, vault_stats):
    # A label (month) can be present in one of research_stats/vault_stats but not the
    # other (e.g. vault stats not yet collected for a recent month), so both lookups
    # need a default — matches the `if label in vault_stats else 0` guard already used
    # by the sibling functions below.
    research, revision, vault = [], [], []
    for label in labels:
        research.append(round(research_stats.get(label, {}).get('size', 0) / GB, 2))
        revision.append(round(research_stats.get(label, {}).get('revision_size', 0) / GB, 2))
        vault.append(round(vault_stats.get(label, {}).get('size', 0) / GB, 2))
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
    return {'labels': labels, 'datasets': datasets}


def project_research_size_chart_data(labels, research_stats, vault_stats):
    research = []
    for label in labels:
        research.append(round((research_stats[label]['size'] + research_stats[label]['revision_size']) / GB, 2))
    datasets = [{
        'label': 'Research',
        'backgroundColor': 'rgba(237, 154, 200, 0.4)',
        'borderColor': 'rgba(237, 154, 200)',
        'borderWidth': 1,
        'data': research,
    }]
    return {'labels': labels, 'datasets': datasets}


def project_vault_size_chart_data(labels, research_stats, vault_stats):
    vault = []
    for label in labels:
        vault.append(round(vault_stats[label]['size'] / GB, 2) if label in vault_stats else 0)
    datasets = [{
        'label': 'Vault',
        'backgroundColor': 'rgb(217, 248, 154, 0.4)',
        'borderColor': 'rgb(217, 248, 154)',
        'borderWidth': 1,
        'data': vault,
    }]
    return {'labels': labels, 'datasets': datasets}


def project_delta_chart_data(labels, research_stats, vault_stats):
    research, vault = [], []
    for label in labels:
        research.append(round((research_stats[label]['delta'] + research_stats[label]['revision_delta']) / GB, 2))
        vault.append(round(vault_stats[label]['delta'] / GB, 2) if label in vault_stats else 0)
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
    return {'labels': labels, 'datasets': datasets}


# name -> formatter(labels, research_stats, vault_stats). All four are derived from a
# single project_research_stats(project_id) call (see generate_chart_cache_task) rather
# than each re-running that per-folder, per-month query loop independently.
#
# project_research_revision_size_chart_json and project_delta_with_revision_chart_json
# exist as views but have no URL route or template using them (dead code predating this
# change), so they aren't built here.
PROJECT_CHART_FORMATTERS = {
    'project_size': project_size_chart_data,
    'project_research_size': project_research_size_chart_data,
    'project_vault_size': project_vault_size_chart_data,
    'project_delta': project_delta_chart_data,
}
