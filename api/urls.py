from django.urls import path
from api.views import GetImageURLView, GetProductsView

urlpatterns = [
    path("image_url/", GetImageURLView.as_view(), name="get_image_url"),
    path("product/", GetProductsView.as_view(), name="get_products"),
]
