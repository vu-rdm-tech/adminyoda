from django.urls import path

from . import views

urlpatterns = [
    path('', views.projects_index_table, name='projects_index'),
    path('storage', views.projects_storage, name='projects_storage'),
    path('<int:project_id>', views.project_detail, name='project_detail'),
    path('project_size_chart_json/<int:project_id>', views.project_size_chart_json, name='project_size_chart_json'),
    path('size_breakdown_chart_json', views.size_breakdown_chart_json, name='size_breakdown_chart_json'),
    path('project_research_size_chart_json/<int:project_id>', views.project_research_size_chart_json, name='project_research_size_chart_json'),
    path('project_vault_size_chart_json/<int:project_id>', views.project_vault_size_chart_json, name='project_vault_size_chart_json'),
    path('project_delta_chart_json/<int:project_id>', views.project_delta_chart_json, name='project_delta_chart_json'),
]