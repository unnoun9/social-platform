CREATE DATABASE social;

CREATE TABLE user_accounts (
	id INT NOT NULL AUTO_INCREMENT,
    display_name VARCHAR(50) NOT NULL,
	email_address VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    signup_date DATE NOT NULL,
    pfp_url VARCHAR(255),
    about VARCHAR(500),
    location VARCHAR(50),
    date_of_birth DATE,
    
    PRIMARY KEY(id)
);

CREATE TABLE posts (
	id INT NOT NULL AUTO_INCREMENT,
	user_id INT NOT NULL,
    parent_id INT DEFAULT NULL,
    title VARCHAR(100) NOT NULL,
    details TEXT,
    date_created DATE NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES user_accounts(id),
    FOREIGN KEY(parent_id) REFERENCES posts(id)
);

CREATE TABLE post_media (
	id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES posts(id)
);

CREATE TABLE endorsements (
	id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    post_id INT NOT NULL,
    endorsement_type INT NOT NULL,
	date_endorsed DATE NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES user_accounts(id),
    FOREIGN KEY(post_id) REFERENCES posts(id),
    CHECK (endorsement_type IN (-1, 1)),
    UNIQUE KEY user_post_unique (user_id, post_id)
);

CREATE TABLE tags (
	id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(30) NOT NULL,
    description VARCHAR(100) NOT NULL,
    
    PRIMARY KEY(id)
);

CREATE TABLE post_tags (
	post_id INT NOT NULL,
    tag_id INT NOT NULL,
    
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(tag_id) REFERENCES tags(id)
);

CREATE TABLE followers (
	follower_user_id INT NOT NULL,
    followed_user_id INT NOT NULL,
    
    FOREIGN KEY (follower_user_id) REFERENCES user_accounts(id),
    FOREIGN KEY (followed_user_id) REFERENCES user_accounts(id)
);

INSERT INTO user_accounts (display_name, email_address, hashed_password, signup_date)
VALUES
('Abdul Hadi', 'Abdul@Hadi', 'lazyman123', CURDATE()),
('Syed Abdullah', 'Syed@Abdullah', 'bruhman123', CURDATE());
