from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

@hooks.register('register_admin_menu_item')
def register_api_docs_menu_item():
    return MenuItem(
        _('API Documentation'),
        '/api/docs/',
        classnames='icon icon-doc-full',
        order=10000,  
    )

@hooks.register('register_admin_menu_item')
def register_api_schema_menu_item():
    return MenuItem(
        _('API Schema'),
        '/api/schema/',
        classnames='icon icon-code',
        order=10001,  
    )