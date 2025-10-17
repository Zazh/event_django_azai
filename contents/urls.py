from django.urls import path
from . import views

app_name = 'contents'

urlpatterns = [
    path('', views.home_page, name='home'),
    path('services/', views.services_list, name='services_list'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
    path('contacts/', views.contact_page, name='contacts'),

]