from django.contrib import admin
from .models import SettingKV, BusinessProfile, DocCounter, BackupArchive, DeletedInvoiceNumber

admin.site.register(SettingKV)
admin.site.register(BusinessProfile)
admin.site.register(DocCounter)
admin.site.register(BackupArchive)
admin.site.register(DeletedInvoiceNumber)

