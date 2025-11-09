from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название региона")
    slug = models.SlugField(unique=True, verbose_name="URL")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ['name']

    def __str__(self) -> str:
        return str(self.name)
        

class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название города")
    region = models.ForeignKey(
        Region, 
        on_delete=models.CASCADE, 
        related_name='cities',
        verbose_name="Регион"
    )
    slug = models.SlugField(verbose_name="URL")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='unique_city_slug_per_region'
            )
        ]

    def __str__(self) -> str:
        return f"{str(self.name)} ({str(self.region.name)})"

    def get_full_name(self):
        return f"{self.name}, {self.region.name}"