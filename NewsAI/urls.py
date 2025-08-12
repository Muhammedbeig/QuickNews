# NewsAI/urls.py
from django.contrib import admin
from django.urls import path
from QuickNews import views as quick_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # “home” view from QuickNews.views
    path('', quick_views.index, name='index'),

    # process-article view
    path('process-article/', quick_views.process_article, name='process_article'),

    # history endpoint
    path('get-history/', quick_views.get_history, name='get_history'),

    path('search_with_context/', quick_views.search_with_context, name='search_with_context'),

    # fetch a single article by ID
    path('get-article/<int:article_id>/', quick_views.get_article, name='get_article'),

    # delete an article by ID
    path('delete-article/<int:article_id>/', quick_views.delete_article, name='delete_article'),
]
