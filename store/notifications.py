from catalog.models import Product, ProductImage
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
get_from_email = settings.EMAIL_HOST_USER
base_url = settings.BASE_URL
business_name = settings.BUSINESS_NAME
business_logo = settings.BUSINESS_LOGO
contact_email = settings.CONTACT_EMAIL
from_email = business_name + "<" + get_from_email + ">"

def get_recommended_products(base_url):
    """Retrieve and format 4 random products for recommendation."""
    recommended_products = Product.objects.filter(status="Publish").order_by('?')[:4]
    formatted_products = []
    for product in recommended_products:
        first_image = ProductImage.objects.filter(product=product).first()
        image_url = first_image.image.url if first_image else None
        formatted_product  = {
            'image_url': image_url,
            'name': product.name,
            'price': product.price,
            'link': f"{base_url}{reverse('store:product_details', args=[product.product_id])}"
        }
        formatted_products.append(formatted_product)
        
    return formatted_products



def notify_buyer_on_order(instance):
    base_url = base_url.rstrip('/')
    status = instance.status
    order_reference = instance.order_reference
    tracking_link = f"{base_url}{reverse('store:track_order', args=[order_reference])}"
    user_name = instance.user.username
    title = f"Your Order with tracking code {order_reference} - {status}!"
    # Get formatted recommended products
    recommended_products = get_recommended_products(base_url)
    context = {
        'business_name': business_name,
        'contact_email': contact_email,
        'user_name': user_name,
        'status': status,
        'order_reference': order_reference,
        'tracking_link': tracking_link,
        'title': title,
        'business_logo': business_logo,
        'base_url': base_url,
        'recommended_products': recommended_products,
    }

    # Render the HTML email content
    html_message = render_to_string("email_templates/order_notification.html", context)
    details = (
        f"Thank you for shopping with us! We’re excited to let you know that your order {order_reference}"
        f"has been successfully received and the status is '{status}'. You can view the latest details and track your order here: {tracking_link}\n\n"
    )

    to_email = instance.user.email
    print(to_email)

    send_mail(
        title,
        details,
        from_email,
        [to_email],
        fail_silently=False,
        html_message=html_message,
    )


def notify_admin_on_order(instance):
    status = instance.status
    order_reference = instance.order_reference
    user_name = instance.user.username
    title = f"{user_name} just placed an order with tracking code {order_reference} - {status}!"

    details = (
        f"just placed an order on {business_name}, the reference code for the order is {order_reference} "
        f"Login to the admin section to manage process the order.\n\n"
    )

    send_mail(
        title,
        details,
        from_email,
        [contact_email],
        fail_silently=False,
    )