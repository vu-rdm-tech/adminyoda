from django.http import JsonResponse
from django.shortcuts import render
from projects.models import Project, MiscStats, VaultDataset, ResearchFolder, Department
from datetime import datetime

start_month = 6
start_year = 2021
today = datetime.now()
end_month = today.month
end_year = today.year

def _get_monthly_miscstats():
    stats = []
    print(end_month)
    print(end_year)
    for year in range(start_year, end_year+1):
        print(year)
        if year == start_year:
            m1 = start_month
        else:
            m1 = 1
        if year == end_year:
            m2 = end_month
        else:
            m2 = 12
        for month in range(m1, m2+1):
            print(month)
            s = MiscStats.objects.filter(collected__year=year, collected__month=month).order_by('collected').last()
            s.label = f'{month} - {year}'
            stats.append(s)
    return stats

print(_get_monthly_miscstats())