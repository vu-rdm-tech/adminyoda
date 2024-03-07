import json
import os
import re
import shutil
from datetime import datetime, timedelta, date
import logging
from projects.models import (
    ResearchFolder,
    VaultFolder,
    VaultDataset,
    VaultStats,
    ResearchStats,
    Person,
    Datamanager,
    MiscStats,
    Project,
    Department,
    Budget,
)
from django.utils.timezone import now, make_aware
from django.db.models.base import ObjectDoesNotExist

DATADIR = os.environ.get("DATADIR")
logger = logging.getLogger(__name__)


# don't forget to 'sudo systemctl restart qcluster' when code here is changed

def _parse_yoda_name(yoda_name):
    parts = yoda_name.split("-")
    faculty = parts[1]
    department_abbr = parts[2]
    projectname = ("-").join(parts[3:])
    return faculty, department_abbr, projectname


def create_projects():
    # create projects from research folders
    # assume all departments are already in the database
    logger.info(f"Creating projects from orphaned research folders.")
    for rf in ResearchFolder.objects.all():
        if rf.project is None:
            logger.info(f"Found orphaned research folder {rf.yoda_name}")
            if len(rf.yoda_name.split("-")) > 3:
                faculty, department_abbr, projectname = _parse_yoda_name(rf.yoda_name)
                if Department.objects.filter(abbreviation=department_abbr, faculty__iexact=faculty).exists():
                    logger.info(f"Create project for {rf.yoda_name} in {department_abbr}")
                    d = Department.objects.get(abbreviation=department_abbr, faculty__iexact=faculty)
                    owner = Person.objects.get(pk=16)
                    budget = Budget.objects.get(pk=46)
                    p, created = Project.objects.get_or_create(
                        title=projectname,
                        department=d,
                        owner=owner,
                        budget=budget,
                        request_date=rf.created,
                        admin_remarks=f"Created automatically from research folder name on {now().date()}",
                    )
                    p.save()
                    rf.project = p
                    rf.save()

def clean_projects():
    # delete projects without research folders
    logger.info(f"Deleting projects without research folders.")
    for p in Project.objects.all():
        active = False
        for r in ResearchFolder.objects.filter(project=p):
            if r.deleted is None:
                active = True
        if not active:
            logger.info(f"Set project {p.title} as deleted.")
            p.delete_date = now()
            p.save()

def clean_folders():
        # when a folder is deleted in Yoda it will no longer be part of the weekly data export. That means we can
    # consider research, vault and dataset folder records last updated <days> before the last collection date (<last_update>) as deleted in Yoda.
    days = 2
    last_update = MiscStats.objects.order_by("collected").last().collected
    cutoff = make_aware(datetime.combine(last_update, datetime.min.time())) - timedelta(
        days=days
    )
    logger.info(f"Mark folders and datasets last updated before {cutoff} as deleted.")
    rf = ResearchFolder.objects.filter(deleted__isnull=True).filter(updated__lte=cutoff)
    vf = VaultFolder.objects.filter(deleted__isnull=True).filter(updated__lte=cutoff)
    vd = VaultDataset.objects.filter(deleted__isnull=True).filter(updated__lte=cutoff)
    for f in rf:
        ResearchStats.objects.update_or_create(
            research_folder=f,
            collected=date.today(),
            defaults={"size": 0, "revision_size": 0},
        )
        logger.info(f"Setting ResearchFolder {f.yoda_name} as deleted.")
    for f in vf:
        VaultStats.objects.update_or_create(
            vault_folder=f,
            collected=date.today(),
            defaults={"size": 0},
        )
        logger.info(f"Setting VaultFolder {f.yoda_name} as deleted.")
    for d in vd:
        logger.info(f"Setting VaulDataset {d.yoda_name} as deleted.")
    vd.update(deleted=now(), size=0)
    vf.update(deleted=now())
    rf.update(deleted=now())

def cleanup():
    clean_folders()
    clean_projects()

def process_irods_stats():
    files = sorted(os.listdir(DATADIR))
    logger.info(f'listing of datadir: [{", ".join(files)}]')
    cnt = 0
    for file in files:
        if file.startswith("yodastats-"):
            cnt = cnt + 1
            logger.info(f"processing {file}")
            with open(f"{DATADIR}/{file}", "r") as fp:
                data = json.load(fp)
                if data["collected"] is None:
                    # old style
                    filedate_str = os.path.splitext(file)[0].split("-")[1]
                else:
                    filedate_str = data["collected"]
                filedate = datetime.strptime(filedate_str, "%Y%m%d").date()
                researchgroup_cnt = 0
                dataset_cnt = 0
                published_cnt = 0
                research_size_total = 0
                vault_size_total = 0
                for group in data["groups"]:
                    if group.startswith("research-"):
                        logger.info(f"processing group {group} in {file}")
                        internal_users = 0
                        external_users = 0
                        for email in data["groups"][group]["members"]:
                            if email.endswith(("vu.nl", "acta.nl")):
                                internal_users += 1
                            else:
                                external_users += 1
                        for email in data["groups"][group]["read_members"]:
                            if email.endswith(("vu.nl", "acta.nl")):
                                internal_users += 1
                            else:
                                external_users += 1
                        researchgroup_cnt += 1
                        researchfolder, created = ResearchFolder.objects.get_or_create(
                            yoda_name=group
                        )
                        researchfolder.category = data["groups"][group]["category"]
                        researchfolder.data_classification = data["groups"][group][
                            "data_classification"
                        ]
                        researchfolder.internal_users = internal_users
                        researchfolder.external_users = external_users
                        researchfolder.save()

                        vaultname = researchfolder.yoda_name.replace(
                            "research-", "vault-", 1
                        )
                        VaultFolder.objects.update_or_create(
                            research_folder=researchfolder,
                            defaults={"yoda_name": vaultname},
                        )
                    elif group.startswith("datamanager-"):
                        logger.info(f"processing datamanager group {group} in {file}")
                        email_regex = (
                            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
                        )
                        for m in data["groups"][group]["members"]:
                            valid = False
                            if re.fullmatch(email_regex, m):  # email
                                u, created = Person.objects.get_or_create(email=m)
                                valid = True
                            elif len(m) == 6:  # vunetid
                                u, created = Person.objects.get_or_create(vunetid=m)
                                valid = True
                            if valid:
                                u.save()
                                d, created = Datamanager.objects.get_or_create(
                                    user=u, yoda_name=group
                                )
                                d.category = data["groups"][group]["category"]
                                d.save()
                for collection in data["collections"]:
                    logger.info(f"process collection {collection}")
                    if collection.startswith("research-"):
                        researchfolder = ResearchFolder.objects.get(
                            yoda_name=collection
                        )
                        researchsize = data["collections"][collection]["size"]
                        try:
                            revisionsize = data["revision_collections"][collection][
                                "size"
                            ]
                        except:
                            revisionsize = 0
                        researchnewest = data["collections"][collection]["newest"]
                        ResearchStats.objects.update_or_create(
                            research_folder=researchfolder,
                            collected=filedate,
                            defaults={
                                "size": researchsize,
                                "revision_size": revisionsize,
                                "newest_file": researchnewest,
                            },
                        )
                        research_size_total += researchsize
                    elif collection.startswith("vault-"):
                        try:
                            vaultfolder = VaultFolder.objects.get(yoda_name=collection)
                            for set in data["collections"][collection]["datasets"]:
                                dataset_cnt += 1
                                dataset, created = VaultDataset.objects.get_or_create(
                                    yoda_name=set, vault_folder=vaultfolder
                                )
                                dataset.status = data["collections"][
                                    vaultfolder.yoda_name
                                ]["datasets"][set]["status"]
                                dataset.retention = int(
                                    data["collections"][vaultfolder.yoda_name][
                                        "datasets"
                                    ][set]["retention_period"]
                                )
                                dataset.data_classification = data["collections"][
                                    vaultfolder.yoda_name
                                ]["datasets"][set]["data_classification"]
                                dataset.size = data["collections"][
                                    vaultfolder.yoda_name
                                ]["datasets"][set]["size"]
                                if dataset.status == "PUBLISHED":
                                    published_cnt += 1
                                dataset.save()
                            vaultsize = data["collections"][collection]["size"]
                            VaultStats.objects.update_or_create(
                                vault_folder=vaultfolder,
                                collected=filedate,
                                defaults={"size": vaultsize},
                            )
                            vault_size_total += vaultsize
                        except ObjectDoesNotExist:
                            logger.warning(
                                f"VaultFolder {collection} does not exist in the database. Is it orphaned?"
                            )
                MiscStats.objects.update_or_create(
                    collected=filedate,
                    defaults={
                        "size_total": data["misc"]["size_total"],
                        "size_research": research_size_total,
                        "size_vault": vault_size_total,
                        "users_total": data["misc"]["users_total"],
                        "internal_users_total": data["misc"]["internal_users_total"],
                        "external_users_total": data["misc"]["external_users_total"],
                        "revision_size": data["misc"]["revision_size"],
                        "trash_size": data["misc"]["trash_size"],
                        "groups_total": researchgroup_cnt,
                        "datasets_total": dataset_cnt,
                        "published_total": published_cnt,
                        "projects_total": Project.objects.filter(
                            delete_date__isnull=True
                        )
                        .all()
                        .count,
                    },
                )

            logger.info(f"move {file} to archived")
            shutil.move(f"{DATADIR}/{file}", f"{DATADIR}/archived/{file}")

    logger.info(f"{cnt} files processed")


# process_irods_stats()
# cleanup()
