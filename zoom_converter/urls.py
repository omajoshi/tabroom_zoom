from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

app_name = 'zoom_converter'
urlpatterns = [
    path('', views.tournament_list, name='tournament_list'),
    path('<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('<int:pk>/update/', views.TournamentUpdate.as_view(), name='tournament_update'),
    path('<int:pk>/access/', views.tournament_access, name='tournament_access'),
    path('<int:pk>/access/<int:revoke_user>/revoke/', views.tournament_access_revoke, name='tournament_access_revoke'),
    path('<int:pk>/access/<int:director_user>/director/', views.tournament_access_director, name='tournament_access_director'),
    path('<int:tournament>/<int:pk>/', views.EventDetail.as_view(), name='event'),
    path('<int:tournament>/<int:event>/<int:pk>/', views.RoundDetail.as_view(), name='round'),
    path('<int:tournament>/<int:event>/<int:round>/<int:pk>/', views.breakout_room_detail, name='breakout_room'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/email/activate/', views.awaiting_email_activation, name='awaiting_email_activation'),
    path('accounts/email/activate/send/', views.send_email_activation, name='send_email_activation'),
    path('accounts/email/activate/<uidb64>/<token>/', views.activate_email, name='activate_email'),
    path('accounts/tabroom/activate/', views.awaiting_tabroom_activation, name='awaiting_tabroom_activation'),
    path('accounts/tabroom/activate/send/', views.send_tabroom_activation, name='send_tabroom_activation'),
    path('accounts/tabroom/activate/<uidb64>/<token>/', views.activate_tabroom, name='activate_tabroom'),
    path('accounts/zoom/activate/', views.awaiting_zoom_activation, name='awaiting_zoom_activation'),
    path('accounts/zoom/activate/send/', views.send_zoom_activation, name='send_zoom_activation'),
    path('accounts/zoom/activate/<uidb64>/<token>/', views.activate_zoom, name='activate_zoom'),
]
