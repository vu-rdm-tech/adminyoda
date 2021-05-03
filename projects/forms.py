from .models import Budget, Project
from django.forms import ModelForm

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ('title', 'description', 'owner', 'manager', 'department', 'budget', 'request_date')

class BudgetForm(ModelForm):
    class Meta:
        model = Budget
        fields = ('code', 'type', 'vunetid')