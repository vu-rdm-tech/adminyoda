from projects.views import project_detail_data, project_research_stats, friendly_size, calculate_blocks, BLOCK_MONTH_COST
from projects.models import Project
import logging
import os
import datetime
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_billing_report():
    pass

def research_cost_table(project_id):
    labels, research_stats, vault_stats = project_research_stats(project_id)
    research_stats_table = [[], [], [], []]
    cumulative_cost = 0
    for label in labels:
        if label.startswith(str(datetime.datetime.now().year)):
            research_stats_table[0].append(label)
            research_stats_table[1].append(friendly_size(research_stats[label]['total_size']))
            blocks = calculate_blocks(research_stats[label]['total_size'])
            cost = (blocks - 1) * BLOCK_MONTH_COST
            research_stats_table[2].append(blocks)
            research_stats_table[3].append(cost)
            cumulative_cost += cost
    return research_stats_table, cumulative_cost


def send_monthly_owner_reports():
    projects = Project.objects.filter(delete_date__isnull=True).all()
    for project in projects:
        details = project_detail_data(project.id)
        project = Project.objects.get(pk=project.id)
        cost_table, cumulative_cost = research_cost_table(project.id)
        params = {'project': project, 'details': details, 'research_stats': cost_table, 'total_cost': cumulative_cost, 'sitename': os.environ.get("SITE_NAME")}
        msg_plain = render_to_string('projects/owner_report.txt', params)
        msg_html = render_to_string('projects/owner_report.html', params)
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

send_monthly_owner_reports()