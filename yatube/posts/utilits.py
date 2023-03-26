from django.core.paginator import Paginator

from yatube.constants import POST_ON_PAGE


def get_page_context(queryset, request):
    paginator = Paginator(queryset, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
