import datetime

import webcolors
from rest_framework import serializers

from .models import Achievement, AchievementCat, Cat, Owner, CHOICES

'''
class Hex2NameColor(serializers.Field):
    # При чтении данных ничего не меняем - просто возвращаем как есть:
    def to_representation(self, value):
        return value

    # При записи код цвета конвертируется в его название:
    def to_internal_value(self, data):
        try:
            # Если имя цвета существует, то конвертируем код в название:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для такого цвета нет имени.')
        return data
'''


class AchievementSerializer(serializers.ModelSerializer):
    # Переопределение поля для его переименования:
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatListSerializer(serializers.ModelSerializer):
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')


class CatSerializer(serializers.ModelSerializer):
    # Переопределение типа поля на другой (вложенный) сериализатор: 
    achievements = AchievementSerializer(many=True, required=False)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'owner', 'achievements',
                  'age')

    def get_age(self, obj):
        return datetime.datetime.now().year - obj.birth_year

    # Чтобы настроить сохранение данных, нужно переопределить метод create()
    # в сериализаторе:
    def create(self, validated_data):
        # Если в исходном запросе не было поля achievements
        if 'achievements' not in self.initial_data:
            # То создаём запись о котике без его достижений
            cat = Cat.objects.create(**validated_data)
            return cat
        # Уберём список достижений из словаря validated_data и сохраним его:
        achievements = validated_data.pop('achievements')
        # Создадим нового котика пока без достижений, данных нам достаточно:
        cat = Cat.objects.create(**validated_data) 
        # Для каждого достижения из списка достижений:
        for achievement in achievements:
            # Создадим новую запись или получим существующий экземпляр из БД:
            current_achievement, status = Achievement.objects.get_or_create(
                **achievement)
            # Поместим ссылку на каждое достижение во вспомогательную таблицу
            # Не забыв указать к какому котику оно относится
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat
            )
        return cat


class OwnerSerializer(serializers.ModelSerializer):
    # Переопределение типа поля связанной модели с дефолтного
    # PrimaryKeyRelatedField на StringRelatedField:
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'cats')

