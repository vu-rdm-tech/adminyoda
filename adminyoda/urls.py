"""adminyoda URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls')),
    path('', views.index, name='index'),
    path('download_billing_report/<slug:year>', views.download_billing_report, name='download_billing_report'),
    path('download_statistics_report', views.download_statistics_report, name='download_statistics_report'),
    path('size_chart_json', views.size_chart_json, name='size_chart_json'),
    path('size_breakdown_chart_json', views.size_breakdown_chart_json, name='size_breakdown_chart_json'),
    path('research_percentage_chart_json', views.research_percentage_chart_json, name='research_percentage_chart_json'),
    path('research_size_chart_json', views.research_size_chart_json, name='research_size_chart_json'),
    path('vault_size_chart_json', views.vault_size_chart_json, name='vault_size_chart_json'),
    path('user_chart_json', views.user_chart_json, name='user_chart_json'),
    path('project_chart_json', views.project_chart_json, name='project_chart_json'),
    path('group_chart_json', views.group_chart_json, name='group_chart_json'),
    path('storage_chart_json', views.storage_chart_json, name='storage_chart_json'),
    path('dataset_chart_json', views.dataset_chart_json, name='dataset_chart_json'),
    path('faculty_chart_json', views.faculty_chart_json, name='faculty_chart_json'),
]
