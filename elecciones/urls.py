from django.urls import path
from . import views

app_name = 'elecciones'

urlpatterns = [
    # Inicio y listado general
    path('', views.inicio, name='inicio'),
    path('votaciones/', views.lista_votaciones, name='lista_votaciones'),

    # Autenticación de Organizadores
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),

    # Creación de votaciones (Solo organizadores)
    path('crear/', views.crear_votacion, name='crear_votacion'),

    # --- ACCESO PARA PARTICIPANTES (CÓDIGO / QR) ---
    # Formulario para ingresar el código de 8 caracteres
    path('ingresar/', views.ingresar_codigo, name='ingresar_codigo'),
    
    # Votar por ID (usuarios registrados) o por Código (participantes anónimos / QR)
    path('votar/<int:votacion_id>/', views.votar, name='votar'),
    path('votar/codigo/<str:codigo>/', views.votar_participante, name='votar_participante'),

    # --- RESULTADOS Y API EN TIEMPO REAL ---
    # Vista HTML de resultados
    path('resultados/<int:votacion_id>/', views.resultados, name='resultados'),
    path('resultados/codigo/<str:codigo>/', views.resultados_por_codigo, name='resultados_por_codigo'),
    
    # Endpoint API JSON (Utilizado por JavaScript para refrescar los datos automáticamente)
    path('api/resultados/<str:codigo>/', views.api_resultados_votacion, name='api_resultados'),
]