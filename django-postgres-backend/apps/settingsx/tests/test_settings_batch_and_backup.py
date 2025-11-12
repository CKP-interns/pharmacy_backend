from django.test import TestCase
from rest_framework.test import APIClient
from apps.settingsx.models import SettingKV, BackupArchive


class SettingsBatchAndBackupTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_group_save(self):
        r = self.client.post('/api/v1/settings/app/save', {
            "alerts": {"ALERT_LOW_STOCK_DEFAULT": "60"},
            "tax": {"TAX_GST_RATE": "18"}
        }, format='json')
        assert r.status_code == 200
        assert SettingKV.objects.get(key='ALERT_LOW_STOCK_DEFAULT').value == '60'
        assert SettingKV.objects.get(key='TAX_GST_RATE').value == '18'

    def test_backup_create(self):
        # needs no special setup, will dump an empty DB
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create(username='admin', is_superuser=True)
        self.client.force_authenticate(admin)
        r = self.client.post('/api/v1/settings/backup/create/', {}, format='json')
        assert r.status_code == 200
        assert BackupArchive.objects.filter(id=r.data.get('archive_id')).exists()

