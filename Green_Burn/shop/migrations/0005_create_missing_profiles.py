from django.db import migrations


# на новой базе сигнал post_save сам создаёт Profile для каждого нового User,
# но пользователи, созданные ДО появления этой модели, профиля не получат —
# эта миграция создаёт им Profile один раз при обновлении проекта
def create_missing_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('shop', 'Profile')

    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)


def reverse_noop(apps, schema_editor):
    # откатывать назад не нужно — Profile удалится автоматически
    # вместе с моделью при откате предыдущей миграции
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_order_orderitem_profile'),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, reverse_noop),
    ]