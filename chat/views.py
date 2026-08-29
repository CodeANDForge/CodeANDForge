from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.mail import mail_admins
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages as django_messages

from .models import Conversation, Message
from .faq_bot import get_bot_reply


@login_required
def chat_view(request):
    conversation, created = Conversation.objects.get_or_create(user=request.user)
    if created or not conversation.is_open:
        conversation.is_open = True
        conversation.escalated_to_human = False
        conversation.save()
        Message.objects.filter(conversation=conversation).delete()
        Message.objects.create(
            conversation=conversation,
            sender="bot",
            text="أهلاً بك! أنا المساعد الآلي لـ Code & Forge. اسألني أي سؤال، ولو حبيت تكلم شخص من فريق الدعم اكتب 'أريد التحدث مع شخص'.",
        )
    messages = conversation.messages.all()
    return render(request, "chat/chat.html", {"conversation": conversation, "messages": messages})


@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid method"}, status=405)

    conversation, _ = Conversation.objects.get_or_create(user=request.user)
    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "empty"}, status=400)

    Message.objects.create(conversation=conversation, sender="user", text=text)

    bot_reply = None
    if not conversation.escalated_to_human:
        reply = get_bot_reply(text)
        if reply == "ESCALATE":
            conversation.escalated_to_human = True
            conversation.save()
            bot_reply = "تمام، هحول محادثتك دلوقتي لفريق الدعم. هيردوا عليك في أقرب وقت ممكن."
            Message.objects.create(conversation=conversation, sender="bot", text=bot_reply)
            if settings.ADMIN_NOTIFICATION_EMAIL:
                try:
                    mail_admins(
                        subject=f"طلب دعم فني من {request.user.username}",
                        message=f"العميل {request.user.username} ({request.user.email}) طلب التحدث مع فريق الدعم.\n\nآخر رسالة: {text}",
                        fail_silently=True,
                    )
                except Exception:
                    pass
        else:
            bot_reply = reply
            Message.objects.create(conversation=conversation, sender="bot", text=bot_reply)

    return JsonResponse({
        "bot_reply": bot_reply,
        "escalated": conversation.escalated_to_human,
    })


@login_required
def poll_messages(request):
    conversation, _ = Conversation.objects.get_or_create(user=request.user)
    messages = conversation.messages.values("sender", "text", "created_at")
    return JsonResponse({"messages": list(messages)})


# ---- Admin views ----

def is_staff(user):
    return user.is_staff


@login_required
def admin_conversations_list(request):
    if not request.user.is_staff:
        return redirect("services:home")
    conversations = Conversation.objects.select_related("user").order_by("-created_at")
    return render(request, "chat/admin_conversations.html", {"conversations": conversations})


@login_required
def admin_conversation_detail(request, user_id):
    if not request.user.is_staff:
        return redirect("services:home")
    target_user = get_object_or_404(User, id=user_id)
    conversation, _ = Conversation.objects.get_or_create(user=target_user)
    messages = conversation.messages.all()
    return render(request, "chat/admin_chat_detail.html", {"conversation": conversation, "messages": messages, "target_user": target_user})


@login_required
def admin_send_message(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "invalid method"}, status=405)

    target_user = get_object_or_404(User, id=user_id)
    conversation, _ = Conversation.objects.get_or_create(user=target_user)
    text = request.POST.get("text", "").strip()
    if text:
        Message.objects.create(conversation=conversation, sender="admin", text=text)
    return JsonResponse({"ok": True})


@login_required
def admin_close_conversation(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({"error": "forbidden"}, status=403)
    target_user = get_object_or_404(User, id=user_id)
    conversation = get_object_or_404(Conversation, user=target_user)
    conversation.messages.all().delete()
    conversation.is_open = False
    conversation.escalated_to_human = False
    conversation.save()
    django_messages.success(request, f"تم إنهاء ومسح محادثة {target_user.username}.")
    return redirect("chat:admin_conversations_list")
