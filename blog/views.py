#from django.shortcuts import render
from .models import Post 
from django.views.generic import ListView, DetailView

class PostList(ListView):
    model = Post
    template_name='blog/index.html'
    ordering='-pk'

class PostDetail(DetailView):
    model = Post
    template_name='blog/single_post_page.html'