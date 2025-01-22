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

class RegisterHandler(tornado.web.RequestHandler):
    def post(self):
        app_log = logging.getLogger("tornado.application")

        try:
            # Retrieve user information from the request
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)
            firstname = self.get_argument("firstname", None)
            lastname = self.get_argument("lastname", None)

            if not (username and password and firstname and lastname):
                self.set_status(400)
                self.write({"success": False, "error": "All fields are required"})
                return

            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Connect to the database
            conn = psycopg2.connect(
                dbname=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=5432
            )
            cursor = conn.cursor()

            # Insert the user into the database
            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                RETURNING userid;
                """,
                (username, hashed_password.decode('utf-8'))
            )
            userid = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO users_info (userid, first_name, last_name)
                VALUES (%s, %s, %s);
                """,
                (userid, firstname, lastname)
            )

            conn.commit()

            self.write({"success": True, "message": "User registered successfully"})
        except psycopg2.IntegrityError:
            conn.rollback()
            self.set_status(400)
            self.write({"success": False, "error": "Username already exists"})
        except Exception as e:
            app_log.error("Error in RegisterHandler: %s", e)
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()
