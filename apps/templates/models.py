from django.db import models

from apps.core.models import BaseModel
from apps.core.validators import validate_image_file


class CardTemplate(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    preview_image = models.ImageField(upload_to="templates/previews/", blank=True, null=True, validators=[validate_image_file])
    category = models.CharField(max_length=100, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
