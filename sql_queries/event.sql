CREATE EVENT IF NOT EXISTS delete_old_accounts
ON SCHEDULE EVERY 1 DAY
DO
    CALL permanently_delete_user();

SHOW EVENTS LIKE 'delete_old_accounts';