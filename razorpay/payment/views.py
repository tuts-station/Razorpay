from django.shortcuts import render
from .forms import OrderForm
import razorpay
from .models import Order
from django.conf import settings

def payment(request):
    if request.method == "POST":
        name = request.POST.get('name')
        amount = int(request.POST.get('amount')) * 100

        # create Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # create order
        response_payment = client.order.create(dict(amount=amount,
                                                    currency='INR')
                                               )

        order_id = response_payment['id']
        order_status = response_payment['status']

        if order_status == 'created':
            order = Order(
                name=name,
                amount=amount,
                order_id=order_id,
            )
            order.save()
            response_payment['name'] = name

            form = OrderForm(request.POST or None)
            return render(request, 'payment.html', {'form': form, 'payment': response_payment})

    form = OrderForm()
    return render(request, 'payment.html', {'form': form})


def payment_status(request):
    response = request.POST
    params_dict = {
        'razorpay_order_id': response['razorpay_order_id'],
        'razorpay_payment_id': response['razorpay_payment_id'],
        'razorpay_signature': response['razorpay_signature']
    }

    # client instance
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        status = client.utility.verify_payment_signature(params_dict)
        order = Order.objects.get(order_id=response['razorpay_order_id'])
        order.razorpay_payment_id = response['razorpay_payment_id']
        order.paid = True
        order.save()
        return render(request, 'callback.html', {'status': True})
    except:
        return render(request, 'callback.html', {'status': False})