from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    # What columns show up on the main list
    list_display = ('email', 'credits', 'is_active', 'is_staff', 'date_joined')
    
    # Adds a search bar at the top to quickly find a user
    search_fields = ('email',)
    
    # Adds a filter sidebar on the right
    list_filter = ('is_active', 'is_staff', 'date_joined')
    
    # Protects certain fields from accidental edits
    readonly_fields = ('date_joined', 'last_login')
    
    # Organize the detail view nicely
    fieldsets = (
        ('User Credentials', {'fields': ('email', 'password')}),
        ('Platform Economy', {'fields': ('credits',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

# Make sure to import it at the top!
from .models import Transaction 

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # What shows up in the main ledger view
    list_display = ('user', 'plan_type', 'amount', 'status', 'created_at')
    
    # Quickly filter to see all "SUCCESS" payments or all "PRO" plan buyers
    list_filter = ('status', 'plan_type', 'created_at')
    
    # The search bar: Look up a payment by the user's email or the exact Razorpay ID
    search_fields = ('user__email', 'razorpay_order_id', 'razorpay_payment_id')
    
    # CRITICAL SECURITY: Financial records should be immutable in the admin panel.
    # We make all the Razorpay data and the amount read-only so it can't be accidentally edited.
    readonly_fields = (
        'user', 
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'razorpay_signature', 
        'amount', 
        'created_at'
    )
    
    # Organize the detail view into clean sections
    fieldsets = (
        ('Customer Info', {'fields': ('user',)}),
        ('Payment Details', {'fields': ('plan_type', 'amount', 'status')}),
        ('Razorpay Audit Trail', {'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )