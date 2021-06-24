from django.urls import path

from . import views

urlpatterns = [
    path('', views.projects_index, name='projects_index'),
    path('storage', views.projects_storage, name='projects_storage'),
    path('<int:project_id>', views.project_detail, name='project_detail'),
]