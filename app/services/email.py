"""
Email service for the Authentication Management Component.

This module provides functionality for sending emails using either SMTP or SendGrid.
It includes functions for sending verification emails and password reset links.
"""

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import BackgroundTasks
from pydantic import EmailStr

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails using SMTP or SendGrid."""

    def __init__(self):
        """Initialize the email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.emails_from_email = settings.EMAILS_FROM_EMAIL
        self.emails_from_name = settings.EMAILS_FROM_NAME or settings.PROJECT_NAME
        
        # Check if SendGrid is configured
        self.use_sendgrid = False
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            if self.smtp_user and "sendgrid" in self.smtp_host.lower():
                self.use_sendgrid = True
                self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.smtp_password)
                logger.info("SendGrid client initialized")
        except ImportError:
            logger.warning("SendGrid package not installed. Using SMTP instead.")
        except Exception as e:
            logger.error(f"Error initializing SendGrid client: {e}")

    # PUBLIC_INTERFACE
    async def send_email(
        self,
        email_to: Union[EmailStr, List[EmailStr]],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send an email to the specified recipient(s).
        
        Args:
            email_to: Email address(es) to send to
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content of the email (optional)
            background_tasks: FastAPI BackgroundTasks for sending email in background
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.emails_from_email or not self.smtp_host:
            logger.error("Email settings not configured")
            return False
            
        if background_tasks:
            background_tasks.add_task(
                self._send_email_task,
                email_to=email_to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
            return True
        
        return await self._send_email_task(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    async def _send_email_task(
        self,
        email_to: Union[EmailStr, List[EmailStr]],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Task for sending an email.
        
        Args:
            email_to: Email address(es) to send to
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content of the email (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if isinstance(email_to, str):
            email_to = [email_to]
            
        if not text_content:
            # Create a simple text version from HTML
            text_content = html_content.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n\n")
            
        try:
            if self.use_sendgrid:
                return await self._send_with_sendgrid(email_to, subject, html_content, text_content)
            else:
                return await self._send_with_smtp(email_to, subject, html_content, text_content)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _send_with_smtp(
        self,
        email_to: List[EmailStr],
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            email_to: List of email addresses to send to
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content of the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.emails_from_name} <{self.emails_from_email}>"
        message["To"] = ", ".join(email_to)
        
        # Add text and HTML parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        try:
            if self.smtp_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.emails_from_email, email_to, message.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.emails_from_email, email_to, message.as_string())
            
            logger.info(f"Email sent successfully to {', '.join(email_to)}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    async def _send_with_sendgrid(
        self,
        email_to: List[EmailStr],
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """
        Send an email using SendGrid.
        
        Args:
            email_to: List of email addresses to send to
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content of the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        from sendgrid.helpers.mail import Mail, Email, To, Content, PlainTextContent, HtmlContent
        
        try:
            from_email = Email(self.emails_from_email, self.emails_from_name)
            
            # Create a separate email for each recipient (SendGrid best practice)
            for recipient in email_to:
                to_email = To(recipient)
                plain_content = PlainTextContent(text_content)
                html_content_obj = HtmlContent(html_content)
                
                mail = Mail(
                    from_email=from_email,
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=plain_content,
                    html_content=html_content_obj
                )
                
                response = self.sendgrid_client.send(mail)
                
                if response.status_code not in (200, 201, 202):
                    logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                    return False
                    
            logger.info(f"Email sent successfully via SendGrid to {', '.join(email_to)}")
            return True
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False

    # PUBLIC_INTERFACE
    async def send_verification_email(
        self,
        email_to: EmailStr,
        token: str,
        username: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send a verification email with a verification link.
        
        Args:
            email_to: Email address to send to
            token: Verification token
            username: Username of the recipient
            background_tasks: FastAPI BackgroundTasks for sending email in background
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Verify your account"
        
        # Create verification link
        verification_link = f"{settings.API_V1_STR}/auth/verify-email?token={token}"
        
        # Create email content
        html_content = f"""
        <html>
            <body>
                <p>Hi {username},</p>
                <p>Welcome to {project_name}!</p>
                <p>Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_link}">Verify Email</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{verification_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't sign up for an account, you can ignore this email.</p>
                <p>Thanks,<br>The {project_name} Team</p>
            </body>
        </html>
        """
        
        text_content = f"""
        Hi {username},
        
        Welcome to {project_name}!
        
        Please verify your email address by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't sign up for an account, you can ignore this email.
        
        Thanks,
        The {project_name} Team
        """
        
        return await self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            background_tasks=background_tasks,
        )

    # PUBLIC_INTERFACE
    async def send_password_reset_email(
        self,
        email_to: EmailStr,
        token: str,
        username: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send a password reset email with a reset link.
        
        Args:
            email_to: Email address to send to
            token: Password reset token
            username: Username of the recipient
            background_tasks: FastAPI BackgroundTasks for sending email in background
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Password Reset"
        
        # Create reset link
        reset_link = f"{settings.API_V1_STR}/auth/reset-password?token={token}"
        
        # Create email content
        html_content = f"""
        <html>
            <body>
                <p>Hi {username},</p>
                <p>You have requested to reset your password for {project_name}.</p>
                <p>Please click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{reset_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request a password reset, you can ignore this email.</p>
                <p>Thanks,<br>The {project_name} Team</p>
            </body>
        </html>
        """
        
        text_content = f"""
        Hi {username},
        
        You have requested to reset your password for {project_name}.
        
        Please click the link below to reset your password:
        {reset_link}
        
        This link will expire in 24 hours.
        
        If you didn't request a password reset, you can ignore this email.
        
        Thanks,
        The {project_name} Team
        """
        
        return await self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            background_tasks=background_tasks,
        )

    # PUBLIC_INTERFACE
    async def send_test_email(
        self,
        email_to: EmailStr,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send a test email to verify email configuration.
        
        Args:
            email_to: Email address to send to
            background_tasks: FastAPI BackgroundTasks for sending email in background
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Test Email"
        
        html_content = f"""
        <html>
            <body>
                <p>This is a test email from {project_name}.</p>
                <p>If you received this email, your email configuration is working correctly.</p>
            </body>
        </html>
        """
        
        text_content = f"""
        This is a test email from {project_name}.
        
        If you received this email, your email configuration is working correctly.
        """
        
        return await self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            background_tasks=background_tasks,
        )