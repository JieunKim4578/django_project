from django.test import TestCase, Client
from bs4 import BeautifulSoup
from .models import Post, Category, Tag
from django.contrib.auth.models import User


# Create your tests here.
class TestView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_jieun = User.objects.create_user(username='jieun', password='jieunjieun')
        self.user_hani = User.objects.create_user(username='hani', password='hanihani')
        self.user_hani.is_staff=True
        self.user_hani.save()
        self.category_midsize = Category.objects.create(name='midsize', slug='midsize')
        self.category_semi = Category.objects.create(name='semi', slug='semi')

        self.tag_grandeur = Tag.objects.create(name='Grandeur', slug='Grandeur')
        self.tag_spark = Tag.objects.create(name='spark', slug='spark')
        self.tag_ionic = Tag.objects.create(name='ionic', slug='ionic')

        self.post_001 = Post.objects.create(
            title = '첫 번째 포스트입니다.', 
            content = 'Hello World. We are the world.',
            category = self.category_midsize,
            author = self.user_jieun, 
            
        )
        self.post_001.tags.add(self.tag_grandeur)

        self.post_002 = Post.objects.create(
            title = '두 번째 포스트입니다.',
            content = '1등이 전부는 아니잖아요?',
            category = self.category_semi, 
            author = self.user_hani, 
        )       

        self.post_003 = Post.objects.create(
            title = '세 번째 포스트입니다.',
            content = 'Hello World. We are the world.',
            author = self.user_jieun, 
        )
        self.post_003.tags.add(self.tag_ionic)
        self.post_003.tags.add(self.tag_spark)


    def test_update_post(self):
        self.post_003 = Post.objects.create(
            title='세번째 포스트입니다.',
            content='category가 없을 수도 있죠',
            author=self.user_jieun
        )

        update_post_url = f'/blog/update_post/{self.post_003.pk}/'
        # 로그인 하지 않은 경우
        response = self.client.get(update_post_url)
        self.assertNotEqual(response.status_code, 200)

        # 로그인은 했지만, 작성자가 아닌 경우
        self.assertNotEqual(self.post_003.author, self.user_hani)
        self.client.login(
            username=self.user_hani.username,
            password='hanihani'
        )
        response = self.client.get(update_post_url)
        self.assertEqual(response.status_code, 403)

        # 작성자(jieun)가 접근하는 경우
        self.client.login(
            username=self.post_003.author.username,
            password='jieunjieun'
        )
        response = self.client.get(update_post_url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual('Edit Post - Blog', soup.title.text)
        main_area = soup.find('div', id='main_area')
        self.assertIn('Edit Post', main_area.text)

        response = self.client.post(
            update_post_url,
            {
                'title': '세번째 포스트를 수정했습니다. ',
                'content': '안녕 세계? 우리는 하나!',
            },
            follow=True
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        main_area = soup.find('div', id='main_area')
        self.assertIn('세번째 포스트를 수정했습니다.', main_area.text)
        self.assertIn('안녕 세계? 우리는 하나!', main_area.text)


    def test_create_post(self):
        # 로그인을 하지 않으면 status_code 가 200이면 안 된다. 
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 200)

        # staff 가 아닌 jieun 이 로그인을 한다. 
        self.client.login(username='jieun', password='jieunjieun')
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 200)

        # staff인 hani로 로그인을 한다
        self.client.login(username='hani', password='hanihani')
        response = self.client.get('/blog/create_post/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual('Create Post - Blog', soup.title.text)
        main_area = soup.find('div', id='main_area')
        self.assertIn('Create New Post', main_area.text)

        self.client.post(
            '/blog/create_post/',
            {
                'title' : 'Post Form 만들기',
                'content' : "Post Form 페이지를 만듭시다.",
            }
        )
        last_post = Post.objects.last()
        self.assertEqual(last_post.title, "Post Form 만들기")
        self.assertEqual(last_post.author.username, 'hani')

    def category_card_test(self, soup):
        categories_card = soup.find('div', id='categories-card')
        self.assertIn('Categories', categories_card.text)
        self.assertIn(
            f'{self.category_midsize.name} ({self.category_midsize.post_set.count()})',
            categories_card.text
        )
        self.assertIn(
            f'{self.category_semi.name} ({self.category_semi.post_set.count()})',
            categories_card.text
        )
        self.assertIn(f'미분류 (1)', categories_card.text)

    def navbar_test(self, soup):
        navbar = soup.nav
        self.assertIn('Blog', navbar.text)
        self.assertIn('About me', navbar.text)

        logo_btn = navbar.find('a', text='Do It Django')
        self.assertEqual(logo_btn.attrs['href'], '/')

        home_btn = navbar.find('a', text='Home')
        self.assertEqual(home_btn.attrs['href'], '/')

        blog_btn = navbar.find('a', text='Blog')
        self.assertEqual(blog_btn.attrs['href'], '/blog/')

        about_me_btn = navbar.find('a', text='About me')
        self.assertEqual(about_me_btn.attrs['href'], '/about_me/')

    def test_category_page(self):
        response = self.client.get(self.category_midsize.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.navbar_test(soup)
        self.category_card_test(soup)

        self.assertIn(self.category_midsize.name, soup.h1.text)

        main_area = soup.find('div', id='main_area')
        self.assertIn(self.category_midsize.name, main_area.text)
        self.assertIn(self.post_001.title, main_area.text)
        self.assertNotIn(self.post_002.title, main_area.text)
        self.assertNotIn(self.post_003.title, main_area.text)

    def test_post_list(self):
        # Post가 있는 경우
        self.assertEqual(Post.objects.count(), 3)

        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual(soup.title.text, 'Blog')

        self.navbar_test(soup)
        self.category_card_test(soup)

        main_area = soup.find('div', id='main_area')
        self.assertNotIn('아직 게시물이 없습니다', main_area.text)

        post_001_card = main_area.find('div', id='post-1')  # id가 post-1인 div를 찾아서, 그 안에
        self.assertIn(self.post_001.title, post_001_card.text)  # title이 있는지
        self.assertIn(self.post_001.category.name, post_001_card.text)  # category가 있는지
        self.assertIn(self.post_001.author.username.upper(), post_001_card.text)  # 작성자명이 있는지
        self.assertIn(self.tag_grandeur.name, post_001_card.text)
        self.assertNotIn(self.tag_spark.name, post_001_card.text)
        self.assertNotIn(self.tag_ionic.name, post_001_card.text)

        post_002_card = main_area.find('div', id='post-2')
        self.assertIn(self.post_002.title, post_002_card.text)
        self.assertIn(self.post_002.category.name, post_002_card.text)
        self.assertIn(self.post_002.author.username.upper(), post_002_card.text)
        self.assertNotIn(self.tag_grandeur.name, post_002_card.text)
        self.assertNotIn(self.tag_spark.name, post_002_card.text)
        self.assertNotIn(self.tag_ionic.name, post_002_card.text)

        post_003_card = main_area.find('div', id='post-3')
        self.assertIn('미분류', post_003_card.text)
        self.assertIn(self.post_003.title, post_003_card.text)
        self.assertIn(self.post_003.author.username.upper(), post_003_card.text)
        self.assertNotIn(self.tag_grandeur.name, post_003_card.text)
        self.assertIn(self.tag_spark.name, post_003_card.text)
        self.assertIn(self.tag_ionic.name, post_003_card.text)


        # Post가 없는 경우
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        response = self.client.get('/blog/')
        soup = BeautifulSoup(response.content, 'html.parser')
        main_area = soup.find('div', id='main_area')  # id가 main-area인 div태그를 찾습니다.
        self.assertIn('아직 게시물이 없습니다', main_area.text)

    def test_post_detail(self):
        # 1.2. 그 포스트의 url 은 '/blog/1/'이다. 
        self.assertEqual(self.post_001.get_absolute_url(), '/blog/1')

        # 2. 첫 번째 포스트의 상세 페이지 테스트 
        # 2.1. 첫 번째 포스트의 url 로 접근하면 정상적으로 작동한다(status code: 200)
        response = self.client.get(self.post_001.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.navbar_test(soup)

        self.category_card_test(soup)

        # 2.3. 첫 번째 포스트의 제목이 웹 브라우저 탭 타이틀에 들어 있다. 
        self.assertIn(self.post_001.title, soup.title.text)

        # 2.4. 첫 번째 포스트의 제목이 포스트 영역에 있다. 
        main_area = soup.find('div', id='main_area')
        post_area = main_area.find('div', id='post_area')
        self.assertIn(self.post_001.title, post_area.text)
        self.assertIn(self.category_midsize.name, post_area.text)
        
        #2.5. 작성자 이름이 포스트 영역에 에 있다. 
        self.assertIn(self.user_jieun.username.upper(), post_area.text)

        # 2.6. 첫 번째 포스트의 내용(content)이 포스트 영역에 있다. 
        self.assertIn(self.post_001.content, post_area.text)

        # tags test 
        self.assertIn(self.tag_grandeur.name, post_area.text)
        self.assertNotIn(self.tag_spark.name, post_area.text)
        self.assertNotIn(self.tag_ionic.name, post_area.text)


    def test_tag_page(self):
        response = self.client.get(self.tag_grandeur.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.navbar_test(soup)
        self.category_card_test(soup)

        self.assertIn(self.tag_grandeur.name, soup.h1.text)

        main_area = soup.find('div', id='main_area')
        self.assertIn(self.tag_grandeur.name, main_area.text)
        self.assertIn(self.post_001.title, main_area.text)
        self.assertNotIn(self.post_002.title, main_area.text)
        self.assertNotIn(self.post_003.title, main_area.text)