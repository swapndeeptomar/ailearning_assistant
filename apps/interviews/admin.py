from django.contrib import admin
from .models import InterviewSession, InterviewResponse


# Inline to show responses inside InterviewSession
class InterviewResponseInline(admin.TabularInline):
    model = InterviewResponse
    extra = 0
    readonly_fields = (
        "question_text",
        "reference_context",
        "user_response_text",
        "semantic_similarity_score",
        "ai_evaluation",
        "created_at",
    )
    can_delete = False
    show_change_link = True


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "document",
        "overall_accuracy_score",
        "is_completed",
        "created_at",
    )
    list_filter = ("is_completed", "created_at")
    search_fields = ("user__username", "document__file_name")
    readonly_fields = ("id", "created_at")
    inlines = [InterviewResponseInline]


@admin.register(InterviewResponse)
class InterviewResponseAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "short_question",
        "semantic_similarity_score",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("question_text", "user_response_text")
    readonly_fields = ("created_at",)

    def short_question(self, obj):
        return obj.question_text[:50] + "..."
    short_question.short_description = "Question"