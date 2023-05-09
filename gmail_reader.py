from __future__ import print_function

import os.path
import email
import base64

from icecream import ic
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailReader:
    def __init__(self):
        # If modifying these scopes, delete the file token.json.
        self._SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        self._creds = None
        self._authenticate()
        self._service = build("gmail", "v1", credentials=self._creds)

    def _authenticate(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            self._creds = Credentials.from_authorized_user_file(
                "token.json", self._SCOPES
            )
        # If there are no (valid) credentials available, let the user log in.
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self._SCOPES
                )
                self._creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self._creds.to_json())

    def get_unread_messages_id(self, max_results=1):
        try:
            # Gets messages in inbox that are unread
            messages_result = (
                self._service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX"],
                    q="is:unread",
                    maxResults=max_results,
                )
                .execute()
            )

            if not messages_result:
                print("No messages found.")
                return

            messages = messages_result["messages"]

            message_ids = []
            for message in messages:
                message_ids.append(message["id"])

            return message_ids

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f"An error occurred: {error}")

    def get_message_html(self, message_id):
        message_result = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="raw")
            .execute()
        )

        # Parse the raw message.
        mime_msg = email.message_from_bytes(
            base64.urlsafe_b64decode(message_result["raw"])
        )

        ic(mime_msg["from"])
        ic(mime_msg["to"])
        ic(mime_msg["subject"])

        message_main_type = mime_msg.get_content_maintype()

        body_html = None

        if message_main_type == "multipart":
            for part in mime_msg.get_payload():
                content_type = part.get_content_type()
                ic(f"Content Type: {content_type}")
                if content_type == "text/html":
                    body_html = part.get_payload()
        elif message_main_type == "text":
            # ic(mime_msg.get_payload())
            ic("text email")

        return body_html

    def parse_html(self, html):
        """
        TODO: Here we will use BS4 to get the data
              we need from the email and return it.
        """
        soup = BeautifulSoup(html)
        print(soup.prettify())
        return True


if __name__ == "__main__":
    er = GmailReader()

    unread_email_id = er.get_unread_messages_id()[0]
    html = er.get_message_html(unread_email_id)
    email_body = er.parse_html(html)
