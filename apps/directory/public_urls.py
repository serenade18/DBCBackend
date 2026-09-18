from django.urls import path

from apps.directory.views import PublicDirectorySearchView

urlpatterns = [
    path("", PublicDirectorySearchView.as_view(), name="public-directory-search"),
]
