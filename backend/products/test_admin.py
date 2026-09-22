from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from products.models import Category, Product


class ProductAdminTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_superuser(
            username='admin_staff',
            email='admin@example.com',
            password='Password123!',
        )
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='user@example.com',
            password='Password123!',
        )
        self.category_decor = Category.objects.create(name='Decor', slug='decor')
        self.category_pots = Category.objects.create(name='Pots', slug='pots')

        # Create products across stock statuses
        self.prod_in_stock = Product.objects.create(
            name='Terracotta Vase',
            slug='terracotta-vase',
            description='Handmade terracotta vase',
            price=Decimal('599.00'),
            stock=20,
            category=self.category_decor,
            is_available=True,
            is_new=False,
        )
        self.prod_low_stock = Product.objects.create(
            name='Peacock Diya',
            slug='peacock-diya',
            description='Peacock motif diya',
            price=Decimal('299.00'),
            stock=3,
            category=self.category_decor,
            is_available=True,
            is_new=True,
        )
        self.prod_out_of_stock = Product.objects.create(
            name='Clay Planter',
            slug='clay-planter',
            description='Large outdoor planter',
            price=Decimal('1200.00'),
            stock=0,
            category=self.category_pots,
            is_available=False,
            is_new=False,
        )

        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self):
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_regular_user_cannot_access_product_admin(self):
        self.client.login(username='regular_user', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access_changelist(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terracotta Vase')
        self.assertContains(response, 'Peacock Diya')
        self.assertContains(response, 'Clay Planter')

    def test_kpi_summary_bar_renders(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'product-admin-kpi-bar')
        self.assertContains(response, '3</strong> Products')
        self.assertContains(response, '2</strong> Active')
        self.assertContains(response, '1</strong> Low Stock')
        self.assertContains(response, '1</strong> Out of Stock')

    def test_stock_badges_rendered_correctly(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'badge-in-stock')
        self.assertContains(response, 'badge-low-stock')
        self.assertContains(response, 'badge-out-of-stock')

    def test_thumbnail_placeholder_when_no_image(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'product-thumb-placeholder')

    def test_thumbnail_renders_with_image(self):
        # Attach a dummy image to prod_in_stock
        dummy_image = SimpleUploadedFile("pottery.jpg", b"file_content", content_type="image/jpeg")
        self.prod_in_stock.image = dummy_image
        self.prod_in_stock.save()

        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'product-thumb-img')
        self.assertContains(response, 'product-thumb-zoom')

    def test_stock_status_filter_in_stock(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + '?stock_status=in_stock'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terracotta Vase')
        self.assertNotContains(response, 'Peacock Diya')
        self.assertNotContains(response, 'Clay Planter')

    def test_stock_status_filter_low_stock(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + '?stock_status=low_stock'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Peacock Diya')
        self.assertNotContains(response, 'Terracotta Vase')
        self.assertNotContains(response, 'Clay Planter')

    def test_stock_status_filter_out_of_stock(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + '?stock_status=out_of_stock'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clay Planter')
        self.assertNotContains(response, 'Terracotta Vase')
        self.assertNotContains(response, 'Peacock Diya')

    def test_search_by_name(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + '?q=Peacock'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Peacock Diya')
        self.assertNotContains(response, 'Terracotta Vase')

    def test_search_by_id(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + f'?q={self.prod_in_stock.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terracotta Vase')
        self.assertNotContains(response, 'Peacock Diya')

    def test_search_by_category_name(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist') + '?q=Pots'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clay Planter')
        self.assertNotContains(response, 'Terracotta Vase')

    def test_bulk_actions(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')

        # Test mark_unavailable
        post_data = {
            'action': 'mark_unavailable',
            '_selected_action': [self.prod_in_stock.id, self.prod_low_stock.id],
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.prod_in_stock.refresh_from_db()
        self.prod_low_stock.refresh_from_db()
        self.assertFalse(self.prod_in_stock.is_available)
        self.assertFalse(self.prod_low_stock.is_available)

        # Test mark_available
        post_data = {
            'action': 'mark_available',
            '_selected_action': [self.prod_in_stock.id],
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.prod_in_stock.refresh_from_db()
        self.assertTrue(self.prod_in_stock.is_available)

        # Test mark_as_new
        post_data = {
            'action': 'mark_as_new',
            '_selected_action': [self.prod_in_stock.id],
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.prod_in_stock.refresh_from_db()
        self.assertTrue(self.prod_in_stock.is_new)

        # Test remove_new_status
        post_data = {
            'action': 'remove_new_status',
            '_selected_action': [self.prod_in_stock.id, self.prod_low_stock.id],
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.prod_in_stock.refresh_from_db()
        self.prod_low_stock.refresh_from_db()
        self.assertFalse(self.prod_in_stock.is_new)
        self.assertFalse(self.prod_low_stock.is_new)

    def test_native_list_editable_bulk_save(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')

        # First GET changelist to parse form management data
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cl = response.context['cl']
        formset = response.context['cl'].formset

        post_data = {
            'form-TOTAL_FORMS': formset.management_form['TOTAL_FORMS'].value(),
            'form-INITIAL_FORMS': formset.management_form['INITIAL_FORMS'].value(),
            'form-MIN_NUM_FORMS': formset.management_form['MIN_NUM_FORMS'].value(),
            'form-MAX_NUM_FORMS': formset.management_form['MAX_NUM_FORMS'].value(),
            '_save': 'Save',
        }

        # Populate formset rows with modifications
        for i, form in enumerate(formset.forms):
            instance = form.instance
            prefix = f'form-{i}-'
            post_data[f'{prefix}id'] = instance.pk
            post_data[f'{prefix}category'] = instance.category_id or ''

            if instance.pk == self.prod_in_stock.pk:
                # Modify stock 20 -> 15 and price 599 -> 649
                post_data[f'{prefix}name'] = 'Terracotta Royal Vase'
                post_data[f'{prefix}price'] = '649.00'
                post_data[f'{prefix}stock'] = '15'
                post_data[f'{prefix}is_available'] = 'on'
            elif instance.pk == self.prod_low_stock.pk:
                # Modify stock 3 -> 0 (now out of stock)
                post_data[f'{prefix}name'] = instance.name
                post_data[f'{prefix}price'] = str(instance.price)
                post_data[f'{prefix}stock'] = '0'
                post_data[f'{prefix}is_new'] = 'on'
                post_data[f'{prefix}is_available'] = 'on'
            else:
                post_data[f'{prefix}name'] = instance.name
                post_data[f'{prefix}price'] = str(instance.price)
                post_data[f'{prefix}stock'] = str(instance.stock)
                if instance.is_available:
                    post_data[f'{prefix}is_available'] = 'on'
                if instance.is_new:
                    post_data[f'{prefix}is_new'] = 'on'

        post_response = self.client.post(url, post_data, follow=True)
        self.assertEqual(post_response.status_code, 200)

        self.prod_in_stock.refresh_from_db()
        self.prod_low_stock.refresh_from_db()

        self.assertEqual(self.prod_in_stock.name, 'Terracotta Royal Vase')
        self.assertEqual(self.prod_in_stock.price, Decimal('649.00'))
        self.assertEqual(self.prod_in_stock.stock, 15)

        self.assertEqual(self.prod_low_stock.stock, 0)
        self.assertTrue(self.prod_low_stock.is_new)

    def test_product_change_form_renders_fieldsets_and_widgets(self):
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_change', args=[self.prod_in_stock.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Basic Information')
        self.assertContains(response, 'Pricing &amp; Inventory')
        self.assertContains(response, 'Product Media')
        self.assertContains(response, 'Display Settings')
        self.assertContains(response, 'id_image_position')
        self.assertContains(response, 'id_image_zoom')
        # Check focal point and product admin media assets are loaded
        self.assertContains(response, 'admin/js/focal_point_picker.js')
        self.assertContains(response, 'admin/js/product_admin.js')
        self.assertContains(response, 'admin/css/focal_point_picker.css')
        self.assertContains(response, 'admin/css/product_admin.css')

    def test_focal_point_picker_dom_compatibility_with_image(self):
        # Attach image to product and verify expected DOM structure
        dummy_image = SimpleUploadedFile("pottery_edit.jpg", b"image_bytes", content_type="image/jpeg")
        self.prod_in_stock.image = dummy_image
        self.prod_in_stock.save()

        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_change', args=[self.prod_in_stock.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # focal_point_picker.js expects imageFieldContainer (.field-image) with an <a> tag
        content = response.content.decode('utf-8')
        self.assertIn('field-image', content)
        self.assertIn('admin-media-preview-card', content)
        self.assertIn('admin-preview-anchor', content)
        self.assertIn(self.prod_in_stock.image.url, content)
        self.assertIn('id="id_image"', content)
        self.assertIn('id="id_image_position"', content)
        self.assertIn('id="id_image_zoom"', content)

    def test_list_editable_validation_error_handling(self):
        # Submitting an invalid value (e.g. empty name or invalid price)
        self.client.login(username='admin_staff', password='Password123!')
        url = reverse('admin:products_product_changelist')

        response = self.client.get(url)
        formset = response.context['cl'].formset

        post_data = {
            'form-TOTAL_FORMS': formset.management_form['TOTAL_FORMS'].value(),
            'form-INITIAL_FORMS': formset.management_form['INITIAL_FORMS'].value(),
            'form-MIN_NUM_FORMS': formset.management_form['MIN_NUM_FORMS'].value(),
            'form-MAX_NUM_FORMS': formset.management_form['MAX_NUM_FORMS'].value(),
            '_save': 'Save',
        }

        for i, form in enumerate(formset.forms):
            instance = form.instance
            prefix = f'form-{i}-'
            post_data[f'{prefix}id'] = instance.pk
            post_data[f'{prefix}category'] = instance.category_id or ''
            if instance.pk == self.prod_in_stock.pk:
                # Submit empty name (violates blank=False)
                post_data[f'{prefix}name'] = ''
                post_data[f'{prefix}price'] = '100.00'
                post_data[f'{prefix}stock'] = '10'
            else:
                post_data[f'{prefix}name'] = instance.name
                post_data[f'{prefix}price'] = str(instance.price)
                post_data[f'{prefix}stock'] = str(instance.stock)

        post_response = self.client.post(url, post_data)
        # Form error renders 200 with errorlist
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'errorlist')
        self.prod_in_stock.refresh_from_db()
        # Original name should NOT be overwritten by empty string
        self.assertEqual(self.prod_in_stock.name, 'Terracotta Vase')

    def test_customer_facing_products_api_regression(self):
        # Ensure customer-facing API continues to function identically (only returns available products)
        api_response = self.client.get('/api/products/')
        self.assertEqual(api_response.status_code, 200)
        data = api_response.json()
        # prod_out_of_stock is is_available=False, so 2 available products returned
        self.assertEqual(len(data), 2)
        product_names = [p['name'] for p in data]
        self.assertIn('Terracotta Vase', product_names)
        self.assertIn('Peacock Diya', product_names)
        self.assertNotIn('Clay Planter', product_names)

