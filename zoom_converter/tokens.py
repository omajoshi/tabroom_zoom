from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(timestamp) + str(user.pk) + str(user.email_confirmed) + user.email


email_token_generator = EmailTokenGenerator()

class TabroomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(timestamp) + str(user.pk) + str(user.tabroom_confirmed) + user.tabroom_email

tabroom_token_generator = TabroomTokenGenerator()

class ZoomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(timestamp) + str(user.pk) + str(user.zoom_confirmed) + user.zoom_email

zoom_token_generator = ZoomTokenGenerator()
