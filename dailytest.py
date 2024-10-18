import os
import tableauserverclient as TSC
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

def send_email(image_file_name, recipient_email):
    print(f"Preparing to send the email to {recipient_email}...")

    message = Mail(
        from_email='roberto@networkmedia.com',
        to_emails=recipient_email,
        subject=subject,
        html_content=f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 0; text-align: center; font-family: Arial, sans-serif;">
            <h3 style="color: #333;">How much did you make?</h3>
            <p>{body}</p>
            <img src="cid:image1" style="max-width: 100%; height: auto; display: block; margin: auto;">
        </body>
        </html>
        """
    )

    try:
        with open(image_file_name, 'rb') as img_file:
            img_data = img_file.read()
            print(f"Image {image_file_name} successfully read.")
    except Exception as e:
        print(f"Error reading image file: {e}")
        return

    encoded_image = base64.b64encode(img_data).decode()
    attached_file = Attachment(
        file_content=encoded_image,
        file_type='image/png',
        file_name=image_file_name,
        disposition='inline', 
        content_id='image1'
    )

    message.add_attachment(attached_file)

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

print("Setting up Tableau connection...")
server_url = 'https://us-west-2b.online.tableau.com/'
personal_access_token_name = os.getenv('TABLEAU_TOKEN_NAME')
personal_access_token_value = os.getenv('TABLEAU_TOKEN_VALUE')
site_name = 'networkmediacom'
workbook_id = '4a8e0197-fd49-416e-b594-6ff90c5ac4b8'

sender_email = 'roberto@networkmedia.com'
creators = [
    {'name': 'Allie Sparks', 'pay_to': 'Allie Sparks', 'email': 'analu.gcs@gmail.com', 'manager_1': 'Allie Sparks','type': 'Creator'},
]
subject = "Check Now How Much You Made!"
body = "Your earnings"

tableau_auth = TSC.PersonalAccessTokenAuth(
    personal_access_token_name,
    personal_access_token_value,
    site_name
)

server = TSC.Server(server_url, use_server_version=True)

pay_to_creator_views = [
    'b1745669-6199-408c-9736-bd089252c080', 'ecc82caa-6990-4565-a31d-ce66a7e50fa1',
    '7709dc4a-28e9-4c50-aa23-12ddb7be876b', '8b033703-de63-4d5d-b02f-234fa5b0192d',
    '20ee2f25-a813-4d80-bc0a-05faa8329f2d', '0aaac321-28b7-4ad8-b464-082e2ac0081e',
    '10e9adbf-8068-4cd4-ac67-d53c9345dd20', '83a3d315-b8e3-488e-97c3-e5c195904c96',
    'f990199f-bb12-4a8d-8b20-d04b204cd106', 'a16b80d2-8277-49dc-8e76-4c8e8b14a27c',
    'b0658762-4235-43b5-bb10-1fed0e0dd094'
]
creator_filter_views = [
    'f0ead2e8-1ba6-4dc6-8924-eccec3570aed', '6499bd01-7714-4d8a-8dc6-1eb93fbef474',
    'e8b72c15-ae7f-4b0f-b79f-8db35134ed61', '1440f136-7846-4732-a3e8-bab54074f13b',
    'ed3680f6-6252-4cb1-887b-1538e5c28e6f', '94086978-3b5e-45c3-8147-78dd64bb1366',
    '9c8f6b10-33c1-4190-a7cb-871d0adc6d4f'
]

creator_type_name_creator = [
    '979b90d4-5964-4868-b223-586f881fa081'
]

managee_videos_views = [
    '898c6384-14c4-4c94-98c0-459aea026331'
]

dashboard_principal_id = '9c8f6b10-33c1-4190-a7cb-871d0adc6d4f'

print("Connecting to Tableau Server...")
try:
    with server.auth.sign_in(tableau_auth):
        all_workbooks, pagination_item = server.workbooks.get()
        workbook = next((wb for wb in all_workbooks if wb.id == workbook_id), None)

        if workbook:
            server.workbooks.populate_views(workbook)
            for creator in creators:
                creator_names = creator['name']
                pay_to_creator = creator['pay_to']
                recipient_email = creator['email']
                manager_1 = creator['manager_1']
                creator_type = creator['type']
                image_file_name_to_send = None

                for view in workbook.views:
                    image_request_options = TSC.ImageRequestOptions(imageresolution=TSC.ImageRequestOptions.Resolution.High)
                
                    if view.id in pay_to_creator_views:
                        image_request_options.vf('Pay_To_Creator_1', pay_to_creator)

                    if view.id in creator_filter_views:
                        image_request_options.vf(creator_type, creator_names)
                    
                    if view.id in creator_type_name_creator:
                        image_request_options.vf('Creator', creator_names)

                    server.views.populate_image(view, image_request_options)

                    if view.id == dashboard_principal_id:
                        image_file_name_to_send = f'{view.name}_{"_".join(creator_names.split())}.png'
                        with open(image_file_name_to_send, 'wb') as file:
                            file.write(view.image)
                    else:
                        image_file_name = f'{view.name}_{"_".join(creator_names.split())}.png'
                        with open(image_file_name, 'wb') as file:
                            file.write(view.image)

                if image_file_name_to_send:
                    send_email(image_file_name_to_send, recipient_email)

        else:
            print("Workbook not found.")
except Exception as e:
    print(f"Error connecting to Tableau Server: {e}")
