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

def generate_token():
    # Generate 192 bytes of random data
    random_bytes = secrets.token_bytes(192)

    # Encode the random bytes to a base64 string
    token = base64.urlsafe_b64encode(random_bytes).decode('utf-8')

    # Trim the token to exactly 256 characters
    return token[:256]


class UPLoginHandler(tornado.web.RequestHandler):
    def post(self):
        app_log = logging.getLogger("tornado.application")
        TOKEN_EXPIRATION_MINUTES = os.environ.get("TOKEN_EXPIRATION", 30)
        conn = None
        try:
            # Parse JSON request body
            data = tornado.escape.json_decode(self.request.body)
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                self.set_status(400)
                self.write({"error": "Username and password are required."})
                return

            # Connect to the database
            conn = psycopg2.connect(
                dbname=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=5432
            )
            cursor = conn.cursor()

            # Query for the user's password hash
            cursor.execute(
                """
                SELECT userid, password_hash
                FROM users
                WHERE username = %s;
                """,
                (username,)
            )
            row = cursor.fetchone()

            if row:
                userid, stored_password_hash = row

                # Verify the password
                if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                    # Check or create token
                    cursor.execute(
                        """
                        SELECT token_id, logintoken, created_at, expires_at
                        FROM login_tokens
                        WHERE userid = %s;
                        """,
                        (userid,)
                    )
                    token_row = cursor.fetchone()

                    logintoken = None
                    expires_at = None
                    app_log.info(f"If tokenrow")


                    token_id, logintoken, created_at, expires_at = token_row
                    app_log.info(f"Logintoken: {logintoken}")
                    # If no token exists or it has expired, create a new one
                    new_expires_at = dt.datetime.now() + dt.timedelta(minutes=int(TOKEN_EXPIRATION_MINUTES))
                    if logintoken is None:
                        logintoken = generate_token()

                        try:
                            cursor.execute(
                                """
                                INSERT INTO login_tokens (userid, logintoken, created_at, expires_at)
                                VALUES (%s, %s, NOW(), %s)

                                """,
                                (userid, logintoken, new_expires_at)
                            )
                            conn.commit()
                        except Exception as e:
                            app_log.error(f"Error saving token: {e}")
                            conn.rollback()

                    elif logintoken:
                        try:
                            cursor.execute(
                                """
                                UPDATE login_tokens
                                SET logintoken = %s, created_at = NOW(), expires_at = %s
                                WHERE userid = %s;

                                """,
                                (logintoken, new_expires_at, userid)
                            )
                            conn.commit()
                            print(f"Token successfully updated for user ID {userid}")
                        except Exception as e:
                            print(f"Error saving token: {e}")
                            conn.rollback()



                    # Update the user's last login timestamp
                    cursor.execute(
                        """
                        UPDATE users_info
                        SET last_logged_in_at = %s
                        WHERE userid = %s;
                        """,
                        (created_at, userid,)
                    )
                    conn.commit()

                    # Respond with success and token
                    app_log.info(f"Returning token: {logintoken}")
                    self.write({
                        "success": True,
                        "userid": userid,
                        "logintoken": logintoken,
                        "expires_at": expires_at.isoformat()
                    })
                else:
                    self.set_status(401)
                    self.write({"error": "Invalid username or password."})
            else:
                self.set_status(401)
                self.write({"error": "Invalid username or password."})

        except Exception as e:
            app_log.error(f"Error in UPLoginHandler: {e}")
            self.set_status(500)
            self.write({"error": "Internal server error."})
        finally:
            if conn:  # Close the database connection if it was opened
                conn.close()