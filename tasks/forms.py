from django import forms
from django.forms import ModelChoiceField
from slugify import slugify
from .models import Task, TaskResponse, Message, Review
from categories.models import Category, CategorySection
from regions.models import City, Region


class TaskForm(forms.ModelForm):
    """Форма для создания задачи"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'location_type', 'city', 'price', 'payment_period']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок задачи...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Опишите задачу подробно...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'location_type': forms.RadioSelect(attrs={
                'class': 'form-check-input',
            }),
            'city': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'payment_period': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'title': 'Заголовок задачи',
            'description': 'Описание задачи',
            'category': 'Категория',
            'location_type': 'Место выполнения задачи',
            'city': 'Город',
            'price': 'Стоимость',
            'payment_period': 'Период оплаты',
        }
        help_texts = {
            'city': 'Укажите город для работы у себя или у заказчика',
            'price': 'Укажите стоимость работы',
            'payment_period': 'Выберите период оплаты',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем поле раздела перед полем категории
        self.fields['section'] = forms.ModelChoiceField(
            queryset=CategorySection.objects.filter(is_active=True).order_by('name'),
            required=True,
            label='Раздел',
            help_text='Сначала выберите раздел, затем категорию',
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_section',
            }),
            empty_label='Выберите раздел'
        )
        
        # Если задача редактируется, устанавливаем начальное значение раздела
        if self.instance and self.instance.pk and hasattr(self.instance, 'category'):
            if self.instance.category:
                self.fields['section'].initial = self.instance.category.section_id
        
        # Фильтруем категории по разделу (если раздел выбран)
        category_field = self.fields['category']
        if isinstance(category_field, ModelChoiceField):
            # Если задача редактируется и есть категория, показываем категории её раздела
            if self.instance and self.instance.pk and hasattr(self.instance, 'category'):
                if self.instance.category:
                    category_field.queryset = Category.objects.filter(
                        section=self.instance.category.section,
                        is_active=True
                    ).select_related('section')
                else:
                    category_field.queryset = Category.objects.none()
            else:
                # При создании новой задачи проверяем, есть ли раздел в POST данных
                # Это нужно для валидации формы после отправки
                section_id = None
                if args and hasattr(args[0], 'get'):
                    section_id = args[0].get('section')
                
                if section_id:
                    try:
                        section_obj = CategorySection.objects.get(pk=section_id, is_active=True)
                        category_field.queryset = Category.objects.filter(
                            section=section_obj,
                            is_active=True
                        ).select_related('section')
                    except (CategorySection.DoesNotExist, ValueError):
                        category_field.queryset = Category.objects.none()
                else:
                    # При создании новой задачи категории не показываем до выбора раздела
                    category_field.queryset = Category.objects.none()
            
            category_field.widget.attrs.update({
                'class': 'form-select',
                'id': 'id_category',
            })
            category_field.empty_label = 'Сначала выберите раздел'
        
        # Добавляем поле региона перед полем города (только если выбран тип работы "У себя" или "У заказчика")
        # Поле региона будет показываться только когда location_type = SELF или CUSTOMER
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
        
        # Если задача редактируется и есть город, устанавливаем начальное значение региона
        if self.instance and self.instance.pk and hasattr(self.instance, 'city'):
            if self.instance.city:
                self.fields['region'].initial = self.instance.city.region_id
        
        # Фильтруем города по региону (если регион выбран)
        city_field = self.fields['city']
        if isinstance(city_field, ModelChoiceField):
            # Если задача редактируется и есть город, показываем города его региона
            if self.instance and self.instance.pk and hasattr(self.instance, 'city'):
                if self.instance.city:
                    city_field.queryset = City.objects.filter(
                        region=self.instance.city.region,
                        is_active=True
                    ).select_related('region')
                else:
                    city_field.queryset = City.objects.none()
            else:
                # При создании новой задачи проверяем, есть ли регион в POST данных
                # Это нужно для валидации формы после отправки
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
                    # При создании новой задачи города не показываем до выбора региона
                    city_field.queryset = City.objects.none()
            
            city_field.widget.attrs.update({
                'class': 'form-select',
                'id': 'id_city',
            })
            city_field.empty_label = 'Сначала выберите регион'
        
        # Делаем город необязательным
        self.fields['city'].required = False
        # Делаем стоимость необязательной
        self.fields['price'].required = False
        
        # Добавляем поле is_active только при редактировании (когда есть instance)
        if self.instance and self.instance.pk:
            self.fields['is_active'] = forms.BooleanField(
                required=False,
                initial=self.instance.is_active,
                label='Показывать задачу',
                help_text='Снимите галочку, чтобы скрыть задачу из общего списка',
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
        
        # Переупорядочиваем поля: section должен быть перед category
        field_order = list(self.fields.keys())
        if 'section' in field_order and 'category' in field_order:
            section_idx = field_order.index('section')
            category_idx = field_order.index('category')
            if section_idx > category_idx:
                field_order.remove('section')
                field_order.insert(category_idx, 'section')

    def clean_category(self):
        """Валидация категории с учетом выбранного раздела"""
        # Queryset уже обновлен в __init__() на основе POST данных
        # Просто возвращаем значение из cleaned_data
        return self.cleaned_data.get('category')
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data
        
        section = cleaned_data.get('section')
        category = cleaned_data.get('category')
        location_type = cleaned_data.get('location_type')
        region = cleaned_data.get('region')
        city = cleaned_data.get('city')

        # Проверяем, что категория принадлежит выбранному разделу
        if section and category:
            if category.section_id != section.id:
                raise forms.ValidationError({
                    'category': 'Выбранная категория не принадлежит выбранному разделу.'
                })
        
        # Если категория выбрана, но раздела нет, это ошибка
        if category and not section:
            raise forms.ValidationError({
                'section': 'Необходимо выбрать раздел перед выбором категории.'
            })

        # Проверяем, что город принадлежит выбранному региону
        if region and city:
            if city.region_id != region.id:
                raise forms.ValidationError({
                    'city': 'Выбранный город не принадлежит выбранному региону.'
                })

        # Если выбрана работа у себя или у заказчика, регион и город обязательны
        if location_type in [Task.LocationType.SELF, Task.LocationType.CUSTOMER]:
            if not region:
                raise forms.ValidationError({
                    'region': 'Укажите регион для выбранного места выполнения задачи.'
                })
            if not city:
                raise forms.ValidationError({
                    'city': 'Укажите город для выбранного места выполнения задачи.'
                })

        # Если выбрана удаленная работа, город и регион не нужны
        if location_type == Task.LocationType.REMOTE:
            cleaned_data['city'] = None
            cleaned_data['region'] = None

        return cleaned_data

    def save(self, commit=True, author=None):
        task = super().save(commit=False)
        if author:
            task.author = author
        
        # Удаляем поля section и region из cleaned_data, так как они не являются полями модели Task
        # Они используются только для фильтрации категорий и городов
        if 'section' in self.cleaned_data:
            del self.cleaned_data['section']
        if 'region' in self.cleaned_data:
            del self.cleaned_data['region']
        
        # Генерируем slug из title, если его нет
        if not task.slug:
            # Создаем базовый слаг из заголовка с транслитерацией кириллицы
            base_slug = slugify(task.title)
            slug = base_slug
            counter = 1
            # Проверяем уникальность slug
            while Task.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            task.slug = slug
        
        # Если задача редактируется и была проверена модератором (активная задача),
        # автоматически отправляем её на модерацию при любом изменении
        if task.pk:
            try:
                # Получаем исходное значение is_moderated из базы данных
                original_task = Task.objects.get(pk=task.pk)
                if original_task.is_moderated:
                    # Задача была проверена, отправляем на повторную модерацию
                    task.is_moderated = False
                # Если задача уже на модерации (is_moderated=False), оставляем как есть
            except Task.DoesNotExist:
                # Задача только создается, оставляем is_moderated как есть (False по умолчанию)
                pass

        if commit:
            task.save()
        return task


class TaskResponseForm(forms.ModelForm):
    """Форма для создания отклика на задачу"""
    class Meta:
        model = TaskResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Напишите сообщение автору задачи...'
            }),
        }
        labels = {
            'message': 'Ваше сообщение',
        }


class MessageForm(forms.ModelForm):
    """Форма для отправки сообщения в рамках отклика"""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите ваше сообщение...'
            }),
        }
        labels = {
            'content': 'Сообщение',
        }


class ReviewForm(forms.ModelForm):
    """Форма для создания отзыва"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Оставьте отзыв о работе...'
            }),
        }
        labels = {
            'rating': 'Оценка',
            'comment': 'Отзыв',
        }
        help_texts = {
            'rating': 'Оцените работу от 1 до 5',
            'comment': 'Оставьте отзыв о работе',
        }

