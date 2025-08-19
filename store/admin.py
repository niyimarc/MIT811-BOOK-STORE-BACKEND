from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Wish, WishList, Faq, EmailSubscriber, ShippingAddress, OrderNote, ContactUs


# Register your models here.
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
    # def has_change_permission(self, request, obj=None):
    #     return False
    
    # def has_add_permission(self, request, obj=None):
    #     return False

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline,]
    list_display = ('user', 'created_on', 'updated_on')

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
    # def has_change_permission(self, request, obj=None):
    #     return False
    
    # def has_add_permission(self, request, obj=None):
    #     return False

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price', 'discount', 'total',)
    extra = 1

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class ShippingAddressInline(admin.TabularInline):
    model = ShippingAddress
    extra = 1

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 1

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ShippingAddressInline, OrderNoteInline]
    list_display = ('user', 'status', 'order_reference', 'payment_made', 'total_discount', 'total_price', 'order_placed', 'packed', 'in_transit', 'delivered', 'created_on', 'updated_on')
    readonly_fields = ('user', 'order_reference', 'payment_made', 'total_discount', 'total_price', 'payment_date', 'packed_date', 'in_transit_date', 'delivered_date', 'packed', 'in_transit', 'delivered', 'order_placed')
    list_filter = ('status', 'payment_made', 'order_placed', 'packed', 'in_transit', 'delivered',)

    # def has_delete_permission(self, request, obj=None):
    #     return False
    

class WishListInline(admin.TabularInline):
    model = WishList
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return False

class WishAdmin(admin.ModelAdmin):
    inlines = [WishListInline,]
    list_display = ('user', 'created_on', 'updated_on')

    def has_delete_permission(self, request, obj=None):
        return False

class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'status')
    list_filter = ('status',)

class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email',)

    def has_delete_permission(self, request, obj=None):
        return False
    
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'message', 'created_on', 'updated_on')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Wish, WishAdmin)
admin.site.register(Faq, FaqAdmin)
admin.site.register(EmailSubscriber, EmailSubscriberAdmin)
admin.site.register(ContactUs, ContactUsAdmin)