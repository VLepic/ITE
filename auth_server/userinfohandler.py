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

class UserInfoHandler(tornado.web.RequestHandler):
    def post(self):
        app_log = logging.getLogger("tornado.application")
        conn = None  # Initialize the connection variable

        try:
            # Retrieve the token from the request
            logintoken = self.get_argument("token", None)
            app_log.info(f"Login token for userinfo received: {logintoken}")

            if not logintoken:
                self.set_status(400)
                self.write({"success": False, "error": "Missing logintoken"})
                return

            # Connect to the database
            conn = psycopg2.connect(
                dbname=os.environ["POSTGRES_DB"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=5432
            )
            cursor = conn.cursor()

            # Query to get user information based on the logintoken
            cursor.execute("""
                SELECT u.userid, u.username, ui.first_name, ui.last_name, lt.created_at, lt.expires_at, ui.last_logged_in_at
                FROM users u
                INNER JOIN users_info ui ON u.userid = ui.userid
                INNER JOIN login_tokens lt ON u.userid = lt.userid
                WHERE lt.logintoken = %s;
            """, (logintoken,))

            user_info = cursor.fetchone()

            if not user_info:
                self.set_status(404)
                self.write({"success": False, "error": "Invalid or expired logintoken"})
                return

            # Check token expiration
            if user_info[5] <= dt.datetime.now():
                self.write({
                    "success": False,
                    "token_expired": True
                })
                return

            # Return user information
            self.write({
                "success": True,
                "userid": user_info[0],
                "username": user_info[1],
                "first_name": user_info[2],
                "last_name": user_info[3],
                "token_created_at": user_info[4].isoformat(),
                "token_expires_at": user_info[5].isoformat(),
                "last_logged_in_at": user_info[6].isoformat() if user_info[6] else None,
            })

        except Exception as e:
            app_log.error(f"Error in UserInfoHandler: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})
        finally:
            if conn is not None:
                conn.close()  # Close the connection safely
