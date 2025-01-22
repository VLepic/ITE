import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.log
from urllib.request import urlopen
import datetime as dt
import logging
import numpy as np
import imutils
import pickle
import cv2
import json
import psycopg2
import secrets
import base64

app_log = logging.getLogger("tornado.application")

detector = cv2.dnn.readNetFromCaffe("faceid/face_detection_model/deploy.prototxt",
                                    "faceid/face_detection_model/res10_300x300_ssd_iter_140000.caffemodel")

embedder = cv2.dnn.readNetFromTorch("faceid/openface_nn4.small2.v1.t7")

recognizer = pickle.loads(open("faceid/output/recognizer.pickle", "rb").read())
le = pickle.loads(open("faceid/output/le.pickle", "rb").read())


def generate_token():
    # Generate 192 bytes of random data
    random_bytes = secrets.token_bytes(192)

    # Encode the random bytes to a base64 string
    token = base64.urlsafe_b64encode(random_bytes).decode('utf-8')

    # Trim the token to exactly 256 characters (if necessary)
    return token[:256]

class RecognizeImageHandler(tornado.web.RequestHandler):
    def post(self):
        # Convert from binary data to string
        received_data = self.request.body.decode()

        assert received_data.startswith("data:image/png"), "Only data:image/png URL supported"

        # Parse data:// URL
        with urlopen(received_data) as response:
            image_data = response.read()

        fn = f"recog_images/img-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.png" 
        with open(fn, "wb") as fw:
            fw.write(image_data)

        image = cv2.imread(fn)
        image = imutils.resize(image, width=600)
        (h, w) = image.shape[:2]

        app_log.info("Processing image")

        imageBlob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

        detector.setInput(imageBlob)
        detections = detector.forward()

        faces = []

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > 0.5:
                # compute the (x, y)-coordinates of the bounding box for the
                # face
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # extract the face ROI
                face = image[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                # ensure the face width and height are sufficiently large
                if fW < 20 or fH < 20:
                    continue

                faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96),
                    (0, 0, 0), swapRB=True, crop=False)
                embedder.setInput(faceBlob)
                vec = embedder.forward()

                # perform classification to recognize the face
                preds = recognizer.predict_proba(vec)[0]
                j = np.argmax(preds)
                proba = preds[j]
                name = le.classes_[j]
                userid = username = token_id = logintoken = created_at = expires_at = None
                TOKEN_EXPIRATION_MINUTES = os.environ.get("TOKEN_EXPIRATION", 30)
                if name != "unknown":
                    conn = psycopg2.connect(
                        dbname=os.environ.get("POSTGRES_DB"),
                        user=os.environ.get("POSTGRES_USER"),
                        password=os.environ.get("POSTGRES_PASSWORD"),
                        host=os.environ.get("POSTGRES_HOST", "postgres"),
                        port=5432
                    )
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT u.userid, username, token_id, logintoken, created_at, expires_at
                        FROM users u
                        LEFT JOIN login_tokens lt ON u.userid = lt.userid
                        WHERE u.username = %s
                        """,
                        (name,)  # Parameterized input
                    )

                    rows = cursor.fetchall()

                    if rows:
                        for row in rows:
                            userid, username, token_id, logintoken, created_at, expires_at = row
                            print(f"User ID: {userid}")
                            print(f"Username: {username}")
                            print(f"Token ID: {token_id}")
                            print(f"Login Token: {logintoken}")
                            print(f"Created At: {created_at}")
                            print(f"Expires At: {expires_at}")
                    else:
                        print("No data found.")

                    if logintoken is None:
                        logintoken = generate_token()
                        expires_at = dt.datetime.now() + dt.timedelta(minutes=int(TOKEN_EXPIRATION_MINUTES))

                        try:
                            cursor.execute(
                                """
                                INSERT INTO login_tokens (userid, logintoken, created_at, expires_at)
                                VALUES (%s, %s, NOW(), %s)
                                """,
                                (userid, logintoken, expires_at)
                            )
                            conn.commit()  # Commit the transaction
                            print(f"Token successfully saved for user ID {userid}")
                        except Exception as e:
                            print(f"Error saving token: {e}")
                            conn.rollback()  # Rollback the transaction on error

                        cursor.execute(
                            """
                            UPDATE users_info
                            SET last_logged_in_at = NOW()
                            WHERE userid = %s;
                            """,
                            (userid,)
                        )
                        conn.commit()


                    elif logintoken:
                        logintoken = generate_token()
                        expires_at = dt.datetime.now() + dt.timedelta(minutes=int(TOKEN_EXPIRATION_MINUTES))

                        try:
                            cursor.execute(
                                """
                                UPDATE login_tokens
                                SET logintoken = %s, created_at = NOW(), expires_at = %s
                                WHERE userid = %s;


                                """,
                                (logintoken, expires_at, userid)
                            )
                            conn.commit()
                            print(f"Token successfully updated for user ID {userid}")
                        except Exception as e:
                            print(f"Error saving token: {e}")
                            conn.rollback()

                        cursor.execute(
                            """
                            UPDATE users_info
                            SET last_logged_in_at = %s
                            WHERE userid = %s;
                            """,
                            (created_at, userid,)
                        )
                        conn.commit()



                faces.append({
                    "success": True,
                    "userid": userid,
                    "name": username,
                    "prob": proba,
                    "token_id": token_id,
                    "logintoken": logintoken,
                    "created_at": created_at.isoformat() if created_at else None,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "bbox": {"x1": int(startX), "x2": int(endX), "y1": int(startY), "y2": int(endY)},
                })

        js = {"faces": faces}
        self.write(js)
        print("Result JSON")
        print(json.dumps(js, indent=4, sort_keys=True))
