CREATE DATABASE social;

CREATE TABLE user_accounts (
	id INT NOT NULL AUTO_INCREMENT,
    display_name VARCHAR(50) NOT NULL,
	email_address VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    signup_date DATETIME NOT NULL,
    account_status VARCHAR(8) NOT NULL DEFAULT 'Active',
    pfp_url TEXT,
    about VARCHAR(500),
    location VARCHAR(50),
    date_of_birth DATE,
    privacy VARCHAR(8) DEFAULT 'Public',
    
    PRIMARY KEY(id),
    UNIQUE (display_name),
    CONSTRAINT chk_status CHECK (account_status IN ('Active', 'Inactive', 'Deleted')),
    CONSTRAINT chk_privacy CHECK (privacy IN ('Public', 'Private'))
);

CREATE TABLE posts (
	id INT NOT NULL AUTO_INCREMENT,
	user_id INT NOT NULL,
    parent_id INT DEFAULT NULL,
    title VARCHAR(100) NOT NULL,
    content VARCHAR(10000),
    date_created DATETIME NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(parent_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE post_media (
	id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    url TEXT NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE share_posts (
    id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    date_shared DATETIME NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(sender_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE endorsements (
	id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    post_id INT NOT NULL,
    endorsement_type INT NOT NULL,
	date_endorsed DATETIME NOT NULL,
    
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(post_id) REFERENCES posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_endorsement_type CHECK (endorsement_type IN (-1, 1)),
    UNIQUE (user_id, post_id)
);

-- CREATE TABLE tags (
-- 	id INT NOT NULL AUTO_INCREMENT,
--     title VARCHAR(30) NOT NULL,
--     description VARCHAR(100) NOT NULL,
    
--     PRIMARY KEY(id)
-- );

-- CREATE TABLE post_tags (
-- 	post_id INT NOT NULL,
--     tag_id INT NOT NULL,
    
--     FOREIGN KEY(post_id) REFERENCES posts(id)
--         ON DELETE CASCADE ON UPDATE CASCADE,
--     FOREIGN KEY(tag_id) REFERENCES tags(id)
--         ON DELETE CASCADE ON UPDATE CASCADE
-- );

CREATE TABLE followers (
	follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    
    FOREIGN KEY (follower_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE messages (
    id INT NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content VARCHAR(5000) NOT NULL,
    date_sent DATETIME NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(sender_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE message_media (
    id INT NOT NULL AUTO_INCREMENT,
    message_id INT NOT NULL,
    url TEXT NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(message_id) REFERENCES messages(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE blocked_users (
    id INT NOT NULL AUTO_INCREMENT,
    blocker_id INT NOT NULL,
    blocked_id INT NOT NULL,
    date_blocked DATETIME NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(blocker_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(blocked_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE notifications (
	id INT NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    notification_type VARCHAR(20) NOT NULL,
    content VARCHAR(100) NOT NULL,
    date_notified DATETIME NOT NULL,
	
    PRIMARY KEY(id),
    FOREIGN KEY(sender_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_notification_type CHECK(notification_type IN ('Message', 'Share', 'Request'))
);

CREATE TABLE communities (
    id INT NOT NULL AUTO_INCREMENT,
    admin_id INT NOT NULL,
    title VARCHAR(30) NOT NULL,
    description VARCHAR(500) NOT NULL,
    date_created DATETIME NOT NULL,
    pfp_url TEXT,

    PRIMARY KEY(id),
    FOREIGN KEY(admin_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE community_members (
    community_id INT NOT NULL,
    member_id INT NOT NULL,
    date_joined DATETIME NOT NULL,

    PRIMARY KEY(community_id, member_id),
    FOREIGN KEY(community_id) REFERENCES communities(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(member_id) REFERENCES user_accounts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);