query = {

    # Users
    'select_all_users': """
            SELECT *
            FROM user_accounts
            ORDER BY signup_date
        """,
    
    'delete_user_by_id': """
            DELETE
            FROM user_accounts
            WHERE id = %s
        """,
        
    'select_user_by_id': """
            SELECT *
            FROM users
            WHERE id = %s
        """,
    
    'select_user_by_display_name': """
            SELECT *
            FROM user_accounts
            WHERE display_name = %s
        """,
    
    'insert_user_signup': """
            INSERT INTO user_accounts (display_name, email_address, hashed_password, signup_date)
            VALUES (%s, %s, %s, NOW())
        """,

    'select_user_age_by_id': """
            SELECT TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age
            FROM user_accounts
            WHERE id = %s
        """,

    'update_user_profile': """
            UPDATE user_accounts SET
            display_name = %s,
            email_address = %s,
            pfp_url = %s,
            about = %s,
            date_of_birth = %s,
            location = %s,
            privacy = %s
            WHERE id = %s
        """,
    
    'select_user_hashed_password_by_id': """
            SELECT hashed_password
            FROM user_accounts
            WHERE id = %s
        """,
    
    'update_user_password': """
            UPDATE user_accounts
            SET hashed_password = %s
            WHERE id = %s
        """,
    
    'soft_delete_user_by_id': """
            UPDATE user_accounts
            SET account_status = 'Deleted', deleted_date = NOW()
            WHERE id = %s
        """,

    'recover_user_by_id': """
            UPDATE user_accounts
            SET account_status = 'Active', deleted_date = NULL
            WHERE id = %s
        """,
    
    # Follows
    'select_follow_instance_by_ids': """
            SELECT * FROM followers
            WHERE follower_id = %s AND followed_id = %s
        """,

    'select_user_follow_count_by_id': """
            SELECT COUNT(*) FROM followers
            WHERE followed_id = %s
        """,
    
    'insert_follow_instance_by_ids': """
            INSERT INTO followers (follower_id, followed_id)
            VALUES (%s, %s)
        """,
    
    'delete_follow_instance_by_ids': """
            DELETE FROM followers
            WHERE follower_id = %s AND followed_id = %s
        """,

    # Blocks
    'select_blocked_instance_by_ids': """
            SELECT * FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """,

    'select_block_existence': """
            SELECT * FROM blocked_users
            WHERE (blocker_id = %s AND blocked_id = %s)
            OR (blocker_id = %s AND blocked_id = %s)
        """,

    'insert_block_instance_by_ids': """
            INSERT INTO blocked_users (blocker_id, blocked_id, date_blocked)
            VALUES (%s, %s, NOW())
        """,
    
    'delete_blocked_instance_by_ids': """
            DELETE FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """,
    
    # Posts
    'select_post_by_id': """
            SELECT *
            FROM posts
            WHERE id = %s
        """,
    
    'select_user_posts_by_id_order_date': """
            SELECT *
            FROM posts
            WHERE user_id = %s
            ORDER BY date_created DESC
        """,

    'insert_post': """
            INSERT INTO POSTS (user_id, title, content, date_created)
            VALUES (%s, %s, %s, NOW())
        """,
    
    'update_post': """
            UPDATE posts
            SET title = %s, content = %s
            WHERE id = %s
        """,
    
    'delete_post_by_id': """
            DELETE
            FROM posts
            WHERE id = %s
        """,

    # Endorsements
    'select_endorsement_count': """
            SELECT COUNT(*) FROM endorsements
            WHERE post_id = %s AND endorsement_type = 'Endorsement'
        """,
    
    'select_condemnation_count': """
            SELECT COUNT(*) FROM endorsements
            WHERE post_id = %s AND endorsement_type = 'Condemnation'
        """,

    'select_endorsement_by_post_user': """
            SELECT * FROM endorsements
            WHERE user_id = %s AND post_id = %s
        """,

    'insert_endorsement': """
            INSERT INTO endorsements (user_id, post_id, endorsement_type, date_endorsed)
            VALUES (%s, %s, %s, NOW())
        """,
    
    'update_endorsement_type': """
            UPDATE endorsements
            SET endorsement_type = %s, date_endorsed = NOW()
            WHERE id = %s
        """,
    
    'delete_endorsement_by_id': """
            DELETE FROM endorsements
            WHERE id = %s
        """,

    # Comments
    'select_comment_by_id': """
            SELECT *
            FROM comments
            WHERE id = %s
        """,

    'update_comment_content': """
            UPDATE comments
            SET content = %s
            WHERE id = %s
        """,

    'delete_comment_by_id': """
            DELETE
            FROM comments
            WHERE id = %s
        """,
    
    'select_comment_count_on_post': """
            SELECT COUNT(*) FROM comments
            WHERE post_id = %s
        """,
    
    'select_post_comments_filter_blockage_status_privacy': """
            SELECT C.id, C.content, C.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM comments C
            JOIN user_accounts U ON C.user_id = U.id
            LEFT JOIN blocked_users B1 ON (B1.blocked_id = C.user_id AND B1.blocker_id = %s)
            LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = C.user_id)
            WHERE C.post_id = %s AND U.account_status != 'Deleted' AND U.privacy = 'Public'
            AND B1.blocked_id IS NULL
            AND B2.blocked_id IS NULL
            ORDER BY C.date_created DESC
        """,
    
    'select_post_comments_filter_status_privacy': """
            SELECT C.id, C.content, C.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM comments C
            JOIN user_accounts U ON C.user_id = U.id
            WHERE C.post_id = %s AND U.account_status != 'Deleted' AND U.privacy = 'Public'
            ORDER BY C.date_created DESC
        """,

    # Messages
    'insert_message': """
            INSERT INTO messages (sender_id, receiver_id, content, date_sent)
            VALUES (%s, %s, %s, NOW())
        """,

    'select_message_conversation_filter_blockage_status_order_date': """
            SELECT U.id, U.display_name, U.pfp_url, MAX(M.date_sent) AS last_message_date
            FROM messages M
            JOIN user_accounts U ON (M.sender_id = U.id OR M.receiver_id = U.id)
            LEFT JOIN blocked_users B1 ON (M.sender_id = B1.blocker_id AND M.receiver_id = B1.blocked_id)
            LEFT JOIN blocked_users B2 ON (M.receiver_id = B2.blocker_id AND M.sender_id = B2.blocked_id)
            WHERE (M.sender_id = %s OR M.receiver_id = %s)
            AND U.id != %s AND U.account_status != 'Deleted'
            AND B1.id IS NULL
            AND B2.id IS NULL
            GROUP BY U.id
            ORDER BY last_message_date DESC
        """,

    'select_sender_receiver_status_privacy': """
            SELECT account_status, privacy
            FROM user_accounts
            WHERE id IN (%s, %s)
        """,

    'select_messages_of_users_order_date': """
            SELECT M.id, M.sender_id, M.receiver_id, M.content, M.date_sent, U.display_name, U.pfp_url
            FROM messages M
            JOIN user_accounts U ON M.sender_id = U.id
            WHERE (M.sender_id = %s AND M.receiver_id = %s)
            OR (M.sender_id = %s AND M.receiver_id = %s)
            ORDER BY M.date_sent
        """,

    # Feed
    'select_posts_join_users_filter_status_privacy': """
            SELECT P.id, P.title, P.content, P.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM posts P
            JOIN user_accounts U ON P.user_id = U.id
            WHERE U.privacy = 'Public' AND account_status != 'Deleted'
            ORDER BY P.date_created DESC
        """,

    'select_posts_join_users_filter_blockage_status_privacy': """
            SELECT P.id, P.title, P.content, P.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM posts P
            JOIN user_accounts U ON P.user_id = U.id
            LEFT JOIN blocked_users B1 ON (B1.blocked_id = P.user_id AND B1.blocker_id = %s)
            LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = P.user_id)
            WHERE U.privacy = 'Public' AND U.account_status != 'Deleted'
            AND B1.blocked_id IS NULL
            AND B2.blocked_id IS NULL
            ORDER BY P.date_created DESC
        """,

    # Searches
    'select_posts_join_users_filter_blockage_status_privacy_search': """
            SELECT P.id, P.title, P.content, P.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM posts P
            JOIN user_accounts U ON P.user_id = U.id
            LEFT JOIN blocked_users B1 ON (B1.blocked_id = P.user_id AND B1.blocker_id = %s)
            LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = P.user_id)
            WHERE U.privacy = 'Public' AND U.account_status != 'Deleted' AND (P.title LIKE %s OR P.content LIKE %s)
            AND B1.blocked_id IS NULL
            AND B2.blocked_id IS NULL
            ORDER BY P.date_created DESC
        """,

    'select_users_filter_blockage_search': """
            SELECT *
            FROM user_accounts U
            LEFT JOIN blocked_users B ON (B.blocked_id = %s AND B.blocker_id = U.id)
            WHERE display_name LIKE %s AND B.blocked_id IS NULL
            ORDER BY display_name
        """,

    'select_posts_join_users_filter_status_privacy_search': """
            SELECT P.id, P.title, P.content, P.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM posts P
            JOIN user_accounts U ON P.user_id = U.id
            WHERE U.privacy = 'Public' AND account_status != 'Deleted' AND (P.title LIKE %s OR P.content LIKE %s)
            ORDER BY P.date_created DESC
        """,

    'select_users_filter_search': """
            SELECT *
            FROM user_accounts
            WHERE display_name LIKE %s
            ORDER BY display_name
        """
    
}