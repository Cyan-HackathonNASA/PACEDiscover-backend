from django.urls import path
from api.views import GetImageURLView

urlpatterns = [
    path("get_image_url/", GetImageURLView.as_view(), name="get_image_url"),
]
