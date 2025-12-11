# accounts/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2')
        read_only_fields = ('id',)

    def validate(self, attrs):
        pw = attrs.get('password')
        pw2 = attrs.get('password2')

        if pw != pw2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        email = attrs.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        if hasattr(user, 'role'):
            user.role = 'citizen'
            user.save(update_fields=['role'])

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'role')
        read_only_fields = ('id', 'date_joined')


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin-created users. Accepts 'password' and uses set_password.
    Admin can set role; optionally set is_staff if role == 'admin'.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'password')
        read_only_fields = ('id',)

    def validate_email(self, value):
        if self.instance:
            qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Another user with this email already exists.")
        else:
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        pwd = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(pwd)
        if getattr(user, 'role', None) == 'admin':
            user.is_staff = True
        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if pwd:
            instance.set_password(pwd)
        if getattr(instance, 'role', None) == 'admin':
            instance.is_staff = True
        instance.save()
        return instance




