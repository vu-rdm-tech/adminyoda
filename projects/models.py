from django.db import models


class Person(models.Model):
    vunetid = models.CharField(max_length=6)
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    orcid = models.CharField(max_length=19, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vunetid


class Department(models.Model):
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    faculty = models.CharField(max_length=255)
    institute = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.faculty} - {self.institute} - {self.name}'

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


class VaultDataset(models.Model):
    yoda_name = models.CharField(max_length=255)
    vault_folder = models.ForeignKey(ResearchFolder, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)  # just in case


class Publications(models.Model):
    vault_dataset = models.ForeignKey(VaultDataset, on_delete=models.CASCADE, blank=True, null=True)
    yoda_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)  # just in case


class Datamanager(models.Model):
    category = models.CharField(max_length=255)
    vunetid = models.CharField(max_length=6)


class ResearchStats(models.Model):
    research_folder = models.ForeignKey(ResearchFolder, on_delete=models.SET_NULL, blank=True, null=True)
    size = models.BigIntegerField()
    created = models.DateTimeField(auto_now_add=True)


class VaultStats(models.Model):
    research_folder = models.ForeignKey(VaultFolder, on_delete=models.CASCADE)
    size = models.BigIntegerField()
    created = models.DateTimeField(auto_now_add=True)
