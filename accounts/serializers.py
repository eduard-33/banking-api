from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BankAccount, Transaction

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user



class BankAccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BankAccount
        fields = ['id', 'username', 'balance', 'created_at']
        read_only_fields = ['balance', 'created_at']



class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type','amount', 'description', 'created_at']
        read_only_fields = ['id', 'transaction_type', 'created_at']



class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)



class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)



class TransferSerializer(serializers.Serializer):
    recipient_username = serializers.CharField(max_length=150)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)

     
