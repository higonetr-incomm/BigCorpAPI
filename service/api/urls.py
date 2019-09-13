from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    path(
        'employees/', views.employees, name='employees'
        ),  # list of employees
    path(
        'employees/<int:employee_id>/', views.employees, name='employees'
        ),  # detail of employee
]
