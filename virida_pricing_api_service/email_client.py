import os

import sendgrid
from sendgrid.helpers.mail import Mail

from schemas.email import AlertEmailTemplate, BenchmarkIndexEmailTemplate
from config import import_class

config = import_class(os.environ['APP_SETTINGS'])


def send_alert_email(template: AlertEmailTemplate):
    """Send alert email

    :param template: The 'SendGrid' email template parameters
    :type template: AlertEmailTemplatae
    :returns: The sendgrid HTTP response.
    """

    mail = Mail(config.SENDGRID_ALERTS_SENDER, config.ALERTS_EMAIL)
    mail.template_id = config.SENDGRID_ALERTS_TEMPLATE_ID
    mail.dynamic_template_data = template.dict()

    try:
        sendgrid_connection = sendgrid.SendGridAPIClient(config.SENDGRID_API_KEY)
        return sendgrid_connection.send(mail)
    except Exception as ex:
        print("[-] Error encountered while attempting to send the alerts email - ", str(ex))


def send_indexes_email(template: BenchmarkIndexEmailTemplate):
    """Send indexes email

    :param template: The 'SendGrid' email template parameters
    :type template: BenchmarkIndexEmailTemplate
    :returns: The sendgrid HTTP response.
    """

    mail = Mail(config.SENDGRID_ALERTS_SENDER, config.ALERTS_EMAIL)
    mail.template_id = config.SENDGRID_INDEXES_TEMPLATE_ID
    mail.dynamic_template_data = template.dict()

    try:
        sendgrid_connection = sendgrid.SendGridAPIClient(config.SENDGRID_API_KEY)
        return sendgrid_connection.send(mail)
    except Exception as ex:
        print("[-] Error encountered while attempting to send the indexes email - ", str(ex))
