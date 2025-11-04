from django.db import models

class Prescription(models.Model):
    """TODO: 1:1 with sale invoice; patient and prescriber details"""
    pass

class H1RegisterEntry(models.Model):
    """TODO: entries for H1 schedule"""
    pass

class NDPSDailyEntry(models.Model):
    """TODO: NDPS daily registers"""
    pass

class RecallEvent(models.Model):
    """TODO: recall events for batch_lots"""
    pass
