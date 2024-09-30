# myproject/urls.py
from django.contrib import admin
from django.urls import path, include  # Include 'include' if you're going to use it
from django.views.generic import RedirectView  # Import RedirectView
from queries.views import search_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('queries/', search_view, name='search'),
    path('', RedirectView.as_view(url='/queries/')),  # Redirect root URL to /queries/
]

