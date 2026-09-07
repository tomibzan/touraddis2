from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    # ✅ 1. Specific, literal paths MUST come first
    path('track-booking/', views.track_booking, name='track_booking'),
    path('book/<slug:slug>/', views.book_tour, name='book_tour'),
    
    # ✅ 2. Generic catch-all paths MUST come last
    path('', views.tour_list, name='tour_list'),
    path('<slug:slug>/', views.tour_detail, name='tour_detail'),
]