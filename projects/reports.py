from projects.views import project_detail_data, project_research_stats, friendly_size
from projects.models import Project
import logging
import os
import datetime
import math
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_billing_report():
    pass

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

def calculate_cost(size, free_block = 500, first_block = 2048, first_block_cost = 200, block_size = 2048, block_cost = 250):
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
                f'{datetime.datetime.now().strftime("%B")} Yoda usage report for "{project.title}"',
                msg_plain,
                settings.REPORTS_MAIL_FROM,
                [settings.REPORTS_MAIL_TEST_TO],
                html_message=msg_html,
            )
            logger.info(f'successfully sent monthly report email to {settings.REPORTS_MAIL_TEST_TO}')
        except Exception as e:
            logger.error(f'unable to send monthly report email to {settings.REPORTS_MAIL_TEST_TO}, error: {e}')

#send_monthly_owner_reports()