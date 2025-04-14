from django import forms


class CustomTagWidget(forms.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {"size": "100"}  # Установите желаемый размер поля
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            value = []

        tags_display = ", ".join(
            [tag.name for tag in value]
        )  # Показываем только названия тегов

        return forms.TextInput().render(name, tags_display, attrs)
