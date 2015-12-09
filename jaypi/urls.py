from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse

from mezzanine.core.sitemaps import DisplayableSitemap
from mezzanine.core.views import direct_to_template
from mezzanine.conf import settings


admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.

urlpatterns = i18n_patterns("",
    # Change the admin prefix here to use an alternate URL for the
    # admin interface, which would be marginally more secure.
    ("^admin/", include(admin.site.urls)),
)

if settings.USE_MODELTRANSLATION:
    urlpatterns += patterns('',
        url('^i18n/$', 'django.views.i18n.set_language', name='set_language'),
    )

urlpatterns += patterns('',
    # HOMEPAGE AS STATIC TEMPLATE
    # ---------------------------
    # This pattern simply loads the index.html template. It isn't
    # commented out like the others, so it's the default. You only need
    # one homepage pattern, so if you use a different one, comment this
    # one out.

    url("^$", direct_to_template, {"template": "index.html"}, name="home"),
)

# Include mezzanine.urls explicitly

# JavaScript localization feature
js_info_dict = {'domain': 'django'}
urlpatterns += patterns('django.views.i18n',
    (r'^jsi18n/(?P<packages>\S+?)/$', 'javascript_catalog', js_info_dict),
)

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns += patterns('',
            url(r'^__debug__/', include(debug_toolbar.urls)),
        )

# Django's sitemap app.
if "django.contrib.sitemaps" in settings.INSTALLED_APPS:
    sitemaps = {"sitemaps": {"all": DisplayableSitemap}}
    urlpatterns += patterns("django.contrib.sitemaps.views",
        ("^sitemap\.xml$", "sitemap", sitemaps)
    )

# Return a robots.txt that disallows all spiders when DEBUG is True.
if getattr(settings, "DEBUG", False):
    urlpatterns += patterns("",
        ("^robots.txt$", lambda r: HttpResponse("User-agent: *\nDisallow: /",
                                                content_type="text/plain")),
    )

# Miscellanous Mezzanine patterns.
urlpatterns += patterns("",
    ("^", include("mezzanine.core.urls")),
    ("^", include("mezzanine.generic.urls")),
)

# Mezzanine's Accounts app
_old_accounts_enabled = getattr(settings, "ACCOUNTS_ENABLED", False)
if _old_accounts_enabled:
    import warnings
    warnings.warn("The setting ACCOUNTS_ENABLED is deprecated. Please "
                  "add mezzanine.accounts to INSTALLED_APPS.")
if _old_accounts_enabled or "mezzanine.accounts" in settings.INSTALLED_APPS:
    # We don't define a URL prefix here such as /account/ since we want
    # to honour the LOGIN_* settings, which Django has prefixed with
    # /account/ by default. So those settings are used in accounts.urls
    urlpatterns += patterns("",
        ("^", include("mezzanine.accounts.urls")),
    )

# Mezzanine's Blog app.
# Plugin LaterPay here
blog_installed = "mezzanine.blog" in settings.INSTALLED_APPS
if blog_installed:
    BLOG_SLUG = settings.BLOG_SLUG.rstrip("/")
    blog_patterns = patterns("",
        ("^%s" % BLOG_SLUG, include("jaypi.custom_blog_urls")),
    )
    urlpatterns += blog_patterns

# Mezzanine's Pages app.
PAGES_SLUG = ""
if "mezzanine.pages" in settings.INSTALLED_APPS:
    # No BLOG_SLUG means catch-all patterns belong to the blog,
    # so give pages their own prefix and inject them before the
    # blog urlpatterns.
    if blog_installed and not BLOG_SLUG:
        PAGES_SLUG = getattr(settings, "PAGES_SLUG", "pages").strip("/") + "/"
        blog_patterns_start = urlpatterns.index(blog_patterns[0])
        urlpatterns[blog_patterns_start:len(blog_patterns)] = patterns("",
            ("^%s" % str(PAGES_SLUG), include("mezzanine.pages.urls")),
        )
    else:
        urlpatterns += patterns("",
            ("^", include("mezzanine.pages.urls")),
        )

# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.
handler404 = "mezzanine.core.views.page_not_found"
handler500 = "mezzanine.core.views.server_error"
