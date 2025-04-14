from django.template.defaultfilters import slugify
from taggit.models import Tag, TaggedItem


def translit_to_eng(s: str) -> str:
    d = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ь": "",
        "ы": "y",
        "ъ": "",
        "э": "r",
        "ю": "yu",
        "я": "ya",
    }

    return "".join(map(lambda x: d[x] if d.get(x, False) else x, s.lower()))


class RuTag(Tag):
    class Meta:
        proxy = True  #  класс является прокси-моделью, т.е. он не создает отдельной таблицы в базе данных, а использует таблицу родительской модели.

    def slugify(self, tag, i=None):
        return slugify(translit_to_eng(self.name))[:128]  # макс. размер slug


class RuTaggedItem(TaggedItem):

    class Meta:
        proxy = True

    @classmethod
    def tag_model(cls):
        return RuTag
