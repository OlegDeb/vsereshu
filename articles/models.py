from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Category(models.Model):
	name = models.CharField("Категория", max_length=200, unique=True)
	slug = models.SlugField(max_length=250, unique=True, verbose_name='Url')

	class Meta:
		verbose_name = "Категория(ю)"
		verbose_name_plural = "Категории"

	def __str__(self):
		return self.name


class Article(models.Model):
	title = models.CharField("Заголовок", max_length=220)
	description = models.CharField("Текст для сео", max_length=250)
	create_at = models.DateTimeField(auto_now_add=True)
	category = models.ForeignKey(
		Category,
		verbose_name="Категория",
		on_delete=models.SET_NULL,
		null=True
	)
	image = models.ImageField("Картинка для статьи", upload_to='articles/')
	text = models.TextField("Текст")
	public = models.BooleanField(verbose_name='Публиковать на сайте', default=True)
	sidebar = models.BooleanField(verbose_name='Популярная статья', default=False)
	slug = models.SlugField("url", max_length=250, unique=True)
	views = models.PositiveIntegerField(verbose_name='Просмотры', default=0)

	image_mini = ImageSpecField(source='image', processors=[ResizeToFill(65, 65)], format='JPEG', options={'quality': 80})
	image_list = ImageSpecField(source='image', processors=[ResizeToFill(400, 200)], format='JPEG', options={'quality': 80})
	image_post = ImageSpecField(source='image', processors=[ResizeToFill(800, 400)], format='JPEG', options={'quality': 80})

	def __str__(self):
		return self.title

	class Meta:
		verbose_name = 'Статья(ю)'
		verbose_name_plural = 'Статьи'
		ordering = ['-id']