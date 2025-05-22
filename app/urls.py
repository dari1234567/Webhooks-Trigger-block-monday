
from django.urls import include, path

from app import views


urlpatterns = [
    
    path("test", views.test, name="test"),
    path ("subscribe", views.subscribe, name="subscribe"),
    path("unsubscribe", views.unsubscribe, name="unsubscribe"),
    path("health", views.health, name="health"),
]
