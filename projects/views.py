from django.http import HttpResponse
from django.shortcuts import render
from .forms import ProjectForm

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def new_project(request):
    form = ProjectForm
    return render(request, 'projects/project_edit.html', {'form': form})