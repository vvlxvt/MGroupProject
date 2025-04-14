import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import Post


class LatestPostsFeed(Feed):
    # подкласс фреймворка Feed синдицированных новостных лент
    title = "Мои работы"
    link = reverse_lazy("job:post_list")
    description = "Новые статьи о наших работах"

    def items(self):
        return Post.published.all()[:3]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords_html(
            markdown.markdown(item.body), 30
        )  # конвертирую контент Markdown -> HTML

    def item_pubdate(self, item):
        return item.publish
