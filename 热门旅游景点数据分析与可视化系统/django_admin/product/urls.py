# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('city', views.city, name='city'),
    path('cities', views.get_all_cities, name='get_all_cities'),
    path('attractions', views.get_attractions_by_city, name='get_attractions_by_city'),
    path('analyze_attraction_reviews', views.analyze_attraction_reviews, name='analyze_attraction_reviews'),
    path('analyze_attraction_introduction', views.analyze_attraction_introduction, name='analyze_attraction_introduction'),
    path('analyze_city_attraction_distribution', views.analyze_city_attraction_distribution, name='analyze_city_attraction_distribution'),
    path('review_analysis', views.review_analysis, name='review_analysis'),
    path('price_analyze', views.price_analyze, name='price_analyze'),
    path('analyze_hot', views.analyze_hot, name='analyze_hot'),
]

