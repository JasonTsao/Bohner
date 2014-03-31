# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Account'
        db.create_table(u'accounts_account', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('user_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('facebook_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('uber', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('profile_pic', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('birthday', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('home_town', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('is_active', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['Account'])

        # Adding model 'AccountDeviceID'
        db.create_table(u'accounts_accountdeviceid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('device_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['AccountDeviceID'])

        # Adding model 'AccountSettings'
        db.create_table(u'accounts_accountsettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.Account'], unique=True)),
            ('private', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('searchable', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('reminder_on', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('reminder_delta', self.gf('timedelta.fields.TimedeltaField')(null=True, blank=True)),
            ('vibrate_on_notification', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['AccountSettings'])

        # Adding model 'AccountSetting'
        db.create_table(u'accounts_accountsetting', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('setting_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('setting_value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, null=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['AccountSetting'])

        # Adding unique constraint on 'AccountSetting', fields ['account', 'setting_name']
        db.create_unique(u'accounts_accountsetting', ['account_id', 'setting_name'])

        # Adding model 'AccountLink'
        db.create_table(u'accounts_accountlink', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='account_user', to=orm['accounts.Account'])),
            ('friend', self.gf('django.db.models.fields.related.ForeignKey')(related_name='friend', to=orm['accounts.Account'])),
            ('invited_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('blocked', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['AccountLink'])

        # Adding unique constraint on 'AccountLink', fields ['account_user', 'friend']
        db.create_unique(u'accounts_accountlink', ['account_user_id', 'friend_id'])

        # Adding model 'Group'
        db.create_table(u'accounts_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group_creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='group_creator', to=orm['accounts.Account'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_active', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'accounts', ['Group'])

        # Adding unique constraint on 'Group', fields ['group_creator', 'name']
        db.create_unique(u'accounts_group', ['group_creator_id', 'name'])

        # Adding M2M table for field members on 'Group'
        db.create_table(u'accounts_group_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm[u'accounts.group'], null=False)),
            ('account', models.ForeignKey(orm[u'accounts.account'], null=False))
        ))
        db.create_unique(u'accounts_group_members', ['group_id', 'account_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Group', fields ['group_creator', 'name']
        db.delete_unique(u'accounts_group', ['group_creator_id', 'name'])

        # Removing unique constraint on 'AccountLink', fields ['account_user', 'friend']
        db.delete_unique(u'accounts_accountlink', ['account_user_id', 'friend_id'])

        # Removing unique constraint on 'AccountSetting', fields ['account', 'setting_name']
        db.delete_unique(u'accounts_accountsetting', ['account_id', 'setting_name'])

        # Deleting model 'Account'
        db.delete_table(u'accounts_account')

        # Deleting model 'AccountDeviceID'
        db.delete_table(u'accounts_accountdeviceid')

        # Deleting model 'AccountSettings'
        db.delete_table(u'accounts_accountsettings')

        # Deleting model 'AccountSetting'
        db.delete_table(u'accounts_accountsetting')

        # Deleting model 'AccountLink'
        db.delete_table(u'accounts_accountlink')

        # Deleting model 'Group'
        db.delete_table(u'accounts_group')

        # Removing M2M table for field members on 'Group'
        db.delete_table('accounts_group_members')


    models = {
        u'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'home_town': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'profile_pic': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'uber': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'accounts.accountdeviceid': {
            'Meta': {'object_name': 'AccountDeviceID'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'device_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'accounts.accountlink': {
            'Meta': {'unique_together': "(('account_user', 'friend'),)", 'object_name': 'AccountLink'},
            'account_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'account_user'", 'to': u"orm['accounts.Account']"}),
            'blocked': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'friend': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'friend'", 'to': u"orm['accounts.Account']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'accounts.accountsetting': {
            'Meta': {'unique_together': "(('account', 'setting_name'),)", 'object_name': 'AccountSetting'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Account']"}),
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'setting_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'setting_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'accounts.accountsettings': {
            'Meta': {'object_name': 'AccountSettings'},
            'account': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['accounts.Account']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'private': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'reminder_delta': ('timedelta.fields.TimedeltaField', [], {'null': 'True', 'blank': 'True'}),
            'reminder_on': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'searchable': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'vibrate_on_notification': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'accounts.group': {
            'Meta': {'unique_together': "(('group_creator', 'name'),)", 'object_name': 'Group'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group_creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'group_creator'", 'to': u"orm['accounts.Account']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['accounts.Account']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['accounts']