from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from product.views import LojaHome

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuario.urls')),
    path('loja/', LojaHome.as_view(), name='loja_home'),
    path('carrinho/', include('pedido.carrinho_urls')),
    path('produtos/', include('product.urls')),
    path('categorias/', include('category.urls')),
    path('pedidos/', include('pedido.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
