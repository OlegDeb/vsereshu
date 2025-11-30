from django import forms
from django.utils.text import slugify
from django.forms import ModelChoiceField
from .models import Vacancy, VacancyResponse, Specialty
from slugify import slugify as slugify_extended
from regions.models import City, Region


class VacancyForm(forms.ModelForm):
    """Форма для создания вакансии"""
    class Meta:
        model = Vacancy
        fields = [
            'title', 'description', 'specialty', 'experience',
            'employment_type', 'work_nature', 'other_conditions',
            'salary', 'location', 'city'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название вакансии...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Опишите вакансию подробно...'
            }),
            'experience': forms.Select(attrs={
                'class': 'form-select',
            }),
            'employment_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'work_nature': forms.Select(attrs={
                'class': 'form-select',
            }),
            'other_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные условия работы...'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Дополнительная информация о месте работы...'
            }),
        }
        labels = {
            'title': 'Название вакансии',
            'description': 'Описание вакансии',
            'specialty': 'Специальность',
            'experience': 'Опыт работы',
            'employment_type': 'Тип занятости',
            'work_nature': 'Характер работы',
            'other_conditions': 'Другие условия',
            'salary': 'Зарплата',
            'location': 'Дополнительная информация о месте работы',
            'city': 'Город',
        }
        help_texts = {
            'salary': 'Укажите зарплату в рублях',
            'other_conditions': 'Необязательное поле',
            'location': 'Укажите адрес или дополнительную информацию о месте работы',
            'city': 'Выберите город из списка',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Фильтруем специальности
        specialty_field = self.fields['specialty']
        if isinstance(specialty_field, ModelChoiceField):
            specialty_field.queryset = Specialty.objects.all().order_by('name')
            specialty_field.widget.attrs.update({
                'class': 'form-select',
                'id': 'id_specialty',
            })
        
        # Делаем поле других условий необязательным
        self.fields['other_conditions'].required = False
        
        # Добавляем поле региона перед полем города
        self.fields['region'] = forms.ModelChoiceField(
            queryset=Region.objects.filter(is_active=True).order_by('name'),
            required=False,
            label='Регион',
            help_text='Сначала выберите регион, затем город',
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_region',
            }),
            empty_label='Выберите регион'
        )
        
        # Если вакансия редактируется и есть город, устанавливаем начальное значение региона
        if self.instance and self.instance.pk and hasattr(self.instance, 'city'):
            if self.instance.city:
                self.fields['region'].initial = self.instance.city.region_id
        
        # Фильтруем города по региону (если регион выбран)
        city_field = self.fields['city']
        if isinstance(city_field, ModelChoiceField):
            # Если вакансия редактируется и есть город, показываем города его региона
            if self.instance and self.instance.pk and hasattr(self.instance, 'city'):
                if self.instance.city:
                    city_field.queryset = City.objects.filter(
                        region=self.instance.city.region,
                        is_active=True
                    ).select_related('region')
                else:
                    city_field.queryset = City.objects.none()
            else:
                # При создании новой вакансии проверяем, есть ли регион в POST данных
                region_id = None
                if args and hasattr(args[0], 'get'):
                    region_id = args[0].get('region')
                
                if region_id:
                    try:
                        region_obj = Region.objects.get(pk=region_id, is_active=True)
                        city_field.queryset = City.objects.filter(
                            region=region_obj,
                            is_active=True
                        ).select_related('region')
                    except (Region.DoesNotExist, ValueError):
                        city_field.queryset = City.objects.none()
                else:
                    city_field.queryset = City.objects.none()
            
            city_field.widget.attrs.update({
                'class': 'form-select',
                'id': 'id_city',
            })
            city_field.empty_label = 'Сначала выберите регион'
        
        # Делаем город необязательным
        self.fields['city'].required = False
        # Делаем поле location необязательным
        self.fields['location'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data
        
        region = cleaned_data.get('region')
        city = cleaned_data.get('city')

        # Проверяем, что город принадлежит выбранному региону
        if region and city:
            if city.region_id != region.id:
                raise forms.ValidationError({
                    'city': 'Выбранный город не принадлежит выбранному региону.'
                })

        return cleaned_data

    def save(self, commit=True, author=None):
        vacancy = super().save(commit=False)
        if author:
            vacancy.author = author
        
        # Удаляем поле region из cleaned_data, так как оно не является полем модели Vacancy
        # Оно используется только для фильтрации городов
        if 'region' in self.cleaned_data:
            del self.cleaned_data['region']
        
        # Автоматически создаем слаг из заголовка
        if not vacancy.slug:
            base_slug = slugify_extended(vacancy.title)
            slug = base_slug
            counter = 1
            while Vacancy.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            vacancy.slug = slug
        
        # Если вакансия редактируется и была проверена модератором, отправляем на повторную модерацию
        if vacancy.pk and vacancy.is_moderated:
            vacancy.is_moderated = False

        if commit:
            # Используем полный save модели, чтобы вызвать логику модели
            vacancy.save()
        return vacancy


class VacancyResponseForm(forms.ModelForm):
    """Форма для отклика на вакансию"""
    class Meta:
        model = VacancyResponse
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Напишите сопроводительное письмо...'
            }),
        }
        labels = {
            'cover_letter': 'Сопроводительное письмо',
        }