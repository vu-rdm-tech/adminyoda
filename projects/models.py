from django.db import models


class Person(models.Model):
    vunetid = models.CharField(max_length=6)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=50, blank=True)
    orcid = models.CharField(max_length=19, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vunetid} | {self.lastname}, {self.firstname}'


class Department(models.Model):
    name = models.CharField(max_length=255, blank=True)
    abbreviation = models.CharField(max_length=255, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    institute = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.faculty} {self.institute} {self.name}'

class Budget(models.Model):
    CODE_TYPES = (
        ('w', 'WBS-Element'),
        ('o', 'Order Number'),
        ('c', 'Cost Center item number'),
    )
    code = models.CharField(max_length=50)  # check this
    type = models.CharField(max_length=1, choices=CODE_TYPES)
    vunetid = models.CharField(max_length=6)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code


class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='project_owner')
    manager = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True,
                                related_name='project_manager')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    request_date = models.DateField()
    requested_size = models.IntegerField(default=500)
    storage_limit = models.IntegerField(default=500)
    admin_remarks = models.TextField(default='', blank=True)
    delete_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ResearchFolder(models.Model):
    category = models.CharField(max_length=255)
    yoda_name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.yoda_name


class VaultFolder(models.Model):
    yoda_name = models.CharField(max_length=255)
    research_folder = models.ForeignKey(ResearchFolder, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)  # just in case

    def __str__(self):
        return self.yoda_name

class VaultDataset(models.Model):
    yoda_name = models.CharField(max_length=255)
    vault_folder = models.ForeignKey(VaultFolder, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, blank=True, null=True)
    retention = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)  # just in case

    def __str__(self):
        return self.yoda_name


class Datamanager(models.Model):
    yoda_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    user = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ResearchStats(models.Model):
    research_folder = models.ForeignKey(ResearchFolder, on_delete=models.SET_NULL, blank=True, null=True)
    size = models.BigIntegerField()
    collected = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


class VaultStats(models.Model):
    vault_folder = models.ForeignKey(VaultFolder, on_delete=models.CASCADE)
    size = models.BigIntegerField()
    collected = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

class MiscStats(models.Model):
    size_total = models.BigIntegerField()
    size_vault = models.BigIntegerField(default=0)
    size_research = models.BigIntegerField(default=0)
    users_total = models.IntegerField()
    internal_users_total = models.IntegerField()
    external_users_total = models.IntegerField()
    projects_total = models.IntegerField(default=6)
    groups_total = models.IntegerField(default=17)
    datasets_total = models.IntegerField(default=8)
    published_total = models.IntegerField(default=0)
    revision_size = models.BigIntegerField()
    trash_size = models.BigIntegerField(default=0)
    collected = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)