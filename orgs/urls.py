from django.urls import path
from . import views
from .models import Report
#from .views import get_unit_tree_data


urlpatterns = [
    path('', views.home),
    path('unit_tree_data/', views.get_unit_tree_data),
    path('unit/<int:node_id>/', views.unit, name='unit'),
    path('company/<int:node_id>/', views.company_view, name='company'),
    path('function/<int:node_id>/', views.function_view, name='function'),
    path('asset/<int:asset_id>/', views.asset_view, name='asset'),
    path('generate-pdf/<str:report_ids>/', views.generate_pdf, name='generate_pdf'),
    path('detailed-condition/<int:report_id>/', views.detailed_condition, name='detailed_condition'),
    path('create-entry/<int:node_id>/', views.create_entry, name='create_entry'),
    path('edit-entry/<int:report_id>/', views.edit_entry, name='edit_entry'),
    path('edit-entry/<path:attachment_url>/', views.show_attachments, name="show_attachments"),
    path('rename/<int:node_id>/', views.rename_node, name='rename'),
    path('create-child/<int:node_id>/', views.create_child_node, name='create-child'),
    path('create-here/<int:node_id>/', views.create_here_node, name='create-here'),
    path('move-node/', views.move_node, name='move-node'),
    path('admin-page/', views.admin_page, name='admin-page'),
    path('admin-page/create-company/', views.admin_create_company, name='admin-create-company'),
    path('admin-page/create-fault/', views.admin_create_fault, name='admin-create-fault'),
    path('admin-page/edit-fault/<int:fault_id>/', views.admin_edit_fault, name='admin-edit-fault'),
    path('admin-page/delete-fault/<int:fault_id>/', views.admin_delete_fault, name='admin-delete-fault'),
    path('admin-page/create-tech/', views.admin_create_tech, name='admin-create-tech'),
    path('admin-page/edit-tech/<int:tech_id>/', views.admin_edit_tech, name='admin-edit-tech'),
    path('admin-page/delete-tech/<int:tech_id>/', views.admin_delete_tech, name='admin-delete-tech'),
    path('admin-page/create-analyst/', views.admin_create_analyst, name='admin-create-analyst'),
    path('admin-page/edit-analyst/<int:analyst_id>/', views.admin_edit_analyst, name='admin-edit-analyst'),
    path('admin-page/delete-analyst/<int:analyst_id>/', views.admin_delete_analyst, name='admin-delete-analyst'),
    path('about/', views.about),
    path('report/', views.report),
]