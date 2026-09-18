from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from apps.cards.models import VCard, VCardStatus, VCardVisibility

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
        vector = SearchVector(*SEARCH_FIELDS)
        query = SearchQuery(q)
        queryset = queryset.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0).order_by("-rank")
    else:
        queryset = queryset.order_by("-is_featured", "-created_at")

    return queryset
