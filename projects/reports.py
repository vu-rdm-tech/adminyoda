from projects.views import project_detail_data, project_research_stats, friendly_size
from projects.models import Project, ResearchStats, ResearchFolder, VaultFolder, VaultDataset
import logging
import os
from datetime import datetime
import math
from django.conf import settings
import json
import pandas as pd

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

GB = 1024 * 1024 * 1024
today = datetime.now()


def _researchstats_month(research_folder, year, month):
    return ResearchStats.objects.filter(research_folder=research_folder, collected__year=year,
                                        collected__month=month).order_by('collected').last()

def _monthly_research_stats(folder, stats, start_year, end_year, end_month):
    for year in range(start_year, end_year + 1):
        if year not in stats:
            stats[year] = {}
        for month in range(1, 13):
            if month not in stats[year]:
                stats[year][month] = {}
            s = _researchstats_month(folder, year, month)
            if s is not None:
                if 'size' not in stats[year][month]:
                    stats[year][month]['size'] = s.size + s.revision_size
                else:
                    stats[year][month]['size'] += s.size + s.revision_size
    return stats

def _yearly_research_stats(folder, stats, start_year, end_year):
    for year in range(start_year, end_year + 1):
        if year not in stats:
            stats[year] = {}
        s = ResearchStats.objects.filter(research_folder=folder, collected__year=year).order_by('collected').last()
        if s is not None:
            if 'size' not in stats[year]:
                stats[year]['size'] = s.size + s.revision_size
            else:
                stats[year]['size'] += s.size + s.revision_size
    return stats

def _vault_datasets_by_month(vault_folder, data, start_year, end_year, end_month):
    for year in range(start_year, end_year + 1):
        if year not in data:
            data[year] = {}
        for month in range(1, 13):
            if month not in data[year]:
                data[year][month] = []
            datasets = VaultDataset.objects.filter(vault_folder=vault_folder, created__year=year, created__month=month, deleted__isnull=True).order_by('created')
            for dataset in datasets:
                data[year][month].append({
                    'size': dataset.size,
                    'retention': dataset.retention,
                    'name': dataset.yoda_name,
                })
    return data
        

def research_cost_table(project_id):
    labels, research_stats, vault_stats = project_research_stats(project_id)
    research_stats_table = [[''], ['Size'], ['Cost']]
    cumulative_cost = 0
    for label in labels:
        if label.startswith(str(datetime.datetime.now().year)):
            research_stats_table[0].append(label)
            research_stats_table[1].append(friendly_size(research_stats[label]['total_size']))
            cost = calculate_cost(research_stats[label]['total_size']) / 12
            research_stats_table[2].append(round(cost, 2))
            cumulative_cost += cost
    return research_stats_table, cumulative_cost

def calculate_blocks(bytes, block_size_GB=2048):
    bytes = bytes + 1 # avoid 0
    gigabytes = bytes/(1024*1024*1024)
    return int(math.ceil(gigabytes/block_size_GB))

def calculate_cost(size, free_block = 500, first_block = 2048, first_block_cost = 200, block_size = 1024, block_cost = 250):
    total_cost = 0
    GBytes = 1024 * 1024 * 1024
    if size > free_block * GBytes:
        total_cost = first_block_cost
    if size > first_block * GBytes:
        total_cost = total_cost + (calculate_blocks(size, block_size) - 1) * block_cost
    return total_cost

def send_monthly_owner_reports():
    projects = Project.objects.filter(delete_date__isnull=True).all()
    for project in projects:
        details = project_detail_data(project.id)
        project = Project.objects.get(pk=project.id)
        cost_table, cumulative_cost = research_cost_table(project.id)
        params = {'project': project, 'details': details, 'research_stats': cost_table, 'total_cost': round(cumulative_cost, 2), 'sitename': os.environ.get("SITE_NAME")}
        msg_plain = render_to_string('projects/owner_report.txt', params)
        msg_html = render_to_string('projects/owner_report.html', params)
        with open(f'email_{project.title}.html', 'w') as fp:
            fp.write(msg_html)
        try:
            send_mail(
                f'{datetime.datetime.now()} Yoda usage report for "{project.title}"',
                msg_plain,
                settings.REPORTS_MAIL_FROM,
                [settings.REPORTS_MAIL_TEST_TO],
                html_message=msg_html,
            )
            logger.info(f'successfully sent monthly report email to {settings.REPORTS_MAIL_TEST_TO}')
        except Exception as e:
            logger.error(f'unable to send monthly report email to {settings.REPORTS_MAIL_TEST_TO}, error: {e}')

def get_billing_data(start_year, end_year, end_month):
    projects = Project.objects.filter(delete_date__isnull=True).all()
    billing_data = {}
    for project in projects:

        rf = ResearchFolder.objects.filter(project=project)  # deleted folders should automatically disappear from the stats
        research = {}
        datasets = {}
        research_yearly = {}
        for f in rf:
            print(f'{project.title} - {f.yoda_name}')
            research = _monthly_research_stats(f, research, start_year, end_year, end_month)
            datasets = _vault_datasets_by_month(VaultFolder.objects.get(research_folder=f), datasets, start_year, end_year, end_month)
            research_yearly = _yearly_research_stats(f, research_yearly, start_year, end_year)
        billing_data[project.id] = {
            'project': project.title,
            'usage_details': f'https://adminyoda.labs.vu.nl/projects/{project.id}',
            'created': project.created.strftime("%Y-%m-%d"),
            'deleted': project.delete_date.strftime("%Y-%m-%d") if project.delete_date else '',
            'owner_name': project.owner.firstname + ' ' + project.owner.lastname,
            'owner_vunetid': project.owner.vunetid,
            'budget_code': project.budget.code,
            'budget_type': project.budget.type,
            'budget_holder': project.budget.vunetid,
            'research': research, 
            'research_yearly': research_yearly,
            'datasets': datasets
        }
    return billing_data

def calculate_research_cost(size, free_block = 500, first_block = 2048, first_block_cost = 200, block_size = 2048, block_cost = 250):
    total_cost = 0
    GBytes = 1024 * 1024 * 1024
    if size > free_block * GBytes:
        total_cost = first_block_cost
    if size > first_block * GBytes:
        total_cost = total_cost + (calculate_blocks(size, block_size) - 1) * block_cost
    return total_cost
    

def calculate_monthly_costs_per_project(year):
    billing_data = get_billing_data(start_year=year, end_year=year, end_month=12)
    for project in billing_data:
        total_research_cost = 0
        total_dataset_cost = 0
        if year in billing_data[project]['research']:
            for month in billing_data[project]['research'][year]:
                cost = 0
                if 'size' in billing_data[project]['research'][year][month]:
                    cost = calculate_cost(billing_data[project]['research'][year][month]['size']) / 12    
                    billing_data[project]['research'][year][month]['cost'] = cost
                    total_research_cost += cost
            for month in billing_data[project]['datasets'][year]:
                cost = 0
                i = 0
                for dataset in billing_data[project]['datasets'][year][month]:
                    if 'size' in dataset:
                        cost += calculate_cost(dataset['size'], first_block_cost=25, block_cost=25) * dataset['retention']
                        total_dataset_cost += cost
                    billing_data[project]['datasets'][year][month][i]['cost'] = cost
                    i += 1
            if 'size' in billing_data[project]['research_yearly'][year]:
                billing_data[project]['yearly_research_cost'] = calculate_cost(billing_data[project]['research_yearly'][year]['size'])
        billing_data[project]['total_dataset_cost'] = total_dataset_cost
        billing_data[project]['total_research_cost'] = total_research_cost
        billing_data[project]['total_cost'] = round(total_research_cost + total_dataset_cost)
    return billing_data

def yearly_billing_report(year):
    if year == today.year:
        filename = f'output/yearly_cost_report_{year}{today.strftime("%U")}.xlsx'
    else:
        filename = f'output/yearly_cost_report_{year}.xlsx'
    if not os.path.isfile(filename):
        data=calculate_monthly_costs_per_project(year)
        bill_data = {}
        columns = ['project', 'usage_details', 'created', 'deleted', 'owner_name', 'owner_vunetid', 'budget_code', 'budget_type', 'budget_holder', 'total_research_cost', 'total_dataset_cost', 'total_cost', 'yearly_research_cost']
        
        for project in data:
            if data[project]['total_cost'] > 0:
                bill_data[project] = data[project]
        with open(f'{filename[:-5]}.json', 'w') as fp:
            json.dump(bill_data, fp)
        df = pd.DataFrame.from_dict(data=bill_data, orient='index', columns=columns)
        df.to_excel(filename)
    return filename

