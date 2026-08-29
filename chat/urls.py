from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("send/", views.send_message, name="send_message"),
    path("poll/", views.poll_messages, name="poll_messages"),
    path("admin/conversations/", views.admin_conversations_list, name="admin_conversations_list"),
    path("admin/conversations/<int:user_id>/", views.admin_conversation_detail, name="admin_conversation_detail"),
    path("admin/conversations/<int:user_id>/send/", views.admin_send_message, name="admin_send_message"),
    path("admin/conversations/<int:user_id>/close/", views.admin_close_conversation, name="admin_close_conversation"),
]
