from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from vacations import pwa_views

urlpatterns = [
    path('manifest.webmanifest', pwa_views.manifest, name='pwa_manifest'),
    path('service-worker.js', pwa_views.service_worker, name='service_worker'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='vacations/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('vacations.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
