-- usersテーブルに朝の通知設定カラムを追加
ALTER TABLE users ADD COLUMN morning_notify TINYINT(1) NOT NULL DEFAULT 0 AFTER onboarding_step;
