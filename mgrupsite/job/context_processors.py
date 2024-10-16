from job.utils import menu

def menu_context(request):
    return {'menu': menu, 'facemenu': menu['services'].get('submenus', [])}

