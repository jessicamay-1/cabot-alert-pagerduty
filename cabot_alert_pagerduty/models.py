import logging
import os
import pygerduty

from django.db import models
from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData


logger = logging.getLogger(__name__)


class PagerdutyAlert(AlertPlugin):
    '''
    This plugin is used for alerting to Pagerduty from Cabot.
    The implementation is a hack, because of the current
    pagerduty design. The alerting parameters are configured on
    a per-user basis and not per service. (hipchat, email, phone-no
    etc.)

    Once you install this plugin,
    1. add a user dedicated to pagerduty
    2. configure this user as "fallback duty officer"
    3. configure the service key in this user's profile
    '''
    name = "Pagerduty"
    author = "Mahendra M"

    def send_alert(self, service, users, duty_officers):
        """Implement your send_alert functionality here."""

        subdomain = os.environ.get('PAGERDUTY_SUBDOMAIN')
        api_token = os.environ.get('PAGERDUTY_API_TOKEN')

        client = pygerduty.PagerDuty(subdomain, api_token)

        description = 'Service: %s is %s' % (service.name,
                                             service.overall_status)

        incident_key = '%s/%d' % (service.name.lower().replace(' ', '-'),
                                  service.pk)

        users = service.users_to_notify.all()

        service_keys = []
        for user in users:
            for plugin in user.profile.user_data():
                service_key = getattr(plugin, 'service_key', None)

                if service_key:
                    service_keys.append(str(service_key))

        for service_key in service_keys:
            try:
                if service.overall_status == service.PASSING_STATUS:
                    client.resolve_incident(service_key,
                                            incident_key)
                else:
                    client.trigger_incident(service_key,
                                            description,
                                            incident_key=incident_key)
            except Exception, exp:
                logger.exception('Error invoking pagerduty: %s' % str(exp))


class PagerdutyAlertUserData(AlertPluginUserData):
    name = "Pagerduty Plugin"
    service_key = models.CharField(max_length=50, blank=True, null=True)