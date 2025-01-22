import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.log
import datetime as dt
import os
import psycopg2
import secrets
import base64
import bcrypt
import logging

class ChangePasswordHandler(tornado.web.RequestHandler):
    def post(self):
        app_log = logging.getLogger("tornado.application")

        try:
            # Retrieve the token and passwords from the request
            logintoken = self.get_argument("token", None)
            old_password = self.get_argument("old_password", None)
            new_password = self.get_argument("new_password", None)

            if not (logintoken and old_password and new_password):
                self.set_status(400)
                self.write({"success": False, "error": "Missing required fields"})
                return

            # Database connection
            conn = psycopg2.connect(
                dbname=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=5432
            )
            cursor = conn.cursor()

            # Validate token and fetch user
            cursor.execute(
                "SELECT u.userid, password_hash FROM users u JOIN login_tokens lt ON u.userid = lt.userid WHERE lt.logintoken = %s",
                (logintoken,)
            )
            user = cursor.fetchone()

            if not user:
                self.set_status(401)
                self.write({"success": False, "error": "Invalid token"})
                return

            userid, password_hash = user

            # Check if old password matches
            if not bcrypt.checkpw(old_password.encode("utf-8"), password_hash.encode("utf-8")):
                self.set_status(401)
                self.write({"success": False, "error": "Old password is incorrect"})
                return

            # Update password
            hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE userid = %s",
                (hashed_password, userid)
            )
            conn.commit()

            self.write({"success": True, "message": "Password changed successfully"})
        except Exception as e:
            app_log.error("Error in ChangePasswordHandler: %s", e)
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})
        finally:
            if "conn" in locals():
                cursor.close()
                conn.close()
