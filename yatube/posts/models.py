from django.db import models
from django.contrib.auth import get_user_model
from .validators import validate_not_empty

# Обращение к пользовалям делается через метод в соответствии с документацией
User = get_user_model()
# Create your models here.


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        validators=[validate_not_empty],
        verbose_name='Текст',
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        blank=True,  # (Позволяет занести в поле пустое значение)
        null=True,  # (Будет хранить пустые значения)
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    def __str__(self) -> str:
        return self.text[:15]

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='post',
        help_text='Комментарий')
    name = models.CharField(max_length=80)
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Оставьте свой комментарий здесь')
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE)
    created = models.DateTimeField(
        verbose_name='Дата комментария',
        auto_now_add=True)

    class Meta:
        ordering = ('created',)
        verbose_name_plural = 'Коментарии'
        verbose_name = 'Коментарий'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        # удобое читаемое имя в множественнои и единственном числе
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
