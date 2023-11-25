from flask import Flask, request, jsonify, render_template
import threading
from azure.communication.email import EmailClient, EmailContent, EmailMessage, EmailRecipients, EmailAddress
from azure.core.exceptions import ServiceRequestError
import csv
import io

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('mailer.html')


@app.route('/submit', methods=['POST'])
def submit():
    sender_address = request.form['sender_address']
    subject_template = request.form['subject_template']
    reply_to_address = request.form['reply_to_address']
    num_threads = int(request.form['num_threads'])
    html_content = request.form['html_content']
    connection_string = request.form['connection_string']
    csv_file = request.files['csv_file']

    contacts = read_csv(csv_file)
    email_client = EmailClient.from_connection_string(connection_string)

    # Create and start a separate thread for sending emails.
    threads = []
    for contact in contacts:
        if threading.active_count() < num_threads:
            thread = threading.Thread(target=send_email, args=(
            email_client, contact, sender_address, subject_template, reply_to_address, html_content))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    return jsonify({'message': 'Emails are being sent.'})


def read_csv(csv_file):
    stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    return list(csv_input)


def send_email(email_client, contact, sender_address, subject_template, reply_to_address, html_content):
    try:
        name = contact["Name"]
        company = contact["Company"]
        email = contact["Email"]
        subject = subject_template.format(Name=name, Company=company)

        # Construct the email message
        email_message = EmailMessage(
            sender=sender_address,
            content=EmailContent(
                subject=subject,
                html=html_content
            ),
            recipients=EmailRecipients(
                to=[EmailAddress(email=email)]
            )
        )

        # Replace 'begin_send' with the appropriate method to send an email
        email_client.send(email_message)

        print(f"Email sent to {name} at {email}")

    except ServiceRequestError as e:
        print(f"Failed to send email to {email}: {e}")


if __name__ == '__main__':
    app.run(debug=True)