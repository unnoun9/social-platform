CREATE DATABASE connect_hub;

-- Stores all information for users
CREATE TABLE user_profiles (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    date_registered DATE NOT NULL,
    account_status VARCHAR(20) NOT NULL,
    profile_pic_url VARCHAR(255),
    age INT,
    gender VARCHAR(6),
    location VARCHAR(50),
    bio VARCHAR(500),
    contact_number VARCHAR(15),
    privacy BOOLEAN,

    PRIMARY KEY(id),
    UNIQUE KEY(username),
    CHECK (gender IN ('male', 'female', 'other')),
    CHECK (account_status IN ('active', 'inactive', 'deleted'))
);

-- Stores all information for posts
-- Has a reference to the creator of the post
-- Also deals with 'comments' and thier relationship with 'parent' posts by referencing another post id
CREATE TABLE posts (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    parent_post_id INT DEFAULT NULL,
    date_created DATE NOT NULL,
    title VARCHAR(100) NOT NULL,
    contents TEXT,

    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES user_profiles(id),
    FOREIGN KEY(parent_post_id) REFERENCES posts(id)
);

-- Contains urls for media files associated with posts, if any
CREATE TABLE post_media (
    id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES posts(id)
);

-- Contains information about any sharing of any posts
CREATE TABLE share_posts (
    id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    sharer_id INT NOT NULL,
    sharee_id INT NOT NULL,
    share_time DATETIME NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(sharer_id) REFERENCES user_profiles(id),
    FOREIGN KEY(sharee_id) REFERENCES user_profiles(id)
);

-- Models friend requests with a sender and receiver
CREATE TABLE friend_requests (
    id INT NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    date_sent DATE NOT NULL,
    accepted BOOLEAN DEFAULT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(sender_id) REFERENCES user_profiles(id),
    FOREIGN KEY(receiver_id) REFERENCES user_profiles(id)
);

-- Contains those users that have been accepted as friends by receiver of the request
CREATE TABLE friends (
    id INT NOT NULL AUTO_INCREMENT,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    date_became_friends DATE NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(user1_id) REFERENCES user_profiles(id),
    FOREIGN KEY(user2_id) REFERENCES user_profiles(id)
);

-- Contains those users that may never interact with each other
CREATE TABLE blocked_users (
    id INT NOT NULL AUTO_INCREMENT,
    blocker_id INT NOT NULL,
    blocked_id INT NOT NULL,
    date_blocked DATE NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(blocker_id) REFERENCES user_profiles(id),
    FOREIGN KEY(blocked_id) REFERENCES user_profiles(id)
);

-- Models messages between users
CREATE TABLE messages (
    id INT NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    time_sent DATETIME NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(sender_id) REFERENCES user_profiles(id),
    FOREIGN KEY(receiver_id) REFERENCES user_profiles(id)
);

-- Contains urls for media files associated with messages, if any
CREATE TABLE message_media (
    id INT NOT NULL AUTO_INCREMENT,
    message_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(message_id) REFERENCES messages(id)
);

-- Contains groups, having a user as its admin and a list of members
CREATE TABLE groups_ (
    id INT NOT NULL AUTO_INCREMENT,
    group_admin_id INT NOT NULL,
    title VARCHAR(30) NOT NULL,
    description VARCHAR(100) NOT NULL,
    date_created DATE NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(group_admin_id) REFERENCES user_profiles(id)
);

-- Links a groups with its members
CREATE TABLE group_members (
    group_id INT NOT NULL,
    member_id INT NOT NULL,
    date_joined DATE NOT NULL,

    PRIMARY KEY(group_id, member_id),
    FOREIGN KEY(group_id) REFERENCES groups_(id),
    FOREIGN KEY(member_id) REFERENCES user_profiles(id)
);

-- Models a notification, having a type and senders / receiver, system for users
CREATE TABLE notifications (
	id INT NOT NULL AUTO_INCREMENT,
    sender_id INT NOT NULL,
    reciever_id INT NOT NULL,
    notification_type VARCHAR(20) NOT NULL,
    content VARCHAR(50) NOT NULL,
	
    PRIMARY KEY(id),
    FOREIGN KEY(sender_id) REFERENCES user_profiles(id),
    FOREIGN KEY(reciever_id) REFERENCES user_profiles(id),
    CHECK(notification_type IN ('message', 'share', 'request'))
);