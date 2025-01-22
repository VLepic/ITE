CREATE TABLE users (
  userid SERIAL PRIMARY KEY UNIQUE,
  username VARCHAR(100) NOT NULL UNIQUE ,
  password_hash VARCHAR(256)
);

CREATE TABLE users_info (
  userid INT PRIMARY KEY,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  last_logged_in_at TIMESTAMP,
  CONSTRAINT fk_users FOREIGN KEY (userid) REFERENCES users (userid)
);

CREATE TABLE login_tokens (
  token_id SERIAL PRIMARY KEY, -- Unique identifier for each token
  userid INT NOT NULL,         -- Reference to the user
  logintoken VARCHAR(256) NOT NULL, -- Token value
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Token creation time
  expires_at TIMESTAMP,        -- Optional expiration time
  CONSTRAINT fk_users FOREIGN KEY (userid) REFERENCES users (userid)
);

-- Vložení dat do tabulky `users`
INSERT INTO users (username, password_hash)
VALUES
('bulinm', '$2b$12$4Fp/Sho4UR/pji.kxSxtku/g/rOlbrb4Ep8geTUl6/8Y01v5sEoja'),
('honzas', '$2b$12$4Fp/Sho4UR/pji.kxSxtku/g/rOlbrb4Ep8geTUl6/8Y01v5sEoja'),
('radova', '$2b$12$4Fp/Sho4UR/pji.kxSxtku/g/rOlbrb4Ep8geTUl6/8Y01v5sEoja'),
('vlepic', '$2b$12$4Fp/Sho4UR/pji.kxSxtku/g/rOlbrb4Ep8geTUl6/8Y01v5sEoja');

-- Vložení dat do tabulky `users_info`
INSERT INTO users_info (userid, first_name, last_name)
VALUES
(1, 'Martin', 'Bulín'),
(2, 'Jan', 'Švec'),
(3, 'Vlasta', 'Radová'),
(4, 'Václav', 'Lepič');