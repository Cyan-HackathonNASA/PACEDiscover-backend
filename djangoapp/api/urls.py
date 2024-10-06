from django.urls import path
from api.views import ImageView, ProductView, ResolutionView, PeriodView, ChatGPTAPIView

urlpatterns = [
    path("image/", ImageView.as_view(), name="image"),
    path("product/", ProductView.as_view(), name="product"),
    path("resolution/", ResolutionView.as_view(), name="resolution"),
    path("period/", PeriodView.as_view(), name="period"),
    path('chat/', ChatGPTAPIView.as_view(), name='chatgpt-api'),
]
