from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse

from .models import Votacion, Opcion, Voto
from .forms import RegistroForm, AccesoCodigoForm, VotacionForm


# ==========================================
# PÁGINA DE INICIO
# ==========================================

def inicio(request):
    ahora = timezone.now()

    votaciones = Votacion.objects.filter(
        activa=True,
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora
    ).order_by('-fecha_creacion')[:3]

    return render(
        request,
        'elecciones/inicio.html',
        {'votaciones': votaciones}
    )


# ==========================================
# LISTA DE VOTACIONES ACTIVAS
# ==========================================

def lista_votaciones(request):
    ahora = timezone.now()

    votaciones = Votacion.objects.filter(
        activa=True,
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora
    ).order_by('fecha_inicio')

    return render(
        request,
        'elecciones/votaciones.html',
        {'votaciones': votaciones}
    )


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            login(request, usuario)

            messages.success(
                request,
                'Tu cuenta de Organizador se creó correctamente.'
            )

            return redirect('elecciones:lista_votaciones')
    else:
        form = RegistroForm()

    return render(
        request,
        'elecciones/registro.html',
        {'form': form}
    )


# ==========================================
# INICIO DE SESIÓN
# ==========================================

def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)

            messages.success(
                request,
                'Has iniciado sesión correctamente.'
            )

            return redirect('elecciones:lista_votaciones')
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        'elecciones/login.html',
        {'form': form}
    )


# ==========================================
# CERRAR SESIÓN
# ==========================================

def cerrar_sesion(request):
    if request.method == 'POST':
        logout(request)

        messages.success(
            request,
            'Has cerrado sesión.'
        )

    return redirect('elecciones:inicio')


# ==========================================
# INGRESAR CON CÓDIGO DE ACCESO
# ==========================================

def ingresar_codigo(request):
    if request.method == 'POST':
        form = AccesoCodigoForm(request.POST)

        if form.is_valid():
            codigo = form.cleaned_data['codigo'].strip().upper()

            votacion = Votacion.objects.filter(
                codigo_acceso=codigo
            ).first()

            if votacion and votacion.esta_abierta():
                return redirect(
                    'elecciones:votar_participante',
                    codigo=votacion.codigo_acceso
                )

            messages.error(
                request,
                'El código es inválido o la votación ya finalizó.'
            )
    else:
        form = AccesoCodigoForm()

    return render(
        request,
        'elecciones/ingresar_codigo.html',
        {'form': form}
    )


# ==========================================
# VOTAR COMO PARTICIPANTE
# No requiere una cuenta registrada
# ==========================================

def votar_por_codigo(request, codigo):
    votacion = get_object_or_404(
        Votacion,
        codigo_acceso=codigo.upper()
    )

    if not votacion.esta_abierta():
        messages.error(
            request,
            'Esta votación ya no está abierta.'
        )

        return redirect('elecciones:inicio')

    # Crear una sesión para el participante anónimo
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Comprobar si el participante ya votó
    if request.user.is_authenticated:
        ya_voto = Voto.objects.filter(
            usuario=request.user,
            votacion=votacion
        ).exists()
    else:
        ya_voto = Voto.objects.filter(
            session_key=session_key,
            votacion=votacion,
            usuario__isnull=True
        ).exists()

    if ya_voto:
        messages.info(
            request,
            'Ya has registrado tu voto en esta votación.'
        )

        return redirect(
            'elecciones:resultados_por_codigo',
            codigo=votacion.codigo_acceso
        )

    opciones = votacion.opciones.all()

    if request.method == 'POST':
        opcion_id = request.POST.get('opcion')
        opcion = opciones.filter(pk=opcion_id).first()

        if not opcion:
            messages.error(
                request,
                'Selecciona una opción válida.'
            )
        else:
            try:
                with transaction.atomic():
                    # Comprobar nuevamente antes de guardar
                    if request.user.is_authenticated:
                        duplicado = Voto.objects.filter(
                            usuario=request.user,
                            votacion=votacion
                        ).exists()
                    else:
                        duplicado = Voto.objects.filter(
                            session_key=session_key,
                            votacion=votacion,
                            usuario__isnull=True
                        ).exists()

                    if duplicado:
                        messages.info(
                            request,
                            'Ya has registrado tu voto.'
                        )
                    else:
                        if request.user.is_authenticated:
                            Voto.objects.create(
                                usuario=request.user,
                                votacion=votacion,
                                opcion=opcion
                            )
                        else:
                            Voto.objects.create(
                                session_key=session_key,
                                votacion=votacion,
                                opcion=opcion
                            )

                        messages.success(
                            request,
                            '¡Tu voto se ha registrado con éxito!'
                        )

                return redirect(
                    'elecciones:resultados_por_codigo',
                    codigo=votacion.codigo_acceso
                )

            except Exception:
                messages.error(
                    request,
                    'No se pudo registrar el voto. Inténtalo nuevamente.'
                )

    return render(
        request,
        'elecciones/votar.html',
        {
            'votacion': votacion,
            'opciones': opciones
        }
    )


# Nombre utilizado en urls.py
votar_participante = votar_por_codigo


# ==========================================
# VOTAR POR ID
# ==========================================

@login_required
def votar(request, votacion_id):
    votacion = get_object_or_404(
        Votacion,
        pk=votacion_id
    )

    return redirect(
        'elecciones:votar_participante',
        codigo=votacion.codigo_acceso
    )


# ==========================================
# RESULTADOS POR ID
# ==========================================

def resultados(request, votacion_id):
    votacion = get_object_or_404(
        Votacion,
        pk=votacion_id
    )

    return redirect(
        'elecciones:resultados_por_codigo',
        codigo=votacion.codigo_acceso
    )


# ==========================================
# MOSTRAR RESULTADOS
# ==========================================

def resultados_por_codigo(request, codigo):
    votacion = get_object_or_404(
        Votacion,
        codigo_acceso=codigo.upper()
    )

    opciones = votacion.opciones.all()

    total_votos = Voto.objects.filter(
        votacion=votacion
    ).count()

    datos_resultados = []

    for opcion in opciones:
        cantidad = Voto.objects.filter(
            votacion=votacion,
            opcion=opcion
        ).count()

        porcentaje = (
            round(cantidad * 100 / total_votos, 1)
            if total_votos > 0
            else 0.0
        )

        datos_resultados.append({
            'opcion': opcion,
            'cantidad': cantidad,
            'porcentaje': porcentaje
        })

    return render(
        request,
        'elecciones/resultados.html',
        {
            'votacion': votacion,
            'resultados': datos_resultados,
            'total_votos': total_votos
        }
    )


# ==========================================
# API DE RESULTADOS PARA ACTUALIZACIÓN DINÁMICA
# ==========================================

def api_resultados_votacion(request, codigo):
    votacion = get_object_or_404(
        Votacion,
        codigo_acceso=codigo.upper()
    )

    opciones = votacion.opciones.all()

    total_votos = Voto.objects.filter(
        votacion=votacion
    ).count()

    datos = []

    for opcion in opciones:
        cantidad = Voto.objects.filter(
            votacion=votacion,
            opcion=opcion
        ).count()

        porcentaje = (
            round(cantidad * 100 / total_votos, 1)
            if total_votos > 0
            else 0.0
        )

        datos.append({
            'id': opcion.id,
            'texto': opcion.texto,
            'cantidad': cantidad,
            'porcentaje': porcentaje
        })

    return JsonResponse({
        'titulo': votacion.titulo,
        'total_votos': total_votos,
        'resultados': datos
    })


# ==========================================
# CREAR VOTACIÓN
# Cualquier usuario autenticado puede crearla
# ==========================================

@login_required
def crear_votacion(request):
    if request.method == 'POST':
        form = VotacionForm(request.POST)

        if form.is_valid():
            opciones_texto = form.cleaned_data['opciones_lista']

            try:
                with transaction.atomic():
                    # Guardar la votación
                    votacion = form.save(commit=False)
                    votacion.creador = request.user
                    votacion.save()

                    # Guardar todas sus opciones
                    for texto in opciones_texto:
                        Opcion.objects.create(
                            votacion=votacion,
                            texto=texto
                        )

                messages.success(
                    request,
                    '¡La votación se creó correctamente!'
                )

                return redirect(
                    'elecciones:resultados_por_codigo',
                    codigo=votacion.codigo_acceso
                )

            except Exception:
                messages.error(
                    request,
                    'Ocurrió un error al guardar la votación. '
                    'Verifica los datos e inténtalo nuevamente.'
                )
    else:
        form = VotacionForm()

    return render(
        request,
        'elecciones/crear_votacion.html',
        {'form': form}
    )