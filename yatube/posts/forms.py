# Импортируем модуль forms, из него возьмём класс ModelForm
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {"text": "Текст", "group": "Группа"}
        help_texts = {
            "text": "Текст нового поста",
            "group": "Группа, к которой будет относиться пост",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        localized_fields = ('text',)
