CREATE DATABASE IF NOT EXISTS watchlist_db;
USE watchlist_db;

CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    join_date DATE DEFAULT (CURRENT_DATE)
);

CREATE TABLE Movie (
    movie_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    release_year INT,
    genre VARCHAR(50),
    director VARCHAR(100),
    description TEXT
);

CREATE TABLE Review (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 10),
    review_text TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id) ON DELETE CASCADE
);

CREATE TABLE Watchlist (
    watchlist_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    status ENUM('Watched', 'Want to Watch', 'Favorite') DEFAULT 'Want to Watch',
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id) ON DELETE CASCADE,
    UNIQUE KEY unique_watchlist (user_id, movie_id)
);

INSERT INTO Movie (title, release_year, genre, director, description) VALUES
('Inception', 2010, 'Sci-Fi', 'Christopher Nolan', 'A thief who steals corporate secrets through dream-sharing technology.'),
('The Dark Knight', 2008, 'Action', 'Christopher Nolan', 'Batman faces the Joker, a criminal mastermind.'),
('Interstellar', 2014, 'Sci-Fi', 'Christopher Nolan', 'A team of explorers travel through a wormhole in space.');