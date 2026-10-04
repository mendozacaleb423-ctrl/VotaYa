from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Votacion, Opcion


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu correo electrónico'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']

        labels = {
            'username': 'Nombre de usuario',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Crea un nombre de usuario'
            }),
        }

    def _init_(self, *args, **kwargs):
        super()._init_(*args, **kwargs)

        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Crea una contraseña'
            })

        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Confirma tu contraseña'
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class AccesoCodigoForm(forms.Form):
    codigo = forms.CharField(
        max_length=50,
        label='Código de acceso',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu código de votación'
        })
    )


class VotacionForm(forms.ModelForm):
    opciones = forms.CharField(
        label='Opciones de respuesta',
        help_text='Escribe al menos dos opciones, una por línea.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Sí\nNo\nTal vez'
        })
    )

    class Meta:
        model = Votacion
        fields = [
            'titulo',
            'descripcion',
            'fecha_inicio',
            'fecha_fin'
        ]

        labels = {
            'titulo': 'Título de la encuesta',
            'descripcion': 'Descripción',
            'fecha_inicio': 'Fecha y hora de inicio',
            'fecha_fin': 'Fecha y hora de finalización',
        }

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe el título de tu encuesta'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente tu encuesta'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'fecha_fin': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
        }

    def _init_(self, *args, **kwargs):
        super()._init_(*args, **kwargs)

        formato = '%Y-%m-%dT%H:%M'

        self.fields['fecha_inicio'].input_formats = [formato]
        self.fields['fecha_fin'].input_formats = [formato]

    def clean(self):
        cleaned_data = super().clean()

        inicio = cleaned_data.get('fecha_inicio')
        fin = cleaned_data.get('fecha_fin')

        if inicio and fin and fin <= inicio:
            self.add_error(
                'fecha_fin',
                'La fecha de finalización debe ser posterior al inicio.'
            )

        opciones_texto = cleaned_data.get('opciones', '')

        opciones = [
            texto.strip()
            for texto in opciones_texto.splitlines()
            if texto.strip()
        ]

        if len(opciones) < 2:
            self.add_error(
                'opciones',
                'Debes escribir al menos dos opciones diferentes.'
            )
        elif len(set(opciones)) != len(opciones):
            self.add_error(
                'opciones',
                'No repitas las opciones de respuesta.'
            )

        cleaned_data['opciones_lista'] = opciones

        return cleaned_data


class VotarForm(forms.Form):
    opcion = forms.ChoiceField(
        label='Selecciona tu opción',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        choices=[]
    )

    def _init_(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])
        super()._init_(*args, **kwargs)
        self.fields['opcion'].choices = choices