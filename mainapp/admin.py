from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, ModelForm  # import forms
from django.contrib import admin
from .models import *   # import all models here

from PIL import Image


class NoteBookAdminForm(ModelForm):  # requirements for download images upper then 400 px

    MIN_RESOLUTIONS = (400, 400)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = 'Загружайте изображения {}x{}'.format(*self.MIN_RESOLUTIONS)

    def clean_image(self):
        image = self.cleaned_data['image']
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTIONS
        if img.height < min_height or img.width < min_width:
            raise ValidationError('Разрешение изображения меньше минимального')
        return image


class NotebookAdmin(admin.ModelAdmin):

    form = NoteBookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='notebooks'))
            # create notebook goods only in notebooks category
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='smartphone'))
            # create smartphone goods only in smartphone category
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)   # Register models in admin panel.
admin.site.register(Notebook, NotebookAdmin)
admin.site.register(Smartphone, SmartphoneAdmin)
# Add SmartphoneAdmin for create smartphone goods only in smartphone category
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
