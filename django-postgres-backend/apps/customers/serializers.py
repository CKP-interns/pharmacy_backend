from rest_framework import serializers
from .models import Customer

<<<<<<< HEAD

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
=======
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('id',)
>>>>>>> b2b2647 (created customers)
