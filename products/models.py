from django.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

import requests


class Category(models.Model):
    """
    # This models the broad categories for styles of beers found
    # on the shop
    """
    class Meta:
        verbose_name_plural = 'Categories'

    name = models.CharField(max_length=260)
    friendly_name = models.CharField(max_length=260, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_friendly_name(self):
        return self.friendly_name


class Style(models.Model):
    """
    # Styles are subcategories of the main categories, and is what the user
    # will see in the product descriptions
    """
    name = models.CharField(max_length=254)
    friendly_name = models.CharField(max_length=254, null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default='other')

    def __str__(self):
        return self.name

    def get_friendly_name(self):
        return self.friendly_name


class Product(models.Model):
    """
    # The model for the products in the store
    """
    PACKAGING_TYPE = [
        ('bottle', 'bottle'),
        ('can', 'can'),
        ('keg', 'keg'),
    ]

    name = models.CharField(max_length=254)
    producer = models.ForeignKey('producers.Producer', null=True, blank=True, on_delete=models.SET_NULL)
    sku = models.CharField(max_length=254, null=True, blank=True)
    style = models.ForeignKey('Style', on_delete=models.CASCADE, default='other')
    description = models.TextField()
    abv = models.DecimalField(max_digits=6, decimal_places=2)
    packaging = models.CharField(max_length=10, choices=PACKAGING_TYPE, default='bottle')
    volume = models.CharField(max_length=10)
    units_per_order = models.IntegerField(default=24)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    rating = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    new_product = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    image = models.ImageField(upload_to='beers', null=True, blank=True)

    def __str__(self):
        return self.name

    """
    # Update to save method so that any image in the 'Image url' field
    # will be saved on the server as the image field.
    """
    def save(self, *args, **kwargs):
        if self.image_url and not self.image:
            image_url = self.image_url
            file_name = image_url.rsplit('/', 1)[-1]
            response = requests.get(image_url)

            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(response.content)
            img_temp.flush()
            self.image.save(f'{self.name}_{file_name}', File(img_temp))
        super(Product, self).save(*args, **kwargs)

    """
    # Calculate the cost of one crate of a product
    """
    @property
    def cost(self):
        return self.price * self.units_per_order
