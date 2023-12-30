from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(template_name='authentication/signin.html'), name='signin'),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),  # Use views.signin for the custom login view
    path('signout/', views.signout, name='signout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_admin/', views.dashboard_admin, name='dashboard_admin'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),

    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('about/', views.about, name='about'),
    path('upload_photo/', views.upload_photo, name='upload_photo'),
    path('manage_users_form/', views.manage_users_form, name='manage_users_form'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('generate_excel/', views.generate_excel, name='generate_excel'),
    path('make_user_admin/', views.make_user_admin, name='make_user_admin'),
    path('delete_selected_activities/', views.delete_selected_activities, name='delete_selected_activities'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
