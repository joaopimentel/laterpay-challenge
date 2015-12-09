from __future__ import unicode_literals
from future.builtins import str
from future.builtins import int
from calendar import month_name

from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from mezzanine.blog.models import BlogPost, BlogCategory
from mezzanine.blog.feeds import PostsRSS, PostsAtom
from mezzanine.conf import settings
from mezzanine.generic.models import Keyword
from mezzanine.utils.views import render, paginate

from laterpay import LaterPayClient, ItemDefinition

User = get_user_model()


def blog_post_list(request, tag=None, year=None, month=None, username=None,
                   category=None, template="blog_post_list.html",
                   extra_context=None):
    """
    Display a list of blog posts that are filtered by tag, year, month,
    author or category. Custom templates are checked for using the name
    ``blog/blog_post_list_XXX.html`` where ``XXX`` is either the
    category slug or author's username if given.
    """
    templates = []
    blog_posts = BlogPost.objects.published(for_user=request.user)
    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        blog_posts = blog_posts.filter(keywords__keyword=tag)
    if year is not None:
        blog_posts = blog_posts.filter(publish_date__year=year)
        if month is not None:
            blog_posts = blog_posts.filter(publish_date__month=month)
            try:
                month = month_name[int(month)]
            except IndexError:
                raise Http404()
    if category is not None:
        category = get_object_or_404(BlogCategory, slug=category)
        blog_posts = blog_posts.filter(categories=category)
        templates.append(u"blog_post_list_%s.html" %
                          str(category.slug))
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        blog_posts = blog_posts.filter(user=author)
        templates.append(u"blog_post_list_%s.html" % username)

    prefetch = ("categories", "keywords__keyword")
    blog_posts = blog_posts.select_related("user").prefetch_related(*prefetch)
    blog_posts = paginate(blog_posts, request.GET.get("page", 1),
                          settings.BLOG_POST_PER_PAGE,
                          settings.MAX_PAGING_LINKS)
    context = {"blog_posts": blog_posts, "year": year, "month": month,
               "tag": tag, "category": category, "author": author}
    context.update(extra_context or {})
    templates.append(template)
    return render(request, templates, context)


def blog_post_detail(request, slug, year=None, month=None, day=None,
                     template="blog/blog_post_detail.html",
                     extra_context=None):
    """. Custom templates are checked for using the name
    ``blog/blog_post_detail_XXX.html`` where ``XXX`` is the blog
    posts's slug.
    """
    lpclient = LaterPayClient(cp_key=settings.LATERPAY_ID,
                              shared_secret=settings.LATERPAY_KEY,
                              api_root=settings.LATERPAY_API_ROOT,
                              web_root=settings.LATERPAY_WEB_ROOT,
                              lptoken=request.session.get('lptoken'))
    post_url = request.build_absolute_uri()
    # check for laterpay token in url
    url_lptoken = request.GET.get('lptoken')
    if url_lptoken:
        request.session['lptoken'] = url_lptoken
        lpclient.lptoken = url_lptoken
    # check for laterpay token in session data
    if not request.session.get('lptoken', False):
        gettoken_url = lpclient.get_gettoken_redirect(post_url)
        return redirect(gettoken_url)

    # Get blog post
    blog_posts = BlogPost.objects.published(for_user=request.user) \
                                 .select_related()
    blog_post = get_object_or_404(blog_posts, slug=slug)
    related_posts = blog_post.related_posts.published(for_user=request.user)
    context = {
        "blog_post": blog_post,
        "editable_obj": blog_post,
        "related_posts": related_posts,
    }
    context.update(extra_context or {})
    templates = [u"blog/blog_post_detail_%s.html" % str(slug), template]

    article_id = blog_post.slug
    access_data = lpclient.get_access(article_id)
    if access_data.get('status') == 'invalid_token':
        gettoken_url = lpclient.get_gettoken_redirect(post_url)
        return redirect(gettoken_url)
    article_access = False
    if access_data.get('status') == 'ok':
        # See if user has access
        article_access = access_data['articles'][article_id]['access']

    if not article_access:
        item = ItemDefinition(article_id, 'EUR50',
                              request.build_absolute_uri(),
                              blog_post.title, cp=settings.LATERPAY_ID)
        add_url = lpclient.get_add_url(item, use_dialog_api=False)
        return redirect(add_url)

    return render(request, templates, context)


def blog_post_feed(request, format, **kwargs):
    """
    Blog posts feeds - maps format to the correct feed view.
    """
    try:
        return {"rss": PostsRSS, "atom": PostsAtom}[format](**kwargs)(request)
    except KeyError:
        raise Http404()
