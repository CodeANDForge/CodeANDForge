from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)
    escalated_to_human = models.BooleanField(default=False)

    def __str__(self):
        return f"محادثة {self.user.username}"


class Message(models.Model):
    SENDER_CHOICES = [
        ("user", "عميل"),
        ("bot", "مساعد آلي"),
        ("admin", "دعم فني"),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"
