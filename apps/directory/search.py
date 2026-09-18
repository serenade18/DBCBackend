from functools import reduce
from operator import or_

from django.db.models import Q

from apps.cards.models import VCard, VCardStatus, VCardVisibility

# §37: portable across DB engines via icontains — swap for MySQL FULLTEXT
# (a migration-added FULLTEXT index + a raw MATCH ... AGAINST annotation) or
# Elasticsearch/OpenSearch once relevance ranking or raw-event volume
# actually requires it; the public search API here wouldn't need to change.
SEARCH_FIELDS = ["display_name", "company_name", "job_title", "bio", "location", "industry"]


def base_directory_queryset():
    """§35/§37: only cards the owner explicitly opted into the directory,
    that are actually public and published."""
    return VCard.objects.filter(
        is_directory_visible=True, status=VCardStatus.PUBLISHED, visibility=VCardVisibility.PUBLIC,
    )


def search_directory(*, q="", category="", location="", industry="", company="", profession=""):
    queryset = base_directory_queryset()

    if category:
        queryset = queryset.filter(job_title__icontains=category.replace("-", " "))
    if profession:
        queryset = queryset.filter(job_title__icontains=profession)
    if location:
        queryset = queryset.filter(location__icontains=location)
    if industry:
        queryset = queryset.filter(industry__icontains=industry)
    if company:
        queryset = queryset.filter(company_name__icontains=company)

    if q:
        condition = reduce(or_, (Q(**{f"{field}__icontains": q}) for field in SEARCH_FIELDS))
        queryset = queryset.filter(condition)

    return queryset.order_by("-is_featured", "-created_at")
