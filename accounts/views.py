# accounts/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.db import transaction
from .models import BankAccount, Transaction
from drf_spectacular.utils import extend_schema
from .serializers import (
    UserSerializer, BankAccountSerializer, TransactionSerializer,
    DepositSerializer, WithdrawSerializer, TransferSerializer
)

@extend_schema(tags=['Authentication'], description='Register a new user and create a bank account')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        BankAccount.objects.create(user=user) 

@extend_schema(tags=['Account'], description='Get current user bank account details')
class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    # We override this to return the current user's bank account
    def get_object(self):
        return self.request.user.bank_account

@extend_schema(tags=['Transactions'], request=DepositSerializer, description='Deposit money into your account')
class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount'] 
        account = request.user.bank_account

        account.balance += amount
        account.save()

        Transaction.objects.create( 
            account=account,
            transaction_type='DEPOSIT',
            amount=amount,
            description='Deposit to account'
        )

        return Response({
            'message': 'Deposit successful',
            'new_balance': str(account.balance)
        })

@extend_schema(tags=['Transactions'], request=WithdrawSerializer, description='Withdraw money from your account')
class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount'] 
        account = request.user.bank_account

        if account.balance < amount:
            return Response(
                {'error': 'insufficient funds'},
                status=status.HTTP_400_BAD_REQUEST
            )

        account.balance -= amount
        account.save()

        Transaction.objects.create( 
            account=account,
            transaction_type='WITHDRAWAL',
            amount=amount,
            description='Withdrawal from account'
        )

        return Response({
            'message': 'Withdrawal successful',
            'new_balance': str(account.balance)
        })

@extend_schema(tags=['Transactions'], request=TransferSerializer, description='Transfer money to another user')
class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount'] 
        recipient_username = serializer.validated_data['recipient_username'] 

        sender_account = request.user.bank_account

        if sender_account.user.username == recipient_username:
            return Response(
                {'error': 'Cannot transfer to yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist: 
            return Response(
                {'error': 'Recipient not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if sender_account.balance < amount:
            return Response(
                {'error': 'Insufficient funds'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipient_account = recipient.bank_account

        with transaction.atomic(): 
            sender_account.balance -= amount
            sender_account.save()

            recipient_account.balance += amount
            recipient_account.save()

            Transaction.objects.create( 
                account=sender_account,
                transaction_type='TRANSFER_OUT',
                amount=amount,
                description=f'Transfer to {recipient_username}'
            )

            Transaction.objects.create( 
                account=recipient_account,
                transaction_type='TRANSFER_IN',
                amount=amount,
                description=f'Transfer from {request.user.username}'
            )

        return Response({
            'message': 'Transfer successful',
            'new_balance': str(sender_account.balance)
        })

@extend_schema(tags=['Transactions'], description='View your transaction history')
class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter( 
            account=self.request.user.bank_account
        ).order_by('-created_at')
