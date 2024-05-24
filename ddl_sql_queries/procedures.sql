DELIMITER $$
CREATE PROCEDURE permanently_delete_user()
BEGIN
    DECLARE _user_id INT;
    DECLARE done INT DEFAULT 0;
    DECLARE cur CURSOR FOR SELECT id FROM user_accounts WHERE deleted_date < NOW() - INTERVAL 7 DAY;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO _user_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        DELETE FROM followers WHERE follower_id = _user_id OR followed_id = _user_id;
        DELETE FROM blocked_users WHERE blocker_id = _user_id OR blocked_id = _user_id;
        DELETE FROM messages WHERE sender_id = _user_id OR receiver_id = _user_id;
        DELETE FROM notifications WHERE originator_id = _user_id OR receiver_id = _user_id;
        DELETE FROM community_members WHERE member_id = _user_id;
        DELETE FROM endorsements WHERE user_id = _user_id;
        DELETE FROM posts WHERE user_id = _user_id;
        DELETE FROM user_accounts WHERE id = _user_id;
    END LOOP;
    CLOSE cur;
END $$
DELIMITER ;

SHOW PROCEDURE STATUS LIKE 'permanently_delete_user';