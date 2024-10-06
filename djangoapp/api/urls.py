from django.urls import path
from api.views import ImageURLView, ProductView, ResolutionView, PeriodView, ChatGPTAPIView

urlpatterns = [
    path("image_url/", ImageURLView.as_view(), name="image_url"),
    path("product/", ProductView.as_view(), name="product"),
    path("resolution/", ResolutionView.as_view(), name="resolution"),
    path("period/", PeriodView.as_view(), name="period"),
    path('chat/', ChatGPTAPIView.as_view(), name='chatgpt-api'),
]
