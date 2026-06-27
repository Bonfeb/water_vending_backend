from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from django.db import transaction
from decimal import Decimal
import requests
import base64
from datetime import datetime

from payments.models import *
from payments.serializers import *
from orders.models import *
from core.notifications import *
from core.permissions import *
from users.models import *


class InitiateSTKPushView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = STKPushSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, pk=serializer.validated_data['order_id'], user=request.user)
        phone = serializer.validated_data['phone_number']

        if order.status != 'pending':
            return Response({'error': 'Order already processed'}, status=status.HTTP_400_BAD_REQUEST)

        # Create payment record
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                'phone_number': phone,
                'amount': order.total_amount
            }
        )

        stk_response = self._initiate_stk_push(phone, order.total_amount, order.id)

        MPesaTransactionLog.objects.create(
            transaction_type='STK_PUSH_REQUEST',
            request_data={'phone': phone, 'amount': str(order.total_amount), 'order_id': order.id},
            response_data=stk_response
        )

        if stk_response.get('success'):
            payment.checkout_request_id = stk_response.get('checkout_request_id')
            payment.merchant_request_id = stk_response.get('merchant_request_id')
            payment.save()

            return Response({
                'message': 'Payment request sent to your phone',
                'checkout_request_id': stk_response.get('checkout_request_id')
            })

        payment.status = 'failed'
        payment.result_description = stk_response.get('error', 'Unknown error')
        payment.save()

        return Response({
            'error': 'Failed to initiate payment',
            'details': stk_response
        }, status=status.HTTP_400_BAD_REQUEST)

    def _initiate_stk_push(self, phone, amount, order_id):
        CONSUMER_KEY = 'your_consumer_key'
        CONSUMER_SECRET = 'your_consumer_secret'
        SHORTCODE = '174379'
        PASSKEY = 'your_passkey'
        CALLBACK_URL = 'https://yourdomain.com/api/payments/callback/'

        try:
            auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            auth = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            response = requests.get(auth_url, headers=headers, timeout=30)
            access_token = response.json().get('access_token')

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f"{SHORTCODE}{PASSKEY}{timestamp}".encode()).decode()

            phone = str(phone)
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif phone.startswith('+'):
                phone = phone[1:]

            stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': SHORTCODE,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(float(amount)),
                'PartyA': phone,
                'PartyB': SHORTCODE,
                'PhoneNumber': phone,
                'CallBackURL': CALLBACK_URL,
                'AccountReference': f'WATER-{order_id}',
                'TransactionDesc': f'Water Order #{order_id}'
            }

            response = requests.post(stk_url, json=payload, headers=headers, timeout=30)
            result = response.json()

            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'message': result.get('CustomerMessage', 'Request accepted')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errorMessage', 'Unknown error')
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

class MPesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            data = request.data
            body = data.get('Body', {}).get('stkCallback', {})

            result_code = body.get('ResultCode')
            checkout_request_id = body.get('CheckoutRequestID')

            MPesaTransactionLog.objects.create(
                transaction_type='STK_PUSH_CALLBACK',
                request_data={},
                response_data=data
            )

            if result_code == 0:
                metadata = body.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = None
                phone_number = None
                amount = None

                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_number = item.get('Value')
                    elif item.get('Name') == 'Amount':
                        amount = item.get('Value')

                payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()

                if payment:
                    payment.status = 'success'
                    payment.mpesa_receipt = receipt_number
                    payment.save()

                    order = payment.order
                    order.status = 'paid'
                    order.mpesa_receipt = receipt_number
                    order.save()

                    notify_admin('New Paid Order', f'Order #{order.id} paid. Receipt: {receipt_number}')

            else:
                payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
                if payment:
                    payment.status = 'failed'
                    payment.result_description = body.get('ResultDesc', 'Payment failed')
                    payment.save()

            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        except Exception as e:
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

class PaymentStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        try:
            payment = order.payment
            return Response({
                'order_id': order.id,
                'status': payment.status,
                'amount': str(payment.amount),
                'mpesa_receipt': payment.mpesa_receipt,
                'created_at': payment.created_at
            })
        except Payment.DoesNotExist:
            return Response({'error': 'No payment found'}, status=status.HTTP_404_NOT_FOUND)
        
class AdminPaymentListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        payments = Payment.objects.select_related('order', 'order__user').order_by('-created_at')

        # Optional filters
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')

        if status_filter:
            payments = payments.filter(status=status_filter)

        if search:
            payments = payments.filter(
                Q(mpesa_receipt__icontains=search) |
                Q(order__user__phone_number__icontains=search) |
                Q(order__user__first_name__icontains=search) |
                Q(order__user__last_name__icontains=search) |
                Q(order__guest_phone__icontains=search) |
                Q(order__guest_name__icontains=search)
            )

        total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
        completed_amount = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        pending_amount = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
        failed_amount = payments.filter(status='failed').aggregate(total=Sum('amount'))['total'] or 0

        serializer = PaymentSerializer(payments, many=True)

        return Response({
            'count': payments.count(),
            'total_amount': str(total_amount),
            'completed_amount': str(completed_amount),
            'pending_amount': str(pending_amount),
            'failed_amount': str(failed_amount),
            'results': serializer.data
        })