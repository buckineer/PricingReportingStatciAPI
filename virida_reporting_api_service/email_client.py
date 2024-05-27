import sendgrid
from sendgrid.helpers.mail import Mail

from schemas.email import BaseEmailTemplate
from config import config


def send_email(template: BaseEmailTemplate):
    """Send indexes email

    :param template: The 'SendGrid' email template parameters
    :type template: BaseEmailTemplate
    :returns: The sendgrid HTTP response.
    """

    mail = Mail(config.SENDGRID_SENDER, config.SENDGRID_ALERTS_EMAIL)
    mail.template_id = config.SENDGRID_REPORTS_TEMPLATE_ID
    mail.dynamic_template_data = template.dict()

    try:
        sendgrid_connection = sendgrid.SendGridAPIClient(config.SENDGRID_API_KEY)
        return sendgrid_connection.send(mail)
    except Exception as ex:
        print("[-] Error encountered while attempting to send the indexes email - ", str(ex))
