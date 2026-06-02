# fix_operators.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Online_coffeenet.settings')
django.setup()

from home_module.models import Operator
import hashlib


def fix_all_passwords():
    """اصلاح همه رمزهای plain text"""
    operators = Operator.objects.all()
    fixed_count = 0

    print("\n" + "=" * 60)
    print("🔧 شروع اصلاح رمزهای عبور اپراتورها")
    print("=" * 60)

    for op in operators:
        if len(op.password) < 64:
            old_pass = op.password
            op.set_password(old_pass)
            op.save(update_fields=['password'])
            fixed_count += 1
            print(f"✅ {op.full_name} ({op.phone}): اصلاح شد")
            print(f"   رمز قدیمی: {old_pass}")
            print(f"   رمز جدید (هش شده): {op.password[:40]}...")
        else:
            print(f"✓ {op.full_name} ({op.phone}): قبلاً هش شده")

        # تست
        print(f"   تست check_password('{op.password[:3]}...'): "
              f"{op.check_password('123') if op.password.startswith('a6') else 'N/A'}")
        print()

    print("=" * 60)
    print(f"🎉 {fixed_count} اپراتور اصلاح شدند!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    fix_all_passwords()