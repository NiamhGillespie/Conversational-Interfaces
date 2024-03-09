
from django.contrib import admin
from django.urls import path, re_path
from api_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'(movierec/(.*)/(.*)/(.*))', views.getMovieRecommendations, name='GetMovieRecs'),
    re_path(r'(movieinfo/(.*))', views.getMovieInformation, name='GetMovieInfo'),
]

