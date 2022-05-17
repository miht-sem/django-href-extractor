from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name="main"),
    path('add/', views.add_url, name="add_url"),
    path('delete/<int:url_id>/', views.delete_url, name="delete_url"),
    path('delete_all_urls/', views.delete_all_urls, name="delete_all_urls"),
    path('show_url/<int:url_id>/', views.parsed, name="show_url"),
]