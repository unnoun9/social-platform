DELIMITER $$
CREATE PROCEDURE permanently_delete_user()
BEGIN
    DECLARE user_id INT;
    DECLARE done INT DEFAULT 0;
    DECLARE cur CURSOR FOR SELECT id FROM user_accounts WHERE deleted_date < NOW() - INTERVAL 7 DAY;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO user_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        DELETE FROM followers WHERE follower_id = user_id OR followed_id = user_id;
        DELETE FROM blocked_users WHERE blocker_id = user_id OR blocked_id = user_id;
        DELETE FROM messages WHERE sender_id = user_id OR receiver_id = user_id;
        DELETE FROM share_posts WHERE sender_id = user_id OR receiver_id = user_id;
        DELETE FROM notifications WHERE sender_id = user_id OR receiver_id = user_id;
        DELETE FROM community_members WHERE member_id = user_id;
        DELETE FROM posts WHERE user_id = user_id;
        DELETE FROM user_accounts WHERE id = user_id;
    END LOOP;
    CLOSE cur;
END $$
DELIMITER ;

SHOW PROCEDURE STATUS LIKE 'permanently_delete_user';