from django.urls import path

from apps.directory.views import DirectoryVisibilityView

urlpatterns = [
    path("vcards/<uuid:vcard_id>/", DirectoryVisibilityView.as_view(), name="directory-visibility"),
]
