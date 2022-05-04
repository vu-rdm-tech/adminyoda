from projects.views import project_detail_data
from projects.models import Project


def message_text(project_id):
    details = project_detail_data(project_id)
    project = Project.objects.get(pk=project_id)
    text = 'Project details:\r\n' \
           f'Title: {details.project.title}\r\n' \
           f'Project owner: {project.owner.firstname} {project.owner.lastname}\r\n' \
           f'Department: {project.department.faculty} {project.department.institute} {project.department.name}\r\n' \
           f'Budget code: {project.budget.code}\r\n' \
           f'Budget owner: {project.budget.vunetid}\r\n' \
           'Please contact us at rdm@vu.nl if this information is incorrect or needs to be updated\r\n\r\n'

    text += 'Folders:\r\n'
    for r in details.research_folders:
        text += f'{r.research_name}: {r.research_size}\r\n' \
                f'{r.vault_name}: {r.vault_size}\r\n'
        if len(r.datasets) > 0:
            text += '\tDatasets in this Vault:\r\n'
        else:
            text += '\tNo datasets in this Vault'
        for d in r.datasets:
            print(d.name)
            text += f'\t\t{d.name} ({d.status}, retention:{d.retention}): {d.csize}\r\n'
        text += '\r\n'
    text += '\r\nProject total:\r\n' \
            f'Research:\t{details.research_size} = {details.research_blocks} {details.research_block_size} block(s)\r\n' \
            f'Vault:\t\t{details.vault_size} = {details.vault_blocks} {details.vault_block_size} block(s)\r\n' \
            f'\r\nMore information can be found on https://adminyoda.labs.vu.nl/projects/{project_id} (on campus or via eduvpn)'
    return text


print(message_text(7))
