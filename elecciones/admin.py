from django.contrib import admin
from .models import Votacion, Opcion, Voto


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'obtener_creador',
        'obtener_codigo',
        'fecha_inicio',
        'fecha_fin',
        'activa',
    )

    list_filter = ('activa', 'fecha_inicio', 'fecha_fin')
    search_fields = ('titulo', 'descripcion')
    inlines = [OpcionInline]

    @admin.display(description='Organizador/Creador')
    def obtener_creador(self, obj):
        if hasattr(obj, 'organizador') and obj.organizador:
            return obj.organizador
        elif hasattr(obj, 'creador') and obj.creador:
            return obj.creador
        return "—"

    @admin.display(description='Código de acceso')
    def obtener_codigo(self, obj):
        return getattr(obj, 'codigo_acceso', "—")

    def get_readonly_fields(self, request, obj=None):
        if hasattr(Votacion, 'codigo_acceso'):
            return ('codigo_acceso',)
        return ()


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ('texto', 'votacion')
    list_filter = ('votacion',)
    search_fields = ('texto',)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = (
        'obtener_votante',
        'votacion',
        'opcion',
        'obtener_fecha',
    )

    list_filter = ('votacion',)
    search_fields = (
        'usuario__username',
        'votacion__titulo',
        'opcion__texto',
    )

    @admin.display(description='Votante')
    def obtener_votante(self, obj):
        if hasattr(obj, 'usuario') and obj.usuario:
            return f"👤 {obj.usuario.username}"
        session_key = getattr(obj, 'session_key', None)
        if session_key:
            return f"🔑 Anónimo ({session_key[:8]}...)"
        return "🔑 Anónimo"

    @admin.display(description='Fecha de voto')
    def obtener_fecha(self, obj):
        for attr in ['fecha_voto', 'fecha_creacion', 'creado_en']:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return "—"

    def get_readonly_fields(self, request, obj=None):
        campos = [f.name for f in Voto._meta.fields]
        return tuple(campos)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False