# order_module/utils.py

def apply_discount(price, discount_code):
    """اعمال تخفیف روی قیمت"""
    discount_amount = int(price * discount_code.discount_percent / 100)
    return price - discount_amount