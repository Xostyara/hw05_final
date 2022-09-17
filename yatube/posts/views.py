
from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from django.shortcuts import render, redirect
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from .utils import paginate_page
from django.views.decorators.cache import cache_page

# Create your views here.


# Главная страница
@cache_page(20)
def index(request):

    # post_list = Post.objects.all().order_by('-pub_date')
    # Если порядок сортировки определен в классе Meta модели,
    # запрос будет выглядить так:
    posts = Post.objects.select_related("group", "author")
    # вызов метода пагинации
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


# Страница с постами группы
def group_posts(request, slug):

    template = 'posts/group_list.html'
    # Функция get_object_or_404 получает по заданным критериям объект
    # из базы данных или возвращает сообщение об ошибке, если объект не найден.
    # В нашем случае в переменную group будут переданы объекты модели Group,
    # поле slug у которых соответствует значению slug в запросе
    group = get_object_or_404(Group, slug=slug)

    # Метод .filter позволяет ограничить поиск по критериям.
    # Это аналог добавления
    # условия WHERE group_id = {group_id}
    # posts = Post.objects.filter(group=group).order_by('-pub_date')[:10]
    group_posts = group.posts.all()
    page_obj = paginate_page(request, group_posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


# Профиль пользователя
def profile(request, username):

    template = 'posts/profile.html'
    user_author = get_object_or_404(User, username=username)

    # такая конструкция ниже тоже работает, но не проходит автотесты
    # user_posts = get_list_or_404(Post, author__username=username)
    # user_posts_count = user404.posts.select_related('author').count()

    user_posts = user_author.posts.all()
    page_obj = paginate_page(request, user_posts)
    following = request.user.is_authenticated and Follow.objects.filter( 
        user=request.user, 
        author=user_author 
    ).exists() 
    context = {
        'page_obj': page_obj,
        'following': following,
        'user_author': user_author,
    }
    return render(request, template, context)


# Посты пользователя
def post_detail(request, post_id):

    template = 'posts/post_detail.html'
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'group'
        ),
        pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'comments': comments,
        'post': post,
        'form': form,
    }
    return render(request, template, context)

# @login_required
# def post_create(request):
#     if request.method == 'POST':
#         form = PostForm(request.POST or None)
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.author = request.user
#             post.save()
#             return redirect('posts:profile', post.author)
#     form = PostForm()
#     return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_create(request):

    form = PostForm(
        request.POST or None,
        files=request.FILES or None)

    if not request.method == "POST":
        return render(
            request,
            "posts/create_post.html",
            {"form": form, "is_edit": False}
        )

    if not form.is_valid():
        return render(
            request,
            "posts/index.html",
            {"form": form, "is_edit": False}
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {
        "form": form,
        "post": post,
        "is_edit": True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """получаем посты в которых author связан через модель Follows
    текущим пользователем через request идем в Post, от туда через filter
     в author, далее через select_related (following) в Follow, далее user.
     Находим пользователя с заданным именем - для него ищем обьекты в
     таблицы Follow которые на него ссылаются далее для всех найденых з
     аписей в Follow ищутся связанные с ним авторы,
     а далее все посты которые связаны с автором"""
    posts_lists = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': paginate_page(request, posts_lists)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Получаем всех автров"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    """Получаем всех подписанных юзеров и отписываем их"""
    author = get_object_or_404(User, username=username)
    follow_qs = Follow.objects.filter(author=author, user=request.user)
    if follow_qs.exists():
        follow_qs.delete() 
    return redirect('posts:profile', username)
