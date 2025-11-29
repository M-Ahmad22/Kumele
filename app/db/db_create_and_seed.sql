-- run in your PostgreSQL target DB (kumele_synthetic or whichever you use)
-- Creates events, user_activities tables if not created by SQLAlchemy (SQLAlchemy will create too)

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    organizer_id INT NOT NULL,
    title TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_activities (
    activity_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type TEXT NOT NULL,
    event_id INT,
    activity_date TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reward_coupons (
    coupon_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    status_level TEXT NOT NULL,
    discount_value NUMERIC(5,2) NOT NULL,
    stackable BOOLEAN DEFAULT FALSE,
    is_redeemed BOOLEAN DEFAULT FALSE,
    issued_at TIMESTAMP DEFAULT now(),
    redeemed_at TIMESTAMP NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS reward_status_history (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    status_level TEXT NOT NULL,
    awarded_count INT DEFAULT 1,
    issued_at TIMESTAMP DEFAULT now(),
    notes TEXT
);


-- seed sample activities for user_id 12345
INSERT INTO user_activities (user_id, activity_type, event_id, activity_date)
VALUES
(12345, 'event_created', 1, now()- interval '10 days'),
(12345, 'event_attended', 2, now()- interval '15 days'),
(12345, 'event_attended', 3, now()- interval '20 days'),
(12345, 'event_created', 4, now()- interval '3 days'),
(12345, 'event_attended', 5, now()- interval '5 days');
