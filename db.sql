-- Создание таблицы users
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы main_goals (основные цели)
CREATE TABLE IF NOT EXISTS main_goals (
    goal_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    goal_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Создание таблицы training_goals (цели обучения)
CREATE TABLE IF NOT EXISTS training_goals (
    training_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    goal_id INT,
    goal_name VARCHAR(255),
    study_time VARCHAR(255),       -- время занятия
    daily_steps INT,               -- шаги обучения за день
    test VARCHAR(255),             -- название теста
    test_result VARCHAR(255),      -- результат теста
    daily_completed BOOLEAN,       -- выполнено обучение за день
    test_passed BOOLEAN,           -- сдан ли тест
    streak_count INT,              -- счётчик без пропущенных дней
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES main_goals(goal_id) ON DELETE CASCADE
);