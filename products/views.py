from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Product, Category, Style
from .forms import ProductForm
from .untappd_handler import UntappdHandler
from .search import get_query


def all_products(request):
    """
    # This view displays products and the logic to sort and order them.
    """
    products = Product.objects.filter(in_stock=True).order_by('name')
    query_string = None
    category = None
    style = None
    sort = None
    direction = None
    packaging = None

    if request.GET:

        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))

            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products = products.order_by(sortkey)

        if 'category' in request.GET:
            category = request.GET['category']
            products = products.filter(style__category__name=category)
            category = Category.objects.get(name=category)

        if 'style' in request.GET:
            style = request.GET['style']
            products = products.filter(style__name=style)
            style = Style.objects.get(name=style)

        if 'packaging' in request.GET:
            packaging = request.GET['packaging']
            if packaging == 'keg':
                products = products.filter(packaging='keg')
            elif packaging == 'bottle_can':
                products = products.exclude(packaging='keg')
            else:
                packaging = None

        if 'q' in request.GET:
            query_string = request.GET['q']

            if not query_string:
                messages.error(request, "No search criteria entered.")
                return redirect(reverse('products'))

            entry_query = get_query(query_string, [
                'name',
                'description',
                'style__friendly_name',
                'producer__name'])

            products = products.filter(entry_query)

    current_sorting = f'{sort}_{direction}'

    # Handle pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)

    try:
        product_page = paginator.page(page)
    except PageNotAnInteger:
        product_page = paginator.page(1)
    except EmptyPage:
        product_page = paginator.page(paginator.num_pages)

    context = {
        'products': product_page,
        'search_term': query_string,
        'category': category,
        'style': style,
        'current_sorting': current_sorting,
        'packaging': packaging,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """
    # This view displays the details of a specific product
    """
    product = get_object_or_404(Product, pk=product_id)
    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)


@login_required
def add_product(request):
    """
    # Handles adding a new product to the database manually or
    # by searching for it on untappd
    """
    if not request.user.is_superuser:
        # If user is not an admin, redirect to home page
        messages.error(request, "Only store owners can access this page.")
        return redirect(reverse('home'))

    if request.POST:
        if 'product_search' in request.POST:
            # If product search on untappd form has been submitted
            search_query = request.POST['product_search']
            results = UntappdHandler.search_beer(search_query)

            if type(results) == str:
                # If UntappdHandler returns a string, this means there was an error
                messages.error(request, f'Error from Untappd:{results}')
                return redirect(reverse('add_product'))

            else:
                form = ProductForm
                context = {
                    'search': True,
                    'form': form,
                    'untappd_results': results
                }

        elif 'beer_id' in request.POST:
            # If product search result has been selected
            beer_id = request.POST['beer_id']
            beer_info = UntappdHandler.get_beer_info(beer_id)

            if type(beer_info) == str:
                # If UntappdHandler returns a string, this means there was an error
                messages.error(request, beer_info)
            else:
                if beer_info['beer_label_hd']:
                    image_url = beer_info['beer_label_hd']
                else:
                    image_url = beer_info['beer_label']

                form = ProductForm(initial={
                    'name': beer_info['beer_name'],
                    'producer': beer_info['brewery']['brewery_name'],
                    'description': beer_info['beer_description'],
                    'image_url': image_url,
                    'abv': round(beer_info['beer_abv'], 2),
                    'rating': round(beer_info['rating_score'], 2)
                })
                context = {
                    'form': form,
                    'image_url': image_url,
                }

        else:
            """
            # Form submission to add a new product
            """
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save()
                messages.success(request, "New product added!")
                return redirect(reverse('product_detail', args=[product.id]))
            else:
                messages.error(request, "An error occurred while updating your profile. Please ensure the form is valid.")

                context = {
                    'form': form,
                }

    else:
        form = ProductForm
        context = {
            'form': form,
        }

    template = 'products/add_product.html'

    return render(request, template, context)


@login_required
def edit_product(request, product_id):
    """
    # Edits a product in the store
    """
    if not request.user.is_superuser:
        # If user is not an admin, redirect to home page
        messages.error(request, "Only store owners can access this page.")
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully updated the product.')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(request, 'There was an error updating the product. Please ensure the form is valid.')

    else:
        form = ProductForm(instance=product)
        messages.info(request, f'You are editing "{product.name}"".')
    context = {
            'form': form,
            'product': product,
        }
    template = 'products/edit_product.html'

    return render(request, template, context)


@login_required
def delete_product(request, product_id):
    """
    # Delete a product from the store
    """
    if not request.user.is_superuser:
        # If user is not an admin, redirect to home page
        messages.error(request, "Only store owners can access this page.")
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Successfully removed product from the shop.')
    return redirect(reverse('products'))


@login_required
def manage_products(request):
    """
    # Manage products in the store
    """
    if not request.user.is_superuser:
        # If user is not an admin, redirect to home page
        messages.error(request, "Only store owners can access this page.")
        return redirect(reverse('home'))

    query = None

    products = Product.objects.all().order_by('producer', 'name')

    if request.GET:
        # If a product has been searched for
        if 'q' in request.GET:
            query_string = request.GET['q']
            if not query_string:
                messages.error(request, "No search criteria entered.")
                return redirect(reverse('manage_products'))

            entry_query = get_query(query_string, [
                'name',
                'description',
                'style__friendly_name',
                'producer__name'])

            products = products.filter(entry_query)

    context = {
        'products': products,
        'search_term': query,
    }

    return render(request, 'products/manage_products.html', context)
