from projects.views import project_detail_data
from projects.models import Project
import logging
import os
import datetime
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_monthly_owner_reports():
    projects = Project.objects.all()
    for project in projects:
        details = project_detail_data(project.id)
        project = Project.objects.get(pk=project.id)
        params = {'project': project, 'details': details, 'sitename': os.environ.get("SITE_NAME")}
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